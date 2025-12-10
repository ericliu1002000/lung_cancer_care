"""
Device service layer: binding/unbinding and smartwatch integration.
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from dataclasses import dataclass
from enum import Enum

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from business_support.models import Device
from users.models import PatientProfile


logger = logging.getLogger(__name__)


class DeviceServiceError(Exception):
    """Base class for device service errors."""


class DeviceNotFoundError(DeviceServiceError):
    pass


class PatientNotFoundError(DeviceServiceError):
    pass


class DeviceInactiveError(DeviceServiceError):
    pass


class DeviceOccupiedError(DeviceServiceError):
    pass


class DeviceTypeConflictError(DeviceServiceError):
    pass


class DeviceNotBoundError(DeviceServiceError):
    pass


class DeviceActionStatus(str, Enum):
    BOUND = "bound"
    ALREADY_BOUND = "already_bound"
    UNBOUND = "unbound"


@dataclass(frozen=True)
class DeviceActionResult:
    device: Device
    status: DeviceActionStatus


def bind_device(imei: str, patient_id: int) -> DeviceActionResult:
    """
    Bind the device identified by IMEI to the patient.

    Rules:
    - Device must exist and be active.
    - Device cannot already belong to another patient.
    - The patient cannot have another device of the same type.
    - If the device is already bound to the same patient, it is treated as a no-op,
      but last_active_at is still updated and status is `ALREADY_BOUND`.
    """

    normalized_imei = _normalize_imei(imei)
    now = timezone.now()
    device_id = None

    try:
        with transaction.atomic():
            device = _lock_device_by_imei(normalized_imei)
            device_id = device.pk

            if not device.is_active:
                raise DeviceInactiveError("设备已停用，无法绑定。")

            patient = _lock_patient(patient_id)
            if not patient:
                raise PatientNotFoundError("患者不存在或已被删除。")

            if device.current_patient_id and device.current_patient_id != patient_id:
                raise DeviceOccupiedError("该设备已绑定其他患者，请先解绑。")

            conflict_exists = (
                Device.objects.select_for_update()
                .filter(current_patient_id=patient_id, device_type=device.device_type)
                .exclude(pk=device.pk)
                .exists()
            )
            if conflict_exists:
                raise DeviceTypeConflictError("该患者已绑定同类型设备，请先解绑。")

            if device.current_patient_id == patient_id:
                device.last_active_at = now
                device.save(update_fields=["last_active_at"])
                return DeviceActionResult(device=device, status=DeviceActionStatus.ALREADY_BOUND)

            device.current_patient = patient
            device.bind_at = now
            device.last_active_at = now
            device.save(update_fields=["current_patient", "bind_at", "last_active_at"])
            return DeviceActionResult(device=device, status=DeviceActionStatus.BOUND)
    except DeviceServiceError:
        if device_id:
            _touch_last_active(device_id, now)
        raise


def unbind_device(imei: str, patient_id: int) -> DeviceActionResult:
    """
    Unbind the device identified by IMEI from the patient.
    """

    normalized_imei = _normalize_imei(imei)
    now = timezone.now()
    device_id = None

    try:
        with transaction.atomic():
            device = _lock_device_by_imei(normalized_imei)
            device_id = device.pk

            patient = _lock_patient(patient_id)
            if not patient:
                raise PatientNotFoundError("患者不存在或已被删除。")

            if device.current_patient_id != patient_id:
                raise DeviceNotBoundError("该设备未绑定指定患者，无需解绑。")

            device.current_patient = None
            device.bind_at = None
            device.last_active_at = now
            device.save(update_fields=["current_patient", "bind_at", "last_active_at"])
            return DeviceActionResult(device=device, status=DeviceActionStatus.UNBOUND)
    except DeviceServiceError:
        if device_id:
            _touch_last_active(device_id, now)
        raise


def _normalize_imei(imei: str) -> str:
    if not imei:
        raise DeviceServiceError("IMEI 不能为空。")
    value = imei.strip()
    if not value:
        raise DeviceServiceError("IMEI 不能为空。")
    return value


def _lock_device_by_imei(imei: str) -> Device:
    try:
        return Device.objects.select_for_update().get(imei=imei)
    except Device.DoesNotExist as exc:
        raise DeviceNotFoundError("设备不存在，请确认 IMEI 是否正确。") from exc


def _lock_patient(patient_id: int) -> PatientProfile | None:
    if not patient_id:
        return None
    return PatientProfile.objects.select_for_update().filter(pk=patient_id).first()


def _touch_last_active(device_id: int, when):
    Device.objects.filter(pk=device_id).update(last_active_at=when)


class SmartWatchService:
    @staticmethod
    def _get_sha1(text):
        """辅助方法：计算 SHA1"""
        return hashlib.sha1(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _get_md5(text_or_bytes):
        """辅助方法：计算 MD5"""
        if isinstance(text_or_bytes, str):
            text_or_bytes = text_or_bytes.encode("utf-8")
        return hashlib.md5(text_or_bytes).hexdigest()

    # ============================
    # 功能 1: 给患者发消息 (API调用)
    # ============================
    @classmethod
    def send_message(cls, device_no, title, content):
        """
        发送消息到手表
        文档参考: API接口文档 - 消息下发
        """
        config = settings.SMARTWATCH_CONFIG
        app_key = config["APP_KEY"]
        app_secret = config["APP_SECRET"]

        # 1. 校验长度限制
        if len(title) > 8:
            return False, "标题不能超过8个字符"
        if len(content) > 80:
            return False, "内容不能超过80个字符"

        # 2. 准备公共参数
        nonce = str(uuid.uuid4()).replace("-", "")  # 随机数
        cur_time = str(int(time.time()))  # 当前时间戳(秒)

        # 3. 计算 CheckSum (API调用模式)
        # 算法: SHA1(AppSecret + Nonce + CurTime)
        raw_str = app_secret + nonce + cur_time
        check_sum = cls._get_sha1(raw_str)

        # 4. 构造 Header
        headers = {
            "AppKey": app_key,
            "Nonce": nonce,
            "CurTime": cur_time,
            "CheckSum": check_sum,
            "Content-Type": "application/json; charset=utf-8",
        }

        # 5. 构造 Body
        payload = {
            "appKey": app_key,
            "deviceNo": device_no,
            "messageTitle": title,
            "messageContent": content,
        }

        # 6. 发送请求
        url = f"{config['API_BASE_URL']}/api/hrt/app/device/watch/message"

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            res_json = response.json()

            # 判断业务成功码 E000000
            if res_json.get("code") == "E000000":
                return True, res_json.get("data", {}).get("msgId")
            logger.error("手表消息发送失败: %s", res_json)
            return False, res_json.get("message")
        except Exception as exc:  # noqa: BLE001
            logger.error("手表接口网络异常: %s", exc)
            return False, str(exc)

    # ============================
    # 功能 2: 验证回调签名 (接收数据辅助)
    # ============================
    @classmethod
    def verify_callback_signature(cls, request):
        """
        验证第三方回调的签名合法性
        文档参考: 回调说明文档 - CheckSum计算
        """
        config = settings.SMARTWATCH_CONFIG
        app_secret = config["APP_SECRET"]

        # 1. 从 Header 获取参数
        # 注意：Django header key 会被转为 HTTP_大写 格式
        req_md5 = request.META.get("HTTP_MD5")
        req_checksum = request.META.get("HTTP_CHECKSUM")
        req_curtime = request.META.get("HTTP_CURTIME")

        if not (req_md5 and req_checksum and req_curtime):
            logger.warning("回调请求缺少必要Header")
            return False

        # 2. 验证 Request Body 的 MD5
        # 必须使用原始 bytes body 计算
        body_bytes = request.body
        my_md5 = cls._get_md5(body_bytes)

        # 为安全起见，对比 MD5
        if my_md5.lower() != req_md5.lower():
            logger.warning("Body MD5不匹配: 接收=%s, 计算=%s", req_md5, my_md5)
            return False

        # 3. 验证最终 CheckSum
        # 算法: SHA1(AppSecret + MD5 + CurTime)
        raw_str = app_secret + req_md5 + req_curtime
        my_checksum = cls._get_sha1(raw_str)

        if my_checksum.lower() == req_checksum.lower():
            return True

        logger.warning("CheckSum不匹配: 接收=%s, 计算=%s", req_checksum, my_checksum)
        return False
