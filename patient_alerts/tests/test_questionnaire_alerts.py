from decimal import Decimal

from django.test import TestCase

from core.models import Questionnaire, QuestionnaireCode
from health_data.models import QuestionnaireSubmission
from patient_alerts.models import AlertEventType, AlertLevel
from patient_alerts.services.questionnaire_alerts import QuestionnaireAlertService
from users.models import PatientProfile


class QuestionnaireAlertServiceTests(TestCase):
    def setUp(self):
        self.patient = PatientProfile.objects.create(phone="18600000111")

    def _get_questionnaire(self, code: str, name: str) -> Questionnaire:
        questionnaire, _ = Questionnaire.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "calculation_strategy": "SUM",
            },
        )
        return questionnaire

    def test_alert_created_when_grade_is_mild(self):
        questionnaire = self._get_questionnaire(QuestionnaireCode.Q_PHYSICAL, "体能评分")
        submission = QuestionnaireSubmission.objects.create(
            patient=self.patient,
            questionnaire=questionnaire,
            total_score=Decimal("2.00"),
        )

        alert = QuestionnaireAlertService.process_submission(submission)

        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_type, AlertEventType.QUESTIONNAIRE)
        self.assertEqual(alert.event_level, AlertLevel.MILD)

    def test_no_alert_when_grade_is_normal(self):
        questionnaire = self._get_questionnaire(QuestionnaireCode.Q_PHYSICAL, "体能评分")
        submission = QuestionnaireSubmission.objects.create(
            patient=self.patient,
            questionnaire=questionnaire,
            total_score=Decimal("1.00"),
        )

        alert = QuestionnaireAlertService.process_submission(submission)

        self.assertIsNone(alert)

    def test_alerts_for_all_questionnaires(self):
        cases = [
            (QuestionnaireCode.Q_PHYSICAL, "体能评分", Decimal("2.00"), AlertLevel.MILD),
            (QuestionnaireCode.Q_BREATH, "呼吸困难评估", Decimal("2.00"), AlertLevel.MILD),
            (QuestionnaireCode.Q_COUGH, "咳嗽与痰色评估", Decimal("9.00"), AlertLevel.SEVERE),
            (QuestionnaireCode.Q_APPETITE, "食欲评估", Decimal("4.00"), AlertLevel.MILD),
            (QuestionnaireCode.Q_PAIN, "身体疼痛评估", Decimal("9.00"), AlertLevel.MODERATE),
            (QuestionnaireCode.Q_SLEEP, "睡眠质量评估", Decimal("30.00"), AlertLevel.MODERATE),
            (QuestionnaireCode.Q_DEPRESSIVE, "抑郁评估", Decimal("5.00"), AlertLevel.MILD),
            (QuestionnaireCode.Q_ANXIETY, "焦虑评估", Decimal("5.00"), AlertLevel.MILD),
        ]

        for code, name, score, expected_level in cases:
            with self.subTest(code=code):
                questionnaire = self._get_questionnaire(code, name)
                submission = QuestionnaireSubmission.objects.create(
                    patient=self.patient,
                    questionnaire=questionnaire,
                    total_score=score,
                )
                alert = QuestionnaireAlertService.process_submission(submission)
                self.assertIsNotNone(alert)
                self.assertEqual(alert.event_type, AlertEventType.QUESTIONNAIRE)
                self.assertEqual(alert.event_level, expected_level)
