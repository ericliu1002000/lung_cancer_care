from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from market.models import Order, Product
from users.models import PatientProfile
from users.services.patient import PatientService


class PatientGuardDaysTests(TestCase):
    def setUp(self) -> None:
        self.service = PatientService()
        self.patient = PatientProfile.objects.create(
            phone="13800000000",
            name="测试患者",
        )
        self.product = Product.objects.create(
            name="监护服务包",
            price="199.00",
            service_content="测试服务内容",
            duration_days=3,
            is_active=True,
        )

    def test_no_paid_orders_returns_zero(self):
        """没有已支付订单时，守护时间为 0。"""
        days = self.service.get_guard_days(self.patient)
        self.assertEqual(days, 0)

    def test_single_paid_order_counts_days_until_yesterday(self):
        """
        单个已支付订单：
        - 从支付日开始按 duration_days 计数；
        - 但最多统计到昨天为止。
        """
        now = timezone.now()
        # 支付时间为 2 天前，duration=3 天：
        # 区间为 [today-2, today]，但只统计到昨天 => 2 天。
        paid_at = now - timedelta(days=2)

        Order.objects.create(
            patient=self.patient,
            product=self.product,
            amount=self.product.price,
            status=Order.Status.PAID,
            paid_at=paid_at,
        )

        days = self.service.get_guard_days(self.patient)
        self.assertEqual(days, 2)

    def test_overlapped_paid_orders_merge_by_calendar_days(self):
        """
        多个已支付订单的服务期重叠时，按自然日去重合并。

        构造：
        - 订单 A：paid_at=today-4, duration=3 => [today-4, today-2]
        - 订单 B：paid_at=today-3, duration=3 => [today-3, today-1]
        去重后覆盖日期：today-4, -3, -2, -1 共 4 天。
        """
        now = timezone.now()

        Order.objects.create(
            patient=self.patient,
            product=self.product,
            amount=self.product.price,
            status=Order.Status.PAID,
            paid_at=now - timedelta(days=4),
        )
        Order.objects.create(
            patient=self.patient,
            product=self.product,
            amount=self.product.price,
            status=Order.Status.PAID,
            paid_at=now - timedelta(days=3),
        )

        days = self.service.get_guard_days(self.patient)
        self.assertEqual(days, 4)

    def test_non_paid_orders_are_ignored(self):
        """非 PAID 状态的订单不会计入守护时间。"""
        now = timezone.now()

        Order.objects.create(
            patient=self.patient,
            product=self.product,
            amount=self.product.price,
            status=Order.Status.PENDING,
            paid_at=None,
        )
        Order.objects.create(
            patient=self.patient,
            product=self.product,
            amount=self.product.price,
            status=Order.Status.CANCELLED,
            paid_at=now - timedelta(days=5),
        )

        days = self.service.get_guard_days(self.patient)
        self.assertEqual(days, 0)

