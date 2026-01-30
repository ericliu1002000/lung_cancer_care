from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from health_data.models import HealthMetric, MetricType
from users.models import CustomUser, PatientProfile


class HealthRecordCanOperateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testpatient_health_record_can_operate",
            password="password",
            wx_openid="test_openid_health_record_can_operate",
        )
        self.patient = PatientProfile.objects.create(user=self.user, name="Test Patient")
        self.client.force_login(self.user)
        self.detail_url = reverse("web_patient:health_record_detail")
        self.records_url = reverse("web_patient:health_records")

    def test_health_records_medication_entry_link_adds_readonly_params(self):
        response = self.client.get(self.records_url, {"source": "medication", "view": "detail"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "source=medication&view=detail")
        self.assertContains(response, "source=health_records")

    def test_health_record_detail_can_operate_true_by_default(self):
        month = timezone.localtime(timezone.now()).strftime("%Y-%m")
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.USE_MEDICATED,
            source="manual",
            measured_at=timezone.now(),
            value_main=Decimal("1"),
        )

        response = self.client.get(
            self.detail_url,
            {"type": "medical", "title": "用药", "month": month, "source": "health_records"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["records"][0]["can_operate"])
        self.assertEqual(payload["records"][0]["id"], metric.id)

    def test_health_record_detail_can_operate_false_for_medication_detail_view(self):
        month = timezone.localtime(timezone.now()).strftime("%Y-%m")
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.USE_MEDICATED,
            source="manual",
            measured_at=timezone.now(),
            value_main=Decimal("1"),
        )

        response = self.client.get(
            self.detail_url,
            {
                "type": "medical",
                "title": "用药",
                "month": month,
                "view": "detail",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["records"][0]["can_operate"])
        self.assertEqual(payload["records"][0]["id"], metric.id)

    def test_health_record_detail_html_hides_buttons_when_can_operate_false(self):
        month = timezone.localtime(timezone.now()).strftime("%Y-%m")
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.USE_MEDICATED,
            source="manual",
            measured_at=timezone.now(),
            value_main=Decimal("1"),
        )

        response = self.client.get(
            self.detail_url,
            {
                "type": "medical",
                "title": "用药",
                "month": month,
                "source": "health_records",
                "view": "detail",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["show_operation_controls"])
        self.assertFalse(response.context["show_add_button"])
