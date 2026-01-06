from __future__ import annotations

from decimal import Decimal
from typing import Any

from patient_alerts.models import AlertEventType, AlertLevel, PatientAlert
from patient_alerts.services.patient_alert import PatientAlertService
from health_data.models import QuestionnaireSubmission


class QuestionnaireAlertService:
    """
    【功能说明】
    - 根据问卷提交结果生成异常报警。
    - 仅对轻/中/重等级触发待办。
    """

    GRADE_TO_LEVEL = {
        2: AlertLevel.MILD,
        3: AlertLevel.MODERATE,
        4: AlertLevel.SEVERE,
    }

    @classmethod
    def process_submission(
        cls, submission: QuestionnaireSubmission
    ) -> PatientAlert | None:
        """
        处理问卷提交并生成报警。

        【参数说明】
        - submission: QuestionnaireSubmission 问卷提交记录。

        【返回值说明】
        - PatientAlert | None：未触发报警返回 None。
        """
        if not submission:
            return None

        try:
            grade_level = submission.grade_level
        except Exception:
            return None
        alert_level = cls.GRADE_TO_LEVEL.get(grade_level)
        if not alert_level:
            return None

        total_score = submission.total_score or Decimal("0")
        title = f"{submission.questionnaire.name}异常"
        content = (
            f"总分 {total_score}，分级 {grade_level} 级"
        )
        payload: dict[str, Any] = {
            "questionnaire_id": submission.questionnaire_id,
            "questionnaire_code": submission.questionnaire.code,
            "total_score": str(total_score),
            "grade_level": grade_level,
        }
        return PatientAlertService.create_or_update_alert(
            patient_id=submission.patient_id,
            event_type=AlertEventType.QUESTIONNAIRE,
            event_level=alert_level,
            event_title=title,
            event_content=content,
            event_time=submission.created_at,
            source_type="questionnaire",
            source_id=submission.id,
            source_payload=payload,
            dedup_filters={
                "event_title": title,
                "source_type": "questionnaire",
            },
        )
