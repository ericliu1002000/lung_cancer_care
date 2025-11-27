"""Doctor domain services."""

from django.core.exceptions import ValidationError

from users.models import DoctorProfile


class DoctorService:
    """封装医生相关的查询逻辑。"""

    def get_doctor_for_sales(self, doctor_id: int, sales_profile) -> DoctorProfile:
        """返回属于当前销售的医生档案。"""

        if not sales_profile:
            raise ValidationError("当前账号无销售档案")

        doctor = (
            DoctorProfile.objects.select_related("studio")
            .filter(pk=doctor_id, sales=sales_profile)
            .first()
        )
        if doctor is None:
            raise ValidationError("未找到医生或无权访问")
        return doctor
