import json
from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from core.models import TreatmentCycle, choices
from users.choices import UserType
from users.models import CustomUser, DoctorProfile, PatientProfile
from web_doctor.views import workspace


class TreatmentCycleRenameViewTests(TestCase):
    def setUp(self):
        self.doctor_user = CustomUser.objects.create_user(
            username="doctor_cycle_rename",
            password="password123",
            user_type=UserType.DOCTOR,
            phone="13900006660",
        )
        self.doctor_profile = DoctorProfile.objects.create(user=self.doctor_user, name="张医生")

        patient_user = CustomUser.objects.create_user(
            username="patient_cycle_rename",
            password="password123",
            user_type=UserType.PATIENT,
            phone="13800006660",
            wx_openid="openid_cycle_rename",
        )
        self.patient = PatientProfile.objects.create(
            user=patient_user,
            doctor=self.doctor_profile,
            name="疗程改名患者",
            phone="13800006660",
            is_active=True,
        )

        other_patient_user = CustomUser.objects.create_user(
            username="patient_cycle_rename_other",
            password="password123",
            user_type=UserType.PATIENT,
            phone="13800006661",
            wx_openid="openid_cycle_rename_other",
        )
        self.other_patient = PatientProfile.objects.create(
            user=other_patient_user,
            doctor=self.doctor_profile,
            name="其他患者",
            phone="13800006661",
            is_active=True,
        )

        self.client.login(username="doctor_cycle_rename", password="password123")

    def _patch_settings_dependencies(self):
        patches = [
            patch("web_doctor.views.workspace.get_active_medication_library", return_value=[]),
            patch("web_doctor.views.workspace.PlanItemService.get_cycle_plan_view", return_value={}),
            patch("web_doctor.views.workspace.MedicalHistoryService.get_last_medical_history", return_value=None),
            patch("web_doctor.views.workspace.get_active_treatment_cycle", return_value=None),
            patch("web_doctor.views.workspace.PatientService"),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

        patient_service_mock = workspace.PatientService.return_value
        patient_service_mock.get_patient_family_members.return_value = []

    def _rename_url(self, cycle: TreatmentCycle) -> str:
        return reverse(
            "web_doctor:patient_treatment_cycle_rename",
            args=[self.patient.id, cycle.id],
        )

    def test_not_started_cycle_can_be_renamed_and_remains_selected(self):
        self._patch_settings_dependencies()
        today = date.today()
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="原未开始疗程",
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=23),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )

        response = self.client.post(self._rename_url(cycle), {"name": "新未开始疗程"})

        self.assertEqual(response.status_code, 200)
        cycle.refresh_from_db()
        self.assertEqual(cycle.name, "新未开始疗程")
        self.assertContains(response, "当前选中：")
        self.assertContains(response, "新未开始疗程")
        self.assertContains(response, 'id="treatment-cycle-settings"')
        self.assertContains(response, 'data-cycle-select-row')
        self.assertContains(response, 'hx-target="#treatment-cycle-settings"')
        self.assertNotContains(response, "疗程改名患者")
        self.assertNotContains(response, "生命体征基线")
        plan_table_url = reverse("web_doctor:patient_settings_plan_table", args=[self.patient.id])
        self.assertContains(response, f'hx-get="{plan_table_url}?cycle_id={cycle.id}"')

    def test_settings_page_renders_inline_rename_for_editable_cycles_only(self):
        self._patch_settings_dependencies()
        today = date.today()
        editable_cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="可改名疗程",
            start_date=today,
            end_date=today + timedelta(days=20),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )
        finished_cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="不可改名疗程",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=10),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )
        settings_url = reverse("web_doctor:patient_workspace_section", args=[self.patient.id, "settings"])
        editable_url = reverse(
            "web_doctor:patient_treatment_cycle_rename",
            args=[self.patient.id, editable_cycle.id],
        )
        finished_url = reverse(
            "web_doctor:patient_treatment_cycle_rename",
            args=[self.patient.id, finished_cycle.id],
        )

        response = self.client.get(settings_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-cycle-rename-open')
        self.assertContains(response, 'data-cycle-select-row')
        self.assertContains(response, 'aria-current="true"')
        self.assertContains(response, editable_url)
        self.assertNotContains(response, finished_url)
        self.assertNotContains(response, "编辑名称")

    def test_in_progress_cycle_can_be_renamed(self):
        self._patch_settings_dependencies()
        today = date.today()
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="原进行中疗程",
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=19),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )

        response = self.client.post(self._rename_url(cycle), {"name": "新进行中疗程"})

        self.assertEqual(response.status_code, 200)
        cycle.refresh_from_db()
        self.assertEqual(cycle.name, "新进行中疗程")

    def test_naturally_finished_cycle_cannot_be_renamed(self):
        self._patch_settings_dependencies()
        today = date.today()
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="自然结束疗程",
            start_date=today - timedelta(days=30),
            end_date=today - timedelta(days=10),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )

        response = self.client.post(self._rename_url(cycle), {"name": "不应更新"})

        self.assertEqual(response.status_code, 200)
        cycle.refresh_from_db()
        self.assertEqual(cycle.name, "自然结束疗程")
        trigger_payload = json.loads(response["HX-Trigger"])
        self.assertIn("已结束或已终止的疗程不允许修改名称。", trigger_payload["plan-error"]["message"])

    def test_terminated_cycle_cannot_be_renamed(self):
        self._patch_settings_dependencies()
        today = date.today()
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="已终止疗程",
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=19),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.TERMINATED,
        )

        response = self.client.post(self._rename_url(cycle), {"name": "不应更新"})

        self.assertEqual(response.status_code, 200)
        cycle.refresh_from_db()
        self.assertEqual(cycle.name, "已终止疗程")
        trigger_payload = json.loads(response["HX-Trigger"])
        self.assertIn("已结束或已终止的疗程不允许修改名称。", trigger_payload["plan-error"]["message"])

    def test_empty_name_is_rejected(self):
        self._patch_settings_dependencies()
        today = date.today()
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="原疗程",
            start_date=today,
            end_date=today + timedelta(days=20),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )

        response = self.client.post(self._rename_url(cycle), {"name": "   "})

        self.assertEqual(response.status_code, 200)
        cycle.refresh_from_db()
        self.assertEqual(cycle.name, "原疗程")
        trigger_payload = json.loads(response["HX-Trigger"])
        self.assertIn("请填写疗程名称。", trigger_payload["plan-error"]["message"])

    def test_name_longer_than_max_length_is_rejected(self):
        self._patch_settings_dependencies()
        today = date.today()
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="原疗程",
            start_date=today,
            end_date=today + timedelta(days=20),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )

        response = self.client.post(self._rename_url(cycle), {"name": "A" * 51})

        self.assertEqual(response.status_code, 200)
        cycle.refresh_from_db()
        self.assertEqual(cycle.name, "原疗程")
        trigger_payload = json.loads(response["HX-Trigger"])
        self.assertIn("疗程名称不能超过 50 个字符。", trigger_payload["plan-error"]["message"])

    def test_cycle_from_other_patient_returns_404(self):
        self._patch_settings_dependencies()
        today = date.today()
        other_cycle = TreatmentCycle.objects.create(
            patient=self.other_patient,
            name="其他患者疗程",
            start_date=today,
            end_date=today + timedelta(days=20),
            cycle_days=21,
            status=choices.TreatmentCycleStatus.IN_PROGRESS,
        )
        url = reverse(
            "web_doctor:patient_treatment_cycle_rename",
            args=[self.patient.id, other_cycle.id],
        )

        response = self.client.post(url, {"name": "不应更新"})

        self.assertEqual(response.status_code, 404)
        other_cycle.refresh_from_db()
        self.assertEqual(other_cycle.name, "其他患者疗程")
