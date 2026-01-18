from django.test import TestCase
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from users.models import PatientProfile
from health_data.models import ClinicalEvent
from web_doctor.views.home import _get_checkup_timeline_data, build_home_context

class TestHomeCheckupTimeline(TestCase):
    def setUp(self):
        self.patient = PatientProfile.objects.create(
            name="Test Patient",
            phone="13800138000"
        )

    @patch('web_doctor.views.home.get_paid_orders_for_patient')
    def test_timeline_with_service_package(self, mock_get_orders):
        # Mock order
        mock_order = MagicMock()
        mock_order.start_date = date(2023, 1, 1)
        mock_order.end_date = date(2023, 12, 31)
        mock_get_orders.return_value = [mock_order]
        
        result = _get_checkup_timeline_data(self.patient)
        timeline = result["timeline_data"]
        
        self.assertEqual(len(timeline), 12)
        self.assertEqual(timeline[0]["month_label"], "2023-01")
        self.assertEqual(timeline[-1]["month_label"], "2023-12")

    @patch('web_doctor.views.home.get_paid_orders_for_patient')
    def test_timeline_cross_year(self, mock_get_orders):
        # Mock order: 2023-11 to 2024-02
        mock_order = MagicMock()
        mock_order.start_date = date(2023, 11, 1)
        mock_order.end_date = date(2024, 2, 29)
        mock_get_orders.return_value = [mock_order]
        
        result = _get_checkup_timeline_data(self.patient)
        timeline = result["timeline_data"]
        
        # Nov, Dec, Jan, Feb -> 4 months
        self.assertEqual(len(timeline), 4)
        self.assertEqual(timeline[0]["month_label"], "2023-11")
        self.assertEqual(timeline[-1]["month_label"], "2024-02")
        
    @patch('web_doctor.views.home.get_paid_orders_for_patient')
    def test_timeline_no_package(self, mock_get_orders):
        mock_get_orders.return_value = []
        
        # Should default to last 12 months (approx)
        result = _get_checkup_timeline_data(self.patient)
        timeline = result["timeline_data"]
        
        self.assertTrue(len(timeline) >= 12)
        # Check if it ends at current month (roughly)
        today = date.today()
        current_month = today.strftime("%Y-%m")
        # Depending on implementation, end_date is today.
        self.assertEqual(timeline[-1]["month_label"], current_month)

    @patch('web_doctor.views.home.get_paid_orders_for_patient')
    def test_data_aggregation(self, mock_get_orders):
        # Setup date range: 2023-01 to 2023-03
        mock_order = MagicMock()
        mock_order.start_date = date(2023, 1, 1)
        mock_order.end_date = date(2023, 3, 31)
        mock_get_orders.return_value = [mock_order]
        
        # Create events
        # 2023-01: 1 checkup, 1 outpatient
        ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=3, # Checkup
            event_date=date(2023, 1, 15)
        )
        ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=1, # Outpatient
            event_date=date(2023, 1, 20)
        )
        # 2023-02: 2 Inpatient
        ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=2, # Inpatient
            event_date=date(2023, 2, 10)
        )
        ClinicalEvent.objects.create(
            patient=self.patient,
            event_type=2, # Inpatient
            event_date=date(2023, 2, 11)
        )
        
        result = _get_checkup_timeline_data(self.patient)
        timeline = result["timeline_data"]
        
        # Verify Jan
        jan_data = next(d for d in timeline if d["month_label"] == "2023-01")
        self.assertEqual(jan_data["checkup_count"], 1)
        self.assertEqual(jan_data["outpatient_count"], 1)
        self.assertEqual(jan_data["hospitalization_count"], 0)
        self.assertEqual(len(jan_data["events"]), 2)
        
        # Verify Feb
        feb_data = next(d for d in timeline if d["month_label"] == "2023-02")
        self.assertEqual(feb_data["hospitalization_count"], 2)

    @patch('web_doctor.views.home.get_paid_orders_for_patient')
    @patch('web_doctor.views.home.PatientService')
    @patch('web_doctor.views.home.MedicalHistoryService')
    @patch('web_doctor.views.home.get_active_treatment_cycle')
    @patch('web_doctor.views.home.ReportUploadService')
    @patch('web_doctor.views.home.get_active_checkup_library')
    def test_default_month_selection(self, mock_lib, mock_upload, mock_cycle, mock_history, mock_ps, mock_get_orders):
        # Mock services to avoid errors
        mock_ps.return_value.get_guard_days.return_value = (10, 20)
        mock_history.get_last_medical_history.return_value = None
        mock_cycle.return_value = None
        mock_upload.list_uploads.return_value.object_list = []
        mock_lib.return_value = []

        # Case 1: Today is in range
        today = date.today()
        mock_order = MagicMock()
        mock_order.start_date = today - timedelta(days=10)
        mock_order.end_date = today + timedelta(days=10)
        mock_get_orders.return_value = [mock_order]
        
        context = build_home_context(self.patient)
        self.assertEqual(context["current_month"], today.strftime("%Y-%m"))
        
        # Case 2: Today is NOT in range (past package)
        mock_order_past = MagicMock()
        mock_order_past.start_date = date(2020, 1, 1)
        mock_order_past.end_date = date(2020, 12, 31)
        mock_get_orders.return_value = [mock_order_past]
        
        context = build_home_context(self.patient)
        self.assertEqual(context["current_month"], "2020-12")
