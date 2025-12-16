"""treatment_cycle service 测试：get_treatment_cycles 分页与排序。"""

from datetime import date, timedelta

from django.test import TestCase

from core.models import TreatmentCycle, choices
from core.service.treatment_cycle import get_treatment_cycles
from users.models import PatientProfile


class TreatmentCycleServiceTest(TestCase):
    """测试 get_treatment_cycles 分页与排序逻辑。"""

    def setUp(self) -> None:
        self.patient = PatientProfile.objects.create(
            phone="13900000000",
            name="分页患者",
        )

        # 创建 15 条疗程，start_date 依次递增，便于验证倒序排序
        base_date = date(2025, 1, 1)
        for i in range(15):
            TreatmentCycle.objects.create(
                patient=self.patient,
                name=f"疗程{i}",
                start_date=base_date + timedelta(days=i),
                cycle_days=21,
                status=choices.TreatmentCycleStatus.IN_PROGRESS,
            )

    def test_get_treatment_cycles_default_first_page(self):
        """默认第一页，每页 10 条，按 start_date 倒序。"""

        page = get_treatment_cycles(self.patient)

        # 默认分页大小
        self.assertEqual(page.paginator.per_page, 10)
        self.assertEqual(page.number, 1)
        self.assertEqual(len(page.object_list), 10)

        # 第一条应是最新的疗程（start_date 最大）
        first_cycle = page.object_list[0]
        self.assertEqual(first_cycle.name, "疗程14")

    def test_get_treatment_cycles_second_page(self):
        """第二页应包含剩余 5 条记录。"""

        page = get_treatment_cycles(self.patient, page=2)

        self.assertEqual(page.number, 2)
        self.assertEqual(len(page.object_list), 5)

        # 第二页第一条应是按倒序的第 11 条
        first_cycle_second_page = page.object_list[0]
        self.assertEqual(first_cycle_second_page.name, "疗程4")

