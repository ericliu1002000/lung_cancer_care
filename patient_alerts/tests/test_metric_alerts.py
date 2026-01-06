from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from health_data.models import HealthMetric, MetricSource, MetricType
from patient_alerts.models import AlertEventType, AlertLevel, PatientAlert
from patient_alerts.services.metric_alerts import MetricAlertService
from users import choices
from users.models import CustomUser, DoctorProfile, PatientProfile


class MetricAlertServiceTests(TestCase):
    def setUp(self):
        self.doctor_user = CustomUser.objects.create_user(
            user_type=choices.UserType.DOCTOR,
            phone="13800138099",
            wx_nickname="Dr. Test",
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor_user,
            name="测试医生",
            hospital="测试医院",
        )
        self.patient = PatientProfile.objects.create(
            phone="18600000099",
            name="测试患者",
            doctor=self.doctor_profile,
            baseline_blood_oxygen=98,
            baseline_weight=Decimal("60.0"),
            baseline_blood_pressure_sbp=120,
            baseline_blood_pressure_dbp=80,
        )

    def test_spo2_alert_created_for_mild(self):
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN,
            value_main=Decimal("94"),
            measured_at=timezone.now(),
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_type, AlertEventType.DATA)
        self.assertEqual(alert.event_level, AlertLevel.MILD)
        self.assertEqual(PatientAlert.objects.count(), 1)

    def test_spo2_alert_created_for_severe(self):
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN,
            value_main=Decimal("89"),
            measured_at=timezone.now(),
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.SEVERE)

    def test_temperature_alert_for_72h_persistent_high(self):
        now = timezone.now()
        HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BODY_TEMPERATURE,
            value_main=Decimal("38.2"),
            measured_at=now - timedelta(hours=72),
            source=MetricSource.MANUAL,
        )
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BODY_TEMPERATURE,
            value_main=Decimal("38.2"),
            measured_at=now,
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.SEVERE)

    def test_temperature_alert_for_high_value(self):
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BODY_TEMPERATURE,
            value_main=Decimal("39.5"),
            measured_at=timezone.now(),
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.SEVERE)

    def test_weight_alert_when_change_over_3_days(self):
        now = timezone.now()
        HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.WEIGHT,
            value_main=Decimal("60.0"),
            measured_at=now - timedelta(days=2),
            source=MetricSource.MANUAL,
        )
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.WEIGHT,
            value_main=Decimal("63.0"),
            measured_at=now,
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.MILD)

    def test_weight_alert_when_change_over_180_days(self):
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.WEIGHT,
            value_main=Decimal("64.0"),
            measured_at=timezone.now(),
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.MILD)

    def test_blood_pressure_alert_created(self):
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_PRESSURE,
            value_main=Decimal("150"),
            value_sub=Decimal("100"),
            measured_at=timezone.now(),
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.SEVERE)

    def test_blood_pressure_alert_for_mild_deviation(self):
        metric = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_PRESSURE,
            value_main=Decimal("132"),
            value_sub=Decimal("88"),
            measured_at=timezone.now(),
            source=MetricSource.MANUAL,
        )

        alert = MetricAlertService.process_metric(metric)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_level, AlertLevel.MILD)

    def test_metric_alert_upgrades_instead_of_duplicate(self):
        time_now = timezone.now()
        metric_low = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN,
            value_main=Decimal("94"),
            measured_at=time_now - timedelta(hours=1),
            source=MetricSource.MANUAL,
        )
        MetricAlertService.process_metric(metric_low)

        metric_high = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN,
            value_main=Decimal("89"),
            measured_at=time_now,
            source=MetricSource.MANUAL,
        )
        MetricAlertService.process_metric(metric_high)

        alerts = PatientAlert.objects.filter(
            patient=self.patient,
            event_type=AlertEventType.DATA,
            event_title="血氧异常",
        )
        self.assertEqual(alerts.count(), 1)
        self.assertEqual(alerts.first().event_level, AlertLevel.SEVERE)

    def test_spo2_confirmed_drop_promotes_level(self):
        time_now = timezone.now()
        metric_first = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN,
            value_main=Decimal("93"),
            measured_at=time_now - timedelta(hours=1),
            source=MetricSource.MANUAL,
        )
        alert_first = MetricAlertService.process_metric(metric_first)
        self.assertIsNotNone(alert_first)
        self.assertEqual(alert_first.event_level, AlertLevel.MILD)

        metric_second = HealthMetric.objects.create(
            patient=self.patient,
            metric_type=MetricType.BLOOD_OXYGEN,
            value_main=Decimal("93"),
            measured_at=time_now,
            source=MetricSource.MANUAL,
        )
        alert_second = MetricAlertService.process_metric(metric_second)
        self.assertIsNotNone(alert_second)
        self.assertEqual(alert_second.event_level, AlertLevel.MODERATE)
