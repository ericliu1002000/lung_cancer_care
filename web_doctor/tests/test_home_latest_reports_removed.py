from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase

from users.models import PatientProfile
from web_doctor.views.home import build_home_context


class HomeLatestReportsRemovedTests(TestCase):
    def setUp(self):
        self.patient = PatientProfile.objects.create(name="Test Patient", phone="13800138001")

    @patch("web_doctor.views.home.get_paid_orders_for_patient")
    @patch("web_doctor.views.home.PatientService")
    @patch("web_doctor.views.home.MedicalHistoryService")
    @patch("web_doctor.views.home.get_active_treatment_cycle")
    @patch("web_doctor.views.home.get_active_checkup_library")
    def test_build_home_context_has_no_latest_reports_key(self, mock_lib, mock_cycle, mock_history, mock_ps, mock_get_orders):
        mock_ps.return_value.get_guard_days.return_value = (1, 1)
        mock_history.get_last_medical_history.return_value = None
        mock_cycle.return_value = None
        mock_lib.return_value = []

        today = date.today()
        mock_order = MagicMock()
        mock_order.start_date = today - timedelta(days=1)
        mock_order.end_date = today + timedelta(days=1)
        mock_get_orders.return_value = [mock_order]

        context = build_home_context(self.patient)
        self.assertNotIn("latest_reports", context)

