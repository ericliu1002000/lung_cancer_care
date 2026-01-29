from datetime import date, datetime, timedelta
from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import CheckupLibrary
from health_data.models import HealthMetric, MetricSource, ReportImage, UploadSource
from health_data.services.health_metric import HealthMetricService
from health_data.services.report_service import ReportUploadService
from market.models import Order, Product
from users import choices
from users.models import CustomUser, PatientProfile


class HealthRecordsCheckupCountsRegressionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username="testpatient_health_records_checkup_counts",
            password="password",
            user_type=choices.UserType.PATIENT,
            wx_openid="test_openid_health_records_checkup_counts",
        )
        self.patient = PatientProfile.objects.create(
            user=self.user, name="Test Patient", phone="13900002001"
        )
        self.client.force_login(self.user)

        self.checkup_item = CheckupLibrary.objects.create(
            name="血常规",
            code="BLOOD_ROUTINE",
            is_active=True,
        )

        product = Product.objects.create(
            name="VIP 服务包",
            price=Decimal("199.00"),
            duration_days=30,
            is_active=True,
        )
        self.order = Order.objects.create(
            patient=self.patient,
            product=product,
            amount=Decimal("199.00"),
            status=Order.Status.PAID,
            paid_at=timezone.now(),
        )

    def test_health_records_checkup_counts_matches_query_metrics_by_type(self):
        start_date = self.order.start_date
        end_date = self.order.end_date

        in_range_dates = [
            start_date,
            min(end_date, start_date + timedelta(days=1)),
            min(end_date, start_date + timedelta(days=2)),
        ]
        out_range_date = start_date - timedelta(days=10)

        for d in in_range_dates:
            ReportUploadService.create_upload(
                self.patient,
                images=[
                    {
                        "image_url": f"https://example.com/{d.isoformat()}.png",
                        "record_type": ReportImage.RecordType.CHECKUP,
                        "checkup_item_id": self.checkup_item.id,
                        "report_date": d,
                    }
                ],
                upload_source=UploadSource.CHECKUP_PLAN,
            )
            HealthMetric.objects.create(
                patient=self.patient,
                metric_type=self.checkup_item.code,
                source=MetricSource.MANUAL,
                measured_at=timezone.make_aware(datetime.combine(d, datetime.min.time())),
            )

        ReportUploadService.create_upload(
            self.patient,
            images=[
                {
                    "image_url": "https://example.com/out.png",
                    "record_type": ReportImage.RecordType.CHECKUP,
                    "checkup_item_id": self.checkup_item.id,
                    "report_date": out_range_date,
                }
            ],
            upload_source=UploadSource.CHECKUP_PLAN,
        )
        HealthMetric.objects.create(
            patient=self.patient,
            metric_type=self.checkup_item.code,
            source=MetricSource.MANUAL,
            measured_at=timezone.make_aware(datetime.combine(out_range_date, datetime.min.time())),
        )

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        old_page = HealthMetricService.query_metrics_by_type(
            patient_id=self.patient.id,
            metric_type=self.checkup_item.code,
            page=1,
            page_size=1,
            start_date=start_dt,
            end_date=end_dt,
        )
        old_count = old_page.paginator.count

        response = self.client.get(reverse("web_patient:health_records"))
        self.assertEqual(response.status_code, 200)
        stats = response.context["checkup_stats"]
        self.assertTrue(len(stats) > 0)

        item = next((s for s in stats if s.get("code") == self.checkup_item.code), None)
        self.assertIsNotNone(item)
        self.assertEqual(int(item.get("count") or 0), int(old_count))
