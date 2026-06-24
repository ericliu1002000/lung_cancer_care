import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from health_data.models import HealthMetric, MetricType
from users.models import CustomUser, PatientProfile

class RecordViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # 创建测试用户和患者
        self.user = CustomUser.objects.create_user(
            username='testpatient', 
            password='password',
            wx_openid='test_openid_record'
        )
        self.patient = PatientProfile.objects.create(user=self.user, name="Test Patient")
        self.client.force_login(self.user)

    def test_record_temperature_timezone_aware(self):
        """测试体温录入是否正确处理时区"""
        url = reverse('web_patient:record_temperature')
        # 模拟前端传入的 Beijing 时间字符串 (YYYY-MM-DD HH:MM)
        # 假设当前是北京时间 2026-01-11 19:46:00
        record_time_str = "2026-01-11 19:46"
        
        response = self.client.post(url, {
            'temperature': '36.5',
            'record_time': record_time_str,
            'record_time_touched': '1',
            'patient_id': self.patient.id
        })
        
        # 1. 验证重定向
        # 期望重定向回当前页面 (刷新)
        self.assertEqual(response.status_code, 302)
        target_url = response.url
        self.assertEqual(target_url, url)
        
        # 2. 验证数据库存储的时间是否为 Aware
        metric = HealthMetric.objects.filter(
            patient=self.patient, 
            metric_type=MetricType.BODY_TEMPERATURE
        ).last()
        
        self.assertIsNotNone(metric)
        self.assertTrue(timezone.is_aware(metric.measured_at))
        
        # 验证转换后的 UTC 时间是否正确
        # 北京时间 19:46 -> UTC 11:46
        # 注意：Django 测试数据库默认可能使用 UTC，measured_at 取出来是 UTC 时间
        utc_expected = datetime.datetime(2026, 1, 11, 11, 46, tzinfo=datetime.timezone.utc)
        self.assertEqual(metric.measured_at, utc_expected)

    def test_record_bp_timezone_aware(self):
        """测试血压录入是否正确处理时区"""
        url = reverse('web_patient:record_bp')
        record_time_str = "2026-01-11 19:46"
        
        response = self.client.post(url, {
            'ssy': '120',
            'szy': '80',
            'heart': '75',
            'record_time': record_time_str,
            'record_time_touched': '1',
            'patient_id': self.patient.id
        })
        
        self.assertEqual(response.status_code, 302)
        target_url = response.url
        self.assertEqual(target_url, url)
        
        # 检查血压记录
        bp_metric = HealthMetric.objects.filter(
            patient=self.patient,
            metric_type=MetricType.BLOOD_PRESSURE
        ).last()
        self.assertTrue(timezone.is_aware(bp_metric.measured_at))
        
        # 检查心率记录
        hr_metric = HealthMetric.objects.filter(
            patient=self.patient,
            metric_type=MetricType.HEART_RATE
        ).last()
        self.assertTrue(timezone.is_aware(hr_metric.measured_at))

    def test_record_spo2_timezone_aware(self):
        """测试血氧录入是否正确处理时区"""
        url = reverse('web_patient:record_spo2')
        record_time_str = "2026-01-11 19:46"
        
        response = self.client.post(url, {
            'spo2': '98',
            'record_time': record_time_str,
            'record_time_touched': '1',
            'patient_id': self.patient.id
        })
        
        self.assertEqual(response.status_code, 302)
        target_url = response.url
        self.assertEqual(target_url, url)
        
        metric = HealthMetric.objects.filter(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN
        ).last()
        self.assertTrue(timezone.is_aware(metric.measured_at))

    @patch("web_patient.views.record.timezone.now")
    def test_record_bp_uses_submit_time_when_time_not_touched(self, mock_now):
        """未手动切换时间时，应以提交时的服务端当前时间为准"""
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 1, 11, 10, 5, 30)
        )
        response = self.client.post(
            reverse("web_patient:record_bp"),
            {
                "ssy": "120",
                "szy": "80",
                "heart": "75",
                "record_time": "2026-01-11 10:01",
                "record_time_touched": "0",
                "patient_id": self.patient.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        bp_metric = HealthMetric.objects.filter(
            patient=self.patient,
            metric_type=MetricType.BLOOD_PRESSURE,
        ).last()
        hr_metric = HealthMetric.objects.filter(
            patient=self.patient,
            metric_type=MetricType.HEART_RATE,
        ).last()
        self.assertEqual(
            timezone.localtime(bp_metric.measured_at).strftime("%Y-%m-%d %H:%M:%S"),
            "2026-01-11 10:05:30",
        )
        self.assertEqual(bp_metric.measured_at, hr_metric.measured_at)

    @patch("web_patient.views.record.timezone.now")
    def test_record_bp_keeps_user_selected_time_when_time_touched(self, mock_now):
        """手动切换时间后，应保留用户选择时间"""
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 1, 11, 10, 5, 30)
        )
        response = self.client.post(
            reverse("web_patient:record_bp"),
            {
                "ssy": "120",
                "szy": "80",
                "heart": "75",
                "record_time": "2026-01-11 09:41",
                "record_time_touched": "1",
                "patient_id": self.patient.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        bp_metric = HealthMetric.objects.filter(
            patient=self.patient,
            metric_type=MetricType.BLOOD_PRESSURE,
        ).last()
        self.assertEqual(
            timezone.localtime(bp_metric.measured_at).strftime("%Y-%m-%d %H:%M:%S"),
            "2026-01-11 09:41:00",
        )

    @patch("web_patient.views.record.timezone.now")
    def test_record_bp_ajax_returns_saved_record_time(self, mock_now):
        """AJAX 提交成功后，应返回后端实际保存时间供前端同步展示"""
        mock_now.return_value = timezone.make_aware(
            datetime.datetime(2026, 1, 11, 10, 5, 30)
        )
        response = self.client.post(
            reverse("web_patient:record_bp"),
            {
                "ssy": "120",
                "szy": "80",
                "heart": "75",
                "record_time": "2026-01-11 10:01",
                "record_time_touched": "0",
                "patient_id": self.patient.id,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["saved_record_time"], "2026-01-11T10:05")
        self.assertEqual(payload["saved_record_time_display"], "2026/01/11 10:05")

    @patch("web_patient.views.record.invalidate_patient_home_plan_cache")
    def test_record_metric_posts_invalidate_home_plan_cache(self, mock_invalidate):
        """首页今日计划相关体征录入成功后，应清理首页计划缓存。"""
        cases = [
            (
                reverse("web_patient:record_temperature"),
                {"temperature": "36.5", "record_time": "2026-01-11 08:00", "record_time_touched": "1"},
            ),
            (
                reverse("web_patient:record_bp"),
                {"ssy": "120", "szy": "80", "heart": "75", "record_time": "2026-01-11 08:00", "record_time_touched": "1"},
            ),
            (
                reverse("web_patient:record_spo2"),
                {"spo2": "98", "record_time": "2026-01-11 08:00", "record_time_touched": "1"},
            ),
            (
                reverse("web_patient:record_weight"),
                {"weight": "65.5", "record_time": "2026-01-11 08:00", "record_time_touched": "1"},
            ),
        ]

        for url, payload in cases:
            with self.subTest(url=url):
                mock_invalidate.reset_mock()
                response = self.client.post(
                    url,
                    {**payload, "patient_id": self.patient.id},
                    HTTP_X_REQUESTED_WITH="XMLHttpRequest",
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "success")
                mock_invalidate.assert_called_once()
                self.assertEqual(mock_invalidate.call_args.args[0], self.patient.id)
                self.assertIn(timezone.localdate(), mock_invalidate.call_args.args[1])

    def test_health_record_detail_month_boundary_excludes_next_month_midnight(self):
        tz = timezone.get_current_timezone()
        month = "2025-01"
        month_end = timezone.make_aware(
            datetime.datetime(2025, 1, 31, 23, 59, 59), tz
        )
        boundary_next_month = timezone.make_aware(
            datetime.datetime(2025, 2, 1, 0, 0), tz
        )

        HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BODY_TEMPERATURE,
            measured_at=month_end,
            value_main=Decimal("36.5"),
        )
        HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BODY_TEMPERATURE,
            measured_at=boundary_next_month,
            value_main=Decimal("36.9"),
        )

        response = self.client.get(
            reverse("web_patient:health_record_detail"),
            {"type": "temperature", "title": "体温", "month": month},
        )

        self.assertEqual(response.status_code, 200)
        records = response.context["records"]
        dates = sorted(item["date"] for item in records)
        self.assertEqual(dates, ["2025-01-31"])

    def test_health_record_detail_initial_batch_uses_six_records_for_current_month(self):
        tz = timezone.get_current_timezone()
        for day in range(28, 20, -1):
            HealthMetric.objects.create(
                patient=self.patient,
                metric_type=MetricType.BODY_TEMPERATURE,
                measured_at=timezone.make_aware(
                    datetime.datetime(2025, 3, day, 8, 0),
                    tz,
                ),
                value_main=Decimal("36.5"),
            )

        response = self.client.get(
            reverse("web_patient:health_record_detail"),
            {"type": "temperature", "title": "体温", "month": "2025-03"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["records"]), 6)
        self.assertEqual(response.context["next_cursor_month"], "2025-03")
        self.assertEqual(response.context["next_cursor_offset"], 6)
        self.assertEqual(
            [item["date"] for item in response.context["records"]],
            [
                "2025-03-28",
                "2025-03-27",
                "2025-03-26",
                "2025-03-25",
                "2025-03-24",
                "2025-03-23",
            ],
        )

    def test_health_record_detail_initial_batch_fills_previous_month_when_current_month_not_enough(self):
        tz = timezone.get_current_timezone()
        for day in (28, 18):
            HealthMetric.objects.create(
                patient=self.patient,
                metric_type=MetricType.BODY_TEMPERATURE,
                measured_at=timezone.make_aware(
                    datetime.datetime(2025, 3, day, 8, 0),
                    tz,
                ),
                value_main=Decimal("36.5"),
            )
        for day in (26, 22, 18, 12, 8):
            HealthMetric.objects.create(
                patient=self.patient,
                metric_type=MetricType.BODY_TEMPERATURE,
                measured_at=timezone.make_aware(
                    datetime.datetime(2025, 2, day, 8, 0),
                    tz,
                ),
                value_main=Decimal("36.5"),
            )

        response = self.client.get(
            reverse("web_patient:health_record_detail"),
            {"type": "temperature", "title": "体温", "month": "2025-03"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["records"]), 6)
        self.assertEqual(response.context["next_cursor_month"], "2025-02")
        self.assertEqual(response.context["next_cursor_offset"], 4)
        self.assertEqual(
            [item["date"] for item in response.context["records"]],
            [
                "2025-03-28",
                "2025-03-18",
                "2025-02-26",
                "2025-02-22",
                "2025-02-18",
                "2025-02-12",
            ],
        )

        ajax_response = self.client.get(
            reverse("web_patient:health_record_detail"),
            {
                "type": "temperature",
                "title": "体温",
                "month": "2025-03",
                "cursor_month": "2025-02",
                "cursor_offset": 4,
                "limit": 6,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(ajax_response.status_code, 200)
        payload = ajax_response.json()
        self.assertEqual([item["date"] for item in payload["records"]], ["2025-02-08"])
        self.assertFalse(payload["has_more"])
        self.assertIsNone(payload["next_cursor_month"])
        self.assertIsNone(payload["next_cursor_offset"])

    def test_health_record_detail_bp_renders_single_line_value(self):
        tz = timezone.get_current_timezone()
        HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_PRESSURE,
            measured_at=timezone.make_aware(
                datetime.datetime(2025, 3, 28, 8, 0),
                tz,
            ),
            value_main=Decimal("120"),
            value_sub=Decimal("80"),
        )

        response = self.client.get(
            reverse("web_patient:health_record_detail"),
            {"type": "bp", "title": "血压", "month": "2025-03"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "血压:")
        self.assertContains(response, "120 / 80")
