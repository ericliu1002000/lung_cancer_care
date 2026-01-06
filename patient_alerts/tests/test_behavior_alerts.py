from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import DailyTask, MonitoringTemplate, PlanItem, TreatmentCycle, choices as core_choices
from health_data.models import MetricType
from patient_alerts.models import AlertEventType, AlertLevel, PatientAlert
from patient_alerts.services.behavior_alerts import BehaviorAlertService
from users.models import PatientProfile


class BehaviorAlertServiceTests(TestCase):
    def setUp(self):
        self.patient = PatientProfile.objects.create(phone="18600001000", name="行为测试")
        self.today = timezone.localdate()

    def test_medication_consecutive_missed_creates_alert(self):
        as_of_date = self.today - timedelta(days=1)
        for offset in range(3):
            DailyTask.objects.create(
                patient=self.patient,
                task_date=as_of_date - timedelta(days=offset),
                task_type=core_choices.PlanItemCategory.MEDICATION,
                title="用药提醒",
                status=core_choices.TaskStatus.PENDING,
            )

        BehaviorAlertService.run(as_of_date=as_of_date, patient_ids=[self.patient.id])

        alert = PatientAlert.objects.filter(
            patient=self.patient, event_type=AlertEventType.BEHAVIOR
        ).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.MODERATE)

    def test_monitoring_consecutive_missed_creates_alert(self):
        template, _ = MonitoringTemplate.objects.get_or_create(
            code=MetricType.BLOOD_OXYGEN,
            defaults={
                "name": "血氧",
                "metric_type": MetricType.BLOOD_OXYGEN,
            },
        )
        cycle = TreatmentCycle.objects.create(
            patient=self.patient,
            name="测试疗程",
            start_date=self.today - timedelta(days=10),
        )
        plan_item = PlanItem.objects.create(
            cycle=cycle,
            category=core_choices.PlanItemCategory.MONITORING,
            template_id=template.id,
            item_name="血氧监测",
        )

        as_of_date = self.today - timedelta(days=1)
        for offset in range(3):
            DailyTask.objects.create(
                patient=self.patient,
                plan_item=plan_item,
                task_date=as_of_date - timedelta(days=offset),
                task_type=core_choices.PlanItemCategory.MONITORING,
                title="血氧监测",
                status=core_choices.TaskStatus.PENDING,
            )

        BehaviorAlertService.run(as_of_date=as_of_date, patient_ids=[self.patient.id])

        alert = PatientAlert.objects.filter(
            patient=self.patient, event_type=AlertEventType.BEHAVIOR
        ).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.MODERATE)

    def test_questionnaire_overdue_creates_alert(self):
        task_date = self.today - timedelta(days=4)
        DailyTask.objects.create(
            patient=self.patient,
            task_date=task_date,
            task_type=core_choices.PlanItemCategory.QUESTIONNAIRE,
            title="随访问卷",
            status=core_choices.TaskStatus.PENDING,
        )

        BehaviorAlertService.run(as_of_date=self.today - timedelta(days=1), patient_ids=[self.patient.id])

        alert = PatientAlert.objects.filter(
            patient=self.patient, event_type=AlertEventType.BEHAVIOR
        ).first()
        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.MODERATE)
