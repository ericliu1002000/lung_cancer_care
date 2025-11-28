from datetime import timedelta
from typing import Optional

# users/services/patient.py
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from users.models import PatientProfile, CustomUser, PatientRelation
from users import choices
from health_data.models import MedicalHistory
from regions.models import Province, City
# 引用 wx 的 client 来获取二维码，注意避免循环引用，可以在方法内引用或使用 lazy import
from wechatpy import WeChatClient 

class PatientService:
    
    
    def generate_bind_qrcode(self, profile_id: int, expire_seconds: int = 604800) -> str:
        """
        【功能4】生成或复用带参二维码（临时二维码）。
        参数值示例：bind_patient_1024
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # 1. 校验档案存在
        profile = PatientProfile.objects.filter(id=profile_id).first()
        if not profile:
            raise ValidationError("患者档案不存在")

        now = timezone.now()

        # 2. 检查缓存 (如果有未过期的二维码图片链接，直接返回)
        # 预留 1 分钟缓冲期，防止临界点失效
        if (
            profile.qrcode_url
            and profile.qrcode_expire_at
            and profile.qrcode_expire_at > (now + timedelta(minutes=1))
        ):
            return profile.qrcode_url

        # 3. 调用微信接口生成
        # 避免循环引用，这里导入
        from wx.services.client import wechat_client

        scene_str = f"bind_patient_{profile_id}"
        try:
            # 创建临时二维码
            res = wechat_client.qrcode.create(
                {
                    "expire_seconds": expire_seconds,  # 7天 (微信最大值)
                    "action_name": "QR_STR_SCENE",
                    "action_info": {"scene": {"scene_str": scene_str}},
                }
            )
        except Exception as e:
            raise ValidationError(f"微信接口调用失败: {str(e)}")

        # 4. 【核心修复】使用 ticket 换取图片链接
        ticket = res.get("ticket")
        if not ticket:
            raise ValidationError("二维码生成失败(无ticket)，请稍后再试")
            
        # get_url 会返回一个 https://mp.weixin.qq.com/cgi-bin/showqrcode?ticket=... 的链接
        # 这个链接可以直接放入 <img src="..."> 中显示
        real_qrcode_img_url = wechat_client.qrcode.get_url(ticket)

        # 5. 更新数据库缓存
        profile.qrcode_url = real_qrcode_img_url
        profile.qrcode_expire_at = now + timedelta(seconds=int(expire_seconds))
        
        # 只更新这就几个字段，提高效率
        profile.save(update_fields=["qrcode_url", "qrcode_expire_at", "updated_at"])

        return real_qrcode_img_url

    

    def get_profile_for_bind(self, profile_id: int) -> PatientProfile:
        """根据 ID 获取档案，找不到抛错。"""

        profile = PatientProfile.objects.filter(pk=profile_id).first()
        if profile is None:
            raise ValidationError("患者档案不存在")
        return profile

    def process_binding(
        self,
        user: CustomUser,
        patient_id: int,
        relation_type: int,
        **kwargs,
    ) -> PatientProfile:
        """处理患者本人或家属绑定逻辑。"""

        profile = self.get_profile_for_bind(patient_id)

        if relation_type == choices.RelationType.SELF:
            if profile.user and profile.user != user:
                raise ValidationError("该档案已被其他微信账号认领")
            if hasattr(user, "patient_profile") and user.patient_profile != profile:
                raise ValidationError("您已绑定过其他患者档案")
            profile.user = user
            profile.claim_status = choices.ClaimStatus.CLAIMED
            profile.save(update_fields=["user", "claim_status", "updated_at"])
            return profile

        relation_name = kwargs.get("relation_name", "")
        receive_alert_msg = kwargs.get("receive_alert_msg", False)

        PatientRelation.objects.update_or_create(
            patient=profile,
            user=user,
            defaults={
                "relation_type": relation_type,
                "relation_name": relation_name,
                "receive_alert_msg": receive_alert_msg,
            },
        )

        return profile

    def create_profile_by_self(self, user: CustomUser, data: dict) -> PatientProfile:
        """
        H5 自注册创建患者档案。
        自动继承 bound_sales 作为新档案归属，并清空线索。
        """

        name = (data.get("name") or "").strip()
        phone = (data.get("phone") or "").strip()
        if not name or not phone:
            raise ValidationError("姓名与电话为必填项")

        with transaction.atomic():
            profile = PatientProfile.objects.create(
                user=user,
                name=name,
                phone=phone,
                source=choices.PatientSource.SELF,
                sales=user.bound_sales,
                claim_status=choices.ClaimStatus.CLAIMED,
            )
            if user.bound_sales_id:
                user.bound_sales = None
                user.save(update_fields=["bound_sales", "updated_at"])
        return profile

    
    def assign_doctor(
        self,
        patient: PatientProfile,
        doctor_id: Optional[int],
        sales_user: CustomUser,
    ) -> PatientProfile:
        """为患者设置主治医生。"""

        if not hasattr(sales_user, "sales_profile"):
            raise ValidationError("当前账号无销售档案")

        doctor = None
        if doctor_id:
            doctor = (
                sales_user.sales_profile.doctors.filter(pk=doctor_id).first()
            )
            if doctor is None:
                raise ValidationError("医生不存在或无权绑定")

        patient.doctor = doctor
        patient.save(update_fields=["doctor", "updated_at"])
        return patient
