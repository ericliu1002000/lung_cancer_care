from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from health_data.models import ClinicalEvent
from users import choices
from users.models import AssistantProfile, DoctorProfile, PatientProfile


User = get_user_model()


class ArchiverLogicTests(TestCase):
    def setUp(self):
        self.doctor_user = User.objects.create_user(
            username="doctor_archiver",
            password="password",
            user_type=choices.UserType.DOCTOR,
            phone="13800000011",
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, name="张医生")

        self.assistant_user = User.objects.create_user(
            username="assistant_archiver",
            password="password",
            user_type=choices.UserType.ASSISTANT,
            phone="13800000012",
        )
        self.assistant = AssistantProfile.objects.create(user=self.assistant_user, name="小助理")
        self.assistant.doctors.add(self.doctor)

        self.patient_user = User.objects.create_user(
            username="patient_archiver",
            user_type=choices.UserType.PATIENT,
            wx_openid="test_openid_archiver",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, name="Test Patient")

    def test_service_sets_archiver_name_doctor_and_assistant(self):
        from health_data.services.report_service import ReportArchiveService

        event_doctor = ReportArchiveService.create_record_with_images(
            patient=self.patient,
            created_by_doctor=self.doctor,
            event_type=1,
            event_date=date(2025, 1, 2),
            images=[{"image_url": "http://test/a.png"}],
            uploader=self.doctor_user,
        )
        event_doctor.refresh_from_db()
        self.assertEqual(event_doctor.archiver_name, self.doctor.name)

        event_assistant = ReportArchiveService.create_record_with_images(
            patient=self.patient,
            created_by_doctor=self.doctor,
            event_type=1,
            event_date=date(2025, 1, 3),
            images=[{"image_url": "http://test/b.png"}],
            uploader=self.assistant_user,
        )
        event_assistant.refresh_from_db()
        self.assertEqual(event_assistant.archiver_name, self.assistant.name)

    def test_service_fallback_archiver_name_unknown(self):
        from health_data.services.report_service import ReportArchiveService

        event = ReportArchiveService.create_record_with_images(
            patient=self.patient,
            created_by_doctor=self.doctor,
            event_type=1,
            event_date=date(2025, 1, 4),
            images=[{"image_url": "http://test/c.png"}],
            uploader=None,
        )
        event.refresh_from_db()
        self.assertIn(event.archiver_name, ("未知", self.doctor.name))

    def test_list_mapping_prefers_event_archiver_name(self):
        ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 1, 5),
            created_by_doctor=self.doctor,
            archiver_name=self.assistant.name,
        )
        event = ClinicalEvent.objects.filter(patient=self.patient, event_date=date(2025, 1, 5)).first()
        self.assertIsNotNone(event)
        from web_doctor.views.reports_history_data import _map_clinical_event_to_dict

        data = _map_clinical_event_to_dict(event)
        self.assertEqual(data["archiver"], self.assistant.name)
        self.assertEqual(data["archiver_name"], self.assistant.name)
