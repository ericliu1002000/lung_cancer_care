from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from patient_alerts.models import AlertEventType, AlertLevel, AlertStatus, PatientAlert
from patient_alerts.services.patient_alert import PatientAlertService
from users import choices
from users.models import CustomUser, DoctorProfile, PatientProfile


class PatientAlertServiceTests(TestCase):
    def setUp(self):
        self.doctor_user = CustomUser.objects.create_user(
            user_type=choices.UserType.DOCTOR,
            phone="13800138111",
            wx_nickname="Dr. Handler",
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            name="处理医生",
            hospital="测试医院",
        )
        self.patient = PatientProfile.objects.create(
            phone="18600000222",
            doctor=self.doctor_profile,
        )
        self.alert = PatientAlert.objects.create(
            patient=self.patient,
            doctor=self.doctor_profile,
            event_type=AlertEventType.DATA,
            event_level=AlertLevel.MILD,
            event_title="血氧异常",
            event_content="血氧 94%",
            event_time=timezone.now(),
            status=AlertStatus.PENDING,
        )

    def test_update_status_sets_handler_and_content(self):
        handler = CustomUser.objects.create_user(
            user_type=choices.UserType.ASSISTANT,
            phone="13800138112",
            wx_nickname="助手",
        )
        handled_at = timezone.now()

        updated = PatientAlertService.update_status(
            alert_id=self.alert.id,
            status=AlertStatus.COMPLETED,
            handler_id=handler.id,
            handle_content="已联系患者，情况稳定。",
            handled_at=handled_at,
        )

        self.assertEqual(updated.status, AlertStatus.COMPLETED)
        self.assertEqual(updated.handler_id, handler.id)
        self.assertEqual(updated.handle_content, "已联系患者，情况稳定。")
        self.assertEqual(updated.handle_time, handled_at)

    def test_get_detail_returns_alert(self):
        detail = PatientAlertService.get_detail(self.alert.id)
        self.assertEqual(detail.id, self.alert.id)
        self.assertEqual(detail.patient_id, self.patient.id)

    def test_get_detail_invalid_id_raises(self):
        with self.assertRaises(ValidationError):
            PatientAlertService.get_detail(999999)
