from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from health_data.models import HealthMetric, MetricSource, MetricType
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

    @patch("health_data.models.HealthMetric.objects.filter")
    @patch("django.apps.apps.get_model")
    def test_query_last_metric(self, mock_get_model, mock_filter):
        """
        测试查询最新指标数据 (query_last_metric)。
        涵盖：
        1. 模拟 PatientProfile 存在。
        2. 模拟数据库查询返回不同类型的 HealthMetric 数据。
        3. 验证 value_display 格式化逻辑。
        4. 验证查询所有 vs 查询单个。
        """
        # 1. 模拟 PatientProfile.objects.filter(id=...).exists() 返回 True
        mock_patient_model = MagicMock()
        mock_patient_model.objects.filter.return_value.exists.return_value = True
        mock_get_model.return_value = mock_patient_model

        # 2. 模拟 HealthMetric.objects.filter(...).order_by(...).first() 的行为
        def filter_side_effect(**kwargs):
            m_type = kwargs.get("metric_type")
            mock_qs = MagicMock()
            mock_metric = MagicMock()

            if m_type == MetricType.BLOOD_PRESSURE:
                # A. 血压 (数值型，有副值)
                mock_metric.metric_type = MetricType.BLOOD_PRESSURE
                mock_metric.value_main = Decimal("118")
                mock_metric.value_sub = Decimal("78")
                mock_metric.measured_at = timezone.now()
                mock_metric.source = MetricSource.DEVICE
                mock_metric.display_value = "118/78"
                mock_qs.order_by.return_value.first.return_value = mock_metric
            elif m_type == MetricType.SPUTUM_COLOR:
                # B. 痰色 (枚举型) - 3: 黄绿色/脓性
                mock_metric.metric_type = MetricType.SPUTUM_COLOR
                mock_metric.value_main = Decimal("3")
                mock_metric.value_sub = None
                mock_metric.measured_at = timezone.now()
                mock_metric.source = MetricSource.MANUAL
                mock_metric.display_value = "黄绿色/脓性（提示细菌感染，需警惕）"
                mock_qs.order_by.return_value.first.return_value = mock_metric
            elif m_type == MetricType.WEIGHT:
                # C. 体重 (数值型，带单位)
                mock_metric.metric_type = MetricType.WEIGHT
                mock_metric.value_main = Decimal("65.50")
                mock_metric.value_sub = None
                mock_metric.measured_at = timezone.now()
                mock_metric.source = MetricSource.DEVICE
                mock_metric.display_value = "65.5 kg"
                mock_qs.order_by.return_value.first.return_value = mock_metric
            else:
                # 其他类型无数据
                mock_qs.order_by.return_value.first.return_value = None

            return mock_qs

        mock_filter.side_effect = filter_side_effect

        # --- 测试场景 1: 查询所有指标 ---
        result_all = HealthMetricService.query_last_metric(self.patient_id)

        # 验证血压格式化
        bp_data = result_all[MetricType.BLOOD_PRESSURE]
        self.assertIsNotNone(bp_data)
        self.assertEqual(bp_data["value_display"], "118/78")
        self.assertEqual(bp_data["name"], "血压")

        # 验证痰色翻译
        sputum_data = result_all[MetricType.SPUTUM_COLOR]
        self.assertIsNotNone(sputum_data)
        self.assertIn("黄绿色/脓性", sputum_data["value_display"])

        # 验证体重单位
        weight_data = result_all[MetricType.WEIGHT]
        self.assertEqual(weight_data["value_display"], "65.5 kg")

        # 验证无数据的指标 (例如心率)
        self.assertIsNone(result_all[MetricType.HEART_RATE])

        # --- 测试场景 2: 查询单个指标 ---
        result_single = HealthMetricService.query_last_metric(
            self.patient_id, metric_type=MetricType.BLOOD_PRESSURE
        )
        self.assertIn(MetricType.BLOOD_PRESSURE, result_single)
        self.assertNotIn(MetricType.SPUTUM_COLOR, result_single)

        # --- 测试场景 3: 患者不存在 ---
        mock_patient_model.objects.filter.return_value.exists.return_value = False
        # 模拟抛出 DoesNotExist (Mock 的 DoesNotExist 只是一个类)
        mock_patient_model.DoesNotExist = Exception
        with self.assertRaises(Exception):
            HealthMetricService.query_last_metric(999)

    @patch("health_data.models.HealthMetric.objects.filter")
    def test_query_metrics_by_type(self, mock_filter):
        """
        测试查询历史数据列表 (query_metrics_by_type)。
        验证：
        1. 返回的对象具备分页所需属性。
        2. page_size 限制逻辑 (最大 100)。
        3. 数据排序和分页。
        """
        # 模拟 QuerySet 及其 order_by 返回值
        mock_qs = MagicMock()
        mock_filter.return_value = mock_qs

        mock_ordered_qs = MagicMock()
        mock_qs.order_by.return_value = mock_ordered_qs

        # 模拟 Paginator.page 返回的“分页对象”
        mock_page = MagicMock()

        mock_metrics_list = []
        for i in range(30):
            m = MagicMock()
            m.id = i
            m.value_main = Decimal("60")
            m.value_sub = None
            m.metric_type = MetricType.WEIGHT
            m.measured_at = timezone.now()
            m.source = MetricSource.DEVICE
            mock_metrics_list.append(m)

        mock_page.object_list = mock_metrics_list
        mock_page.number = 1
        mock_page_paginator = MagicMock()
        mock_page_paginator.count = 150
        mock_page_paginator.num_pages = 2
        mock_page.paginator = mock_page_paginator

        # 为了不依赖真实 Paginator，这里直接打补丁 Paginator，使其返回我们的 mock_page
        with patch("health_data.services.health_metric.Paginator") as mock_paginator_cls:
            mock_paginator = MagicMock()
            mock_paginator.page.return_value = mock_page
            mock_paginator_cls.return_value = mock_paginator

            # --- 调用测试 ---
            # 请求 page_size=200，预期被限制为 100
            result_page = HealthMetricService.query_metrics_by_type(
                self.patient_id,
                MetricType.WEIGHT,
                page=1,
                page_size=200,
            )

        # --- 验证 ---
        # 1. 返回的对象就是我们构造的 mock_page，且具备分页属性
        self.assertIs(result_page, mock_page)
        self.assertEqual(result_page.object_list, mock_metrics_list)
        self.assertEqual(result_page.paginator.count, 150)

        # 2. 验证 page_size 限制：Paginator 应当用 100 作为 per_page
        mock_paginator_cls.assert_called_once()
        args, kwargs = mock_paginator_cls.call_args
        # args[0] 是 queryset，args[1] 是 per_page
        self.assertEqual(args[1], 100)

        # 3. 验证 filter 参数
        mock_filter.assert_called_with(
            patient_id=self.patient_id, metric_type=MetricType.WEIGHT
        )
