import json
from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from core.models import CheckupLibrary
from health_data.models import ClinicalEvent, ReportImage, ReportUpload, UploadSource
from users import choices
from users.models import DoctorProfile, PatientProfile
from web_doctor.views.reports_history_data import handle_reports_history_section


User = get_user_model()


class ConsultationRecordDeleteTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.doctor_user = User.objects.create_user(
            username="doctor_delete",
            password="password",
            user_type=choices.UserType.DOCTOR,
            phone="13800000001",
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, name="Test Doctor")

        self.patient_user = User.objects.create_user(
            username="patient_delete",
            user_type=choices.UserType.PATIENT,
            wx_openid="test_openid_delete",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, name="Test Patient")

        CheckupLibrary.objects.create(name="血常规")

    def test_delete_consultation_record_success(self):
        event = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 1, 10),
            created_by_doctor=self.doctor,
            interpretation="To be deleted",
        )
        upload = ReportUpload.objects.create(patient=self.patient, upload_source=UploadSource.DOCTOR_BACKEND)
        img1 = ReportImage.objects.create(
            upload=upload,
            image_url="http://test.com/delete_1.jpg",
            record_type=1,
            clinical_event=event,
            report_date=date(2025, 1, 10),
            archived_by=self.doctor,
            archived_at=timezone.now(),
        )
        img2 = ReportImage.objects.create(
            upload=upload,
            image_url="http://test.com/delete_2.jpg",
            record_type=1,
            clinical_event=event,
            report_date=date(2025, 1, 10),
            archived_by=self.doctor,
            archived_at=timezone.now(),
        )

        self.client.force_login(self.doctor_user)
        url = reverse("web_doctor:delete_consultation_record", args=[self.patient.id, event.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        data = json.loads(resp.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["event_id"], event.id)
        self.assertEqual(data["updated_images"], 2)

        self.assertFalse(ClinicalEvent.objects.filter(id=event.id).exists())

        img1.refresh_from_db()
        img2.refresh_from_db()
        for img in (img1, img2):
            self.assertIsNone(img.clinical_event)
            self.assertIsNone(img.record_type)
            self.assertIsNone(img.checkup_item)
            self.assertIsNone(img.report_date)
            self.assertIsNone(img.archived_by)
            self.assertIsNone(img.archived_at)

    def test_delete_cancel_semantic(self):
        event = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 1, 11),
            created_by_doctor=self.doctor,
        )
        self.assertTrue(ClinicalEvent.objects.filter(id=event.id).exists())

    def test_delete_consultation_record_service_exception(self):
        event = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 1, 12),
            created_by_doctor=self.doctor,
        )

        self.client.force_login(self.doctor_user)
        url = reverse("web_doctor:delete_consultation_record", args=[self.patient.id, event.id])

        with patch("web_doctor.views.reports_history_data.ReportArchiveService.delete_clinical_event") as mocked:
            mocked.side_effect = Exception("boom")
            resp = self.client.post(url)

        self.assertEqual(resp.status_code, 500)
        data = json.loads(resp.content)
        self.assertEqual(data["status"], "error")
        self.assertTrue(ClinicalEvent.objects.filter(id=event.id).exists())

    def test_list_sync_after_delete(self):
        event_to_delete = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 1, 13),
            created_by_doctor=self.doctor,
        )
        event_keep = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=2,
            event_date=date(2025, 1, 14),
            created_by_doctor=self.doctor,
        )

        self.client.force_login(self.doctor_user)
        url = reverse("web_doctor:delete_consultation_record", args=[self.patient.id, event_to_delete.id])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)

        request = self.factory.get("/doctor/workspace/reports?tab=records")
        request.user = self.doctor_user
        context = {"patient": self.patient}
        handle_reports_history_section(request, context)
        reports = context.get("reports_page").object_list
        ids = [r["id"] for r in reports]
        self.assertNotIn(event_to_delete.id, ids)
        self.assertIn(event_keep.id, ids)

