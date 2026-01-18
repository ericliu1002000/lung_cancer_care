from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils import timezone

from health_data.models import ReportUpload, ReportImage
from health_data.models.report_upload import UploadSource
from users import choices
from users.models import DoctorProfile, PatientProfile
from web_doctor.views.reports_history_data import _get_archives_data
from web_doctor.views.workspace import patient_workspace_section


User = get_user_model()


class ImageArchivesDateFilterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="doctor_image_archives_date_filter",
            password="password",
            user_type=choices.UserType.DOCTOR,
            phone="13800000111",
        )
        self.doctor_profile = DoctorProfile.objects.create(user=self.user, name="Test Doctor")

        self.patient_user = User.objects.create_user(
            username="patient_image_archives_date_filter",
            user_type=choices.UserType.PATIENT,
            wx_openid="openid_image_archives_date_filter",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, name="Test Patient", doctor=self.doctor_profile)

    def _create_upload_with_image(self, source: int, created_at: datetime):
        upload = ReportUpload.objects.create(patient=self.patient, upload_source=source)
        ReportUpload.objects.filter(id=upload.id).update(created_at=timezone.make_aware(created_at))
        upload.refresh_from_db()
        ReportImage.objects.create(upload=upload, image_url=f"http://test/{upload.id}.png")
        return upload

    def test_date_filter_applied_to_list_uploads(self):
        self._create_upload_with_image(UploadSource.PERSONAL_CENTER, datetime(2025, 1, 1, 12, 0, 0))
        self._create_upload_with_image(UploadSource.CHECKUP_PLAN, datetime(2025, 1, 5, 12, 0, 0))
        self._create_upload_with_image(UploadSource.PERSONAL_CENTER, datetime(2025, 1, 10, 12, 0, 0))

        archives_list, page_obj = _get_archives_data(self.patient, page=1, page_size=10, start_date="2025-01-02", end_date="2025-01-09")
        self.assertEqual(page_obj.paginator.count, 1)
        self.assertEqual(len(archives_list), 1)

    def test_date_values_persist_and_pagination_keeps_params(self):
        base = datetime(2025, 1, 1, 12, 0, 0)
        for i in range(11):
            src = UploadSource.PERSONAL_CENTER if i % 2 == 0 else UploadSource.CHECKUP_PLAN
            self._create_upload_with_image(src, base + timedelta(days=i))

        url = reverse("web_doctor:patient_workspace_section", args=[self.patient.id, "reports"])
        request = self.factory.get(
            url,
            {
                "tab": "images",
                "startDate": "2025-01-01",
                "endDate": "2025-01-31",
                "images_page": "1",
                "records_page": "1",
            },
        )
        request.user = self.user
        response = patient_workspace_section(request, self.patient.id, "reports")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf-8", errors="ignore")

        self.assertIn("dateStart: '2025-01-01'", html)
        self.assertIn("dateEnd: '2025-01-31'", html)
        self.assertNotIn('name=\"category\"', html)
        self.assertNotIn("category=", html)
        self.assertIn("startDate=2025-01-01", html)
        self.assertIn("endDate=2025-01-31", html)
