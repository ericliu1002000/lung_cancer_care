from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.utils import timezone

from health_data.models import ClinicalEvent
from health_data.services.report_service import ReportArchiveService
from users import choices
from users.models import DoctorProfile, PatientProfile
from web_doctor.views.reports_history_data import handle_reports_history_section


User = get_user_model()


class ReportListFilterTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.doctor_user = User.objects.create_user(
            username="doc_filter",
            password="password",
            user_type=choices.UserType.DOCTOR,
            phone="13800000003",
        )
        self.doctor = DoctorProfile.objects.create(user=self.doctor_user, name="张三医生")

        self.doctor_user2 = User.objects.create_user(
            username="doc_filter_2",
            password="password",
            user_type=choices.UserType.DOCTOR,
            phone="13800000004",
        )
        self.doctor2 = DoctorProfile.objects.create(user=self.doctor_user2, name="李四")

        self.patient_user = User.objects.create_user(
            username="patient_filter",
            user_type=choices.UserType.PATIENT,
            wx_openid="test_openid_filter",
        )
        self.patient = PatientProfile.objects.create(user=self.patient_user, name="Test Patient")

        self.e_outpatient = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 1, 10),
            created_by_doctor=self.doctor,
        )
        ClinicalEvent.objects.filter(id=self.e_outpatient.id).update(
            created_at=timezone.make_aware(datetime(2025, 1, 15, 9, 0, 0))
        )

        self.e_inpatient = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=2,
            event_date=date(2025, 2, 10),
            created_by_doctor=self.doctor2,
        )
        ClinicalEvent.objects.filter(id=self.e_inpatient.id).update(
            created_at=timezone.make_aware(datetime(2025, 2, 20, 10, 0, 0))
        )

        self.e_checkup = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=3,
            event_date=date(2025, 3, 10),
            created_by_doctor=self.doctor,
        )
        ClinicalEvent.objects.filter(id=self.e_checkup.id).update(
            created_at=timezone.make_aware(datetime(2025, 3, 25, 11, 0, 0))
        )

        self.e_no_doctor = ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1,
            event_date=date(2025, 4, 10),
            created_by_doctor=None,
        )
        ClinicalEvent.objects.filter(id=self.e_no_doctor.id).update(
            created_at=timezone.make_aware(datetime(2025, 4, 15, 12, 0, 0))
        )

    def test_default_returns_all(self):
        page = ReportArchiveService.list_clinical_events(patient=self.patient, page=1, page_size=50)
        ids = {e.id for e in page.object_list}
        self.assertEqual(ids, {self.e_outpatient.id, self.e_inpatient.id, self.e_checkup.id, self.e_no_doctor.id})

    def test_filter_record_type(self):
        page = ReportArchiveService.list_clinical_events(patient=self.patient, record_type="住院", page=1, page_size=50)
        ids = [e.id for e in page.object_list]
        self.assertEqual(ids, [self.e_inpatient.id])

    def test_filter_report_date_range(self):
        page = ReportArchiveService.list_clinical_events(
            patient=self.patient,
            report_start_date=date(2025, 2, 1),
            report_end_date=date(2025, 3, 31),
            page=1,
            page_size=50,
        )
        ids = {e.id for e in page.object_list}
        self.assertEqual(ids, {self.e_inpatient.id, self.e_checkup.id})

    def test_filter_archive_date_range(self):
        page = ReportArchiveService.list_clinical_events(
            patient=self.patient,
            archive_start_date=date(2025, 2, 1),
            archive_end_date=date(2025, 2, 28),
            page=1,
            page_size=50,
        )
        ids = [e.id for e in page.object_list]
        self.assertEqual(ids, [self.e_inpatient.id])

    def test_filter_archiver_name_like(self):
        page = ReportArchiveService.list_clinical_events(
            patient=self.patient,
            archiver_name="张三",
            page=1,
            page_size=50,
        )
        ids = {e.id for e in page.object_list}
        self.assertEqual(ids, {self.e_outpatient.id, self.e_checkup.id})

    def test_filter_combination(self):
        page = ReportArchiveService.list_clinical_events(
            patient=self.patient,
            record_type="门诊",
            report_start_date=date(2025, 1, 1),
            report_end_date=date(2025, 12, 31),
            archive_start_date=date(2025, 1, 1),
            archive_end_date=date(2025, 1, 31),
            archiver_name="张三",
            page=1,
            page_size=50,
        )
        ids = [e.id for e in page.object_list]
        self.assertEqual(ids, [self.e_outpatient.id])

    def test_view_mapping_contains_archiver_name_field(self):
        request = self.factory.get(
            "/doctor/workspace/patient/{}/reports/".format(self.patient.id),
            {"tab": "records", "recordType": "all"},
        )
        context = {"patient": self.patient}
        template_name = handle_reports_history_section(request, context)
        self.assertTrue(template_name.endswith("web_doctor/partials/reports_history/list.html"))
        reports_page = context["reports_page"]
        self.assertTrue(reports_page.object_list)
        first = reports_page.object_list[0]
        self.assertIn("archiver_name", first)

    def test_date_range_invalid_is_ignored(self):
        request = self.factory.get(
            "/doctor/workspace/patient/{}/reports/".format(self.patient.id),
            {"tab": "records", "reportDateStart": "invalid-date", "reportDateEnd": "2025-03-31"},
        )
        context = {"patient": self.patient}
        handle_reports_history_section(request, context)
        ids = {item["id"] for item in context["reports_page"].object_list}
        self.assertEqual(ids, {self.e_outpatient.id, self.e_inpatient.id, self.e_checkup.id})
