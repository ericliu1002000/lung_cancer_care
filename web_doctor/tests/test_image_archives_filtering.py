from datetime import datetime, date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from health_data.models import ReportUpload, ReportImage
from health_data.models.report_upload import UploadSource
from users import choices
from users.models import PatientProfile
from web_doctor.views.reports_history_data import _get_archives_data


User = get_user_model()


class ImageArchivesFilteringTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username="patient_archives_filter",
            user_type=choices.UserType.PATIENT,
            wx_openid="openid_archives_filter",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, name="Test Patient")

    def _create_upload_with_image(self, source: int, created_at: datetime, report_date: date | None = None):
        upload = ReportUpload.objects.create(patient=self.patient, upload_source=source)
        ReportUpload.objects.filter(id=upload.id).update(created_at=timezone.make_aware(created_at))
        upload.refresh_from_db()
        ReportImage.objects.create(
            upload=upload,
            image_url=f"http://test/{upload.id}.png",
            report_date=report_date,
        )
        return upload

    def test_filters_only_patient_sources(self):
        self._create_upload_with_image(UploadSource.DOCTOR_BACKEND, datetime(2025, 1, 3, 10, 0, 0))
        self._create_upload_with_image(UploadSource.PERSONAL_CENTER, datetime(2025, 1, 2, 10, 0, 0))
        self._create_upload_with_image(UploadSource.CHECKUP_PLAN, datetime(2025, 1, 1, 10, 0, 0))

        result = _get_archives_data(self.patient, page=1, page_size=10)
        sources = {group["upload_source"] for group in result["archives_list"]}
        self.assertEqual(sources, {UploadSource.PERSONAL_CENTER.label, UploadSource.CHECKUP_PLAN.label})

    def test_doctor_backend_uploads_are_excluded(self):
        self._create_upload_with_image(UploadSource.DOCTOR_BACKEND, datetime(2025, 1, 10, 10, 0, 0))

        result = _get_archives_data(self.patient, page=1, page_size=10)
        sources = [group["upload_source"] for group in result["archives_list"]]
        self.assertNotIn(UploadSource.DOCTOR_BACKEND.label, sources)

    def test_pagination_count_and_order_unchanged(self):
        for i in range(12):
            source = UploadSource.PERSONAL_CENTER if i % 2 == 0 else UploadSource.CHECKUP_PLAN
            self._create_upload_with_image(source, datetime(2025, 1, 1, 12, 0, 0) + timedelta(days=i))
        for j in range(3):
            self._create_upload_with_image(UploadSource.DOCTOR_BACKEND, datetime(2025, 2, 1, 12, 0, 0) + timedelta(days=j))

        page1 = _get_archives_data(self.patient, page=1, page_size=10)["page_obj"]
        self.assertEqual(page1.paginator.count, 12)
        self.assertEqual(len(page1.object_list), 10)
        self.assertEqual(timezone.localtime(page1.object_list[0].created_at).date(), date(2025, 1, 12))

        page2 = _get_archives_data(self.patient, page=2, page_size=10)["page_obj"]
        self.assertEqual(len(page2.object_list), 2)
        self.assertEqual(timezone.localtime(list(page2.object_list)[-1].created_at).date(), date(2025, 1, 1))

    def test_upload_without_images_is_ignored(self):
        upload = ReportUpload.objects.create(patient=self.patient, upload_source=UploadSource.PERSONAL_CENTER)
        ReportUpload.objects.filter(id=upload.id).update(created_at=timezone.make_aware(datetime(2025, 1, 1, 10, 0, 0)))

        result = _get_archives_data(self.patient, page=1, page_size=10)
        self.assertEqual(result["archives_list"], [])
