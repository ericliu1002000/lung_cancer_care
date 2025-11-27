import time
import uuid
import hashlib
import requests
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SmartWatchService:
    
    @staticmethod
    def _get_sha1(text):
        """辅助方法：计算 SHA1"""
        return hashlib.sha1(text.encode('utf-8')).hexdigest()

    @staticmethod
    def _get_md5(text_or_bytes):
        """辅助方法：计算 MD5"""
        if isinstance(text_or_bytes, str):
            text_or_bytes = text_or_bytes.encode('utf-8')
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
        app_key = config['APP_KEY']
        app_secret = config['APP_SECRET']
        
        # 1. 校验长度限制 [cite: 543]
        if len(title) > 8:
            return False, "标题不能超过8个字符"
        if len(content) > 80:
            return False, "内容不能超过80个字符"

        # 2. 准备公共参数
        nonce = str(uuid.uuid4()).replace('-', '') # 随机数 
        cur_time = str(int(time.time()))           # 当前时间戳(秒) 
        
        # 3. 计算 CheckSum (API调用模式)
        # 算法: SHA1(AppSecret + Nonce + CurTime) 
        raw_str = app_secret + nonce + cur_time
        check_sum = cls._get_sha1(raw_str)

        # 4. 构造 Header [cite: 430]
        headers = {
            'AppKey': app_key,
            'Nonce': nonce,
            'CurTime': cur_time,
            'CheckSum': check_sum,
            'Content-Type': 'application/json; charset=utf-8'
        }

        # 5. 构造 Body [cite: 543]
        payload = {
            "appKey": app_key,
            "deviceNo": device_no,
            "messageTitle": title,
            "messageContent": content
        }

        # 6. 发送请求
        url = f"{config['API_BASE_URL']}/api/hrt/app/device/watch/message" # [cite: 536]
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            res_json = response.json()
            
            # 判断业务成功码 E000000 [cite: 496]
            if res_json.get('code') == 'E000000':
                return True, res_json.get('data', {}).get('msgId')
            else:
                logger.error(f"手表消息发送失败: {res_json}")
                return False, res_json.get('message')
                
        except Exception as e:
            logger.error(f"手表接口网络异常: {e}")
            return False, str(e)

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
        app_secret = config['APP_SECRET']
        
        # 1. 从 Header 获取参数 [cite: 12, 14]
        # 注意：Django header key 会被转为 HTTP_大写 格式
        req_md5 = request.META.get('HTTP_MD5')
        req_checksum = request.META.get('HTTP_CHECKSUM')
        req_curtime = request.META.get('HTTP_CURTIME')
        
        if not (req_md5 and req_checksum and req_curtime):
            logger.warning("回调请求缺少必要Header")
            return False

        # 2. 验证 Request Body 的 MD5 [cite: 28]
        # 必须使用原始 bytes body 计算
        body_bytes = request.body
        my_md5 = cls._get_md5(body_bytes)
        
        # 这一步文档没明确说要对比 md5，但通常为了安全应该对比
        if my_md5.lower() != req_md5.lower():
            logger.warning(f"Body MD5不匹配: 接收={req_md5}, 计算={my_md5}")
            return False

        # 3. 验证最终 CheckSum
        # 算法: SHA1(AppSecret + MD5 + CurTime) [cite: 23]
        # 注意：这里的 MD5 使用的是 Header 传入的 md5 还是 body 计算的 md5？
        # 根据 Java 示例: encode("sha1", appSecret + md5 + curTime) [cite: 21]
        raw_str = app_secret + req_md5 + req_curtime
        my_checksum = cls._get_sha1(raw_str)
        
        if my_checksum.lower() == req_checksum.lower():
            return True
        else:
            logger.warning(f"CheckSum不匹配: 接收={req_checksum}, 计算={my_checksum}")
            return False