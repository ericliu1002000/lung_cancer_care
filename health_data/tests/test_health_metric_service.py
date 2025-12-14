from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone

from health_data.models import MetricType, MetricSource
from health_data.services.health_metric import HealthMetricService


class HealthMetricServiceTest(TestCase):
    def setUp(self):
        # 模拟数据
        self.patient_id = 1001
        self.measured_at = timezone.now()

    @patch("health_data.models.HealthMetric.objects.create")
    def test_save_manual_sputum_color(self, mock_create):
        """
        测试手动保存痰色指标。
        验证重点：
        1. source 是否自动被标记为 MANUAL。
        2. value_main 是否正确传入。
        3. value_sub 是否默认为 None。
        """
        # 准备数据：痰色为 3 (黄绿色/脓性)
        metric_type = MetricType.SPUTUM_COLOR
        value = Decimal("3")

        # 调用服务方法
        HealthMetricService.save_manual_metric(
            patient_id=self.patient_id,
            metric_type=metric_type,
            measured_at=self.measured_at,
            value_main=value
        )

        # 断言：验证 ORM 的 create 方法是否被以正确的参数调用
        mock_create.assert_called_once_with(
            patient_id=self.patient_id,
            metric_type=metric_type,
            source=MetricSource.MANUAL,  # 核心验证点
            value_main=value,
            value_sub=None,              # 核心验证点
            measured_at=self.measured_at
        )

    @patch("health_data.models.HealthMetric.objects.create")
    def test_save_manual_pain_score(self, mock_create):
        """
        测试手动保存疼痛评分。
        """
        # 准备数据：头部疼痛 7 分
        metric_type = MetricType.PAIN_HEAD
        value = Decimal("7")

        HealthMetricService.save_manual_metric(
            patient_id=self.patient_id,
            metric_type=metric_type,
            measured_at=self.measured_at,
            value_main=value
        )

        # 断言参数
        mock_create.assert_called_once_with(
            patient_id=self.patient_id,
            metric_type=metric_type,
            source=MetricSource.MANUAL,
            value_main=value,
            value_sub=None,
            measured_at=self.measured_at
        )