"""患者端计划与任务状态服务。"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List

from django.utils import timezone

from core.models import DailyTask, MonitoringTemplate, choices
from users.models import PatientProfile


_SUMMARY_TITLE_BY_TYPE = {
    choices.PlanItemCategory.MEDICATION: "用药提醒",
    choices.PlanItemCategory.CHECKUP: "复查提醒",
    choices.PlanItemCategory.QUESTIONNAIRE: "问卷提醒",
}


def get_daily_plan_summary(
    patient: PatientProfile,
    task_date: date = date.today(),
) -> List[Dict[str, Any]]:
    """
    【功能说明】
    - 汇总患者当天的计划任务，用于患者端列表展示。

    【使用方法】
    - `get_daily_plan_summary(patient)` 返回今天的计划摘要；
    - `get_daily_plan_summary(patient, date(2025, 1, 1))` 返回指定日期摘要。

    【参数说明】
    - patient: PatientProfile，当前患者。
    - task_date: date，默认为当天。

    【返回值说明】
    - List[dict]，结构示例：
      [{"task_type": 1, "status": 0, "title": "用药提醒"}]
    """

    task_types = (
        choices.PlanItemCategory.MEDICATION,
        choices.PlanItemCategory.CHECKUP,
        choices.PlanItemCategory.QUESTIONNAIRE,
        choices.PlanItemCategory.MONITORING,
    )

    tasks = (
        DailyTask.objects.filter(
            patient=patient,
            task_date=task_date,
            task_type__in=task_types,
        )
        .order_by("id")
    )

    # 按类型聚合任务，便于后续做“合并/逐条”逻辑。
    tasks_by_type = {task_type: [] for task_type in task_types}
    for task in tasks:
        tasks_by_type[task.task_type].append(task)

    summary: List[Dict[str, Any]] = []
    # 用药/复查/问卷：每类只保留一条摘要。
    for task_type in (
        choices.PlanItemCategory.MEDICATION,
        choices.PlanItemCategory.CHECKUP,
        choices.PlanItemCategory.QUESTIONNAIRE,
    ):
        task_list = tasks_by_type[task_type]
        if not task_list:
            continue
        summary.append(
            {
                "task_type": int(task_type),
                "status": int(task_list[0].status),
                "title": _SUMMARY_TITLE_BY_TYPE[task_type],
            }
        )

    # 监测：逐条返回（前端需逐项展示）。
    for task in tasks_by_type[choices.PlanItemCategory.MONITORING]:
        summary.append(
            {
                "task_type": int(task.task_type),
                "status": int(task.status),
                "title": task.title,
            }
        )

    return summary


def _resolve_task_date(occurred_at: datetime | None) -> date:
    """
    【功能说明】
    - 将事件发生时间转换为任务日期，用于筛选当日任务。

    【使用方法】
    - `_resolve_task_date(measured_at)`。

    【参数说明】
    - occurred_at: datetime | None，事件时间；为空则使用当前时间。

    【返回值说明】
    - date，对应任务日期。
    """
    if occurred_at is None:
        return timezone.localdate()
    if timezone.is_naive(occurred_at):
        return occurred_at.date()
    return timezone.localtime(occurred_at).date()


def _resolve_completed_at(occurred_at: datetime | None) -> datetime:
    """
    【功能说明】
    - 统一任务完成时间字段；若未提供则使用当前时间。

    【使用方法】
    - `_resolve_completed_at(measured_at)`。

    【参数说明】
    - occurred_at: datetime | None，事件时间。

    【返回值说明】
    - datetime，用于写入 completed_at。
    """
    return occurred_at or timezone.now()


def complete_daily_medication_tasks(
    patient_id: int,
    occurred_at: datetime | None = None,
) -> int | None:
    """
    【功能说明】
    - 将患者当天所有“用药任务”标记为已完成。

    【使用方法】
    - `complete_daily_medication_tasks(patient_id, measured_at)`。

    【参数说明】
    - patient_id: int，患者 ID。
    - occurred_at: datetime | None，事件时间，用于定位当日任务及 completed_at。

    【返回值说明】
    - int | None：返回第一条匹配任务的 ID；若无任务则返回 None。
    """
    completed_at = _resolve_completed_at(occurred_at)
    task_date = _resolve_task_date(completed_at)

    tasks = DailyTask.objects.filter(
        patient_id=patient_id,
        task_date=task_date,
        task_type=choices.PlanItemCategory.MEDICATION,
        status=choices.TaskStatus.PENDING,
    )
    task_id = tasks.values_list("id", flat=True).first()
    tasks.update(
        status=choices.TaskStatus.COMPLETED,
        completed_at=completed_at,
    )
    return task_id


def complete_daily_monitoring_tasks(
    patient_id: int,
    metric_type: str,
    occurred_at: datetime | None = None,
) -> int:
    """
    【功能说明】
    - 将患者当天指定监测项的任务标记为已完成。

    【使用方法】
    - `complete_daily_monitoring_tasks(patient_id, MetricType.BODY_TEMPERATURE, measured_at)`。

    【参数说明】
    - patient_id: int，患者 ID。
    - metric_type: str，健康指标类型（对应 MonitoringTemplate.code）。
    - occurred_at: datetime | None，事件时间，用于定位当日任务及 completed_at。

    【返回值说明】
    - int：实际更新的任务数量。
    """
    completed_at = _resolve_completed_at(occurred_at)
    task_date = _resolve_task_date(completed_at)

    template_ids = list(
        MonitoringTemplate.objects.filter(code=metric_type).values_list("id", flat=True)
    )
    if not template_ids:
        return 0

    tasks = DailyTask.objects.filter(
        patient_id=patient_id,
        task_date=task_date,
        task_type=choices.PlanItemCategory.MONITORING,
        plan_item__template_id__in=template_ids,
        status=choices.TaskStatus.PENDING,
    )
    return tasks.update(
        status=choices.TaskStatus.COMPLETED,
        completed_at=completed_at,
    )


def complete_daily_questionnaire_tasks(
    patient_id: int,
    occurred_at: datetime | None = None,
) -> int:
    """
    【功能说明】
    - 将患者当天的问卷任务标记为已完成。

    【使用方法】
    - `complete_daily_questionnaire_tasks(patient_id, submitted_at)`。

    【参数说明】
    - patient_id: int，患者 ID。
    - occurred_at: datetime | None，事件时间，用于定位当日任务及 completed_at。

    【返回值说明】
    - int：实际更新的任务数量。
    """
    completed_at = _resolve_completed_at(occurred_at)
    task_date = _resolve_task_date(completed_at)

    tasks = DailyTask.objects.filter(
        patient_id=patient_id,
        task_date=task_date,
        task_type=choices.PlanItemCategory.QUESTIONNAIRE,
        status=choices.TaskStatus.PENDING,
    )
    return tasks.update(
        status=choices.TaskStatus.COMPLETED,
        completed_at=completed_at,
    )


def complete_daily_checkup_tasks(
    patient_id: int,
    occurred_at: datetime | None = None,
) -> int:
    """
    【功能说明】
    - 将患者当天的复查任务标记为已完成。

    【使用方法】
    - `complete_daily_checkup_tasks(patient_id, uploaded_at)`。

    【参数说明】
    - patient_id: int，患者 ID。
    - occurred_at: datetime | None，事件时间，用于定位当日任务及 completed_at。

    【返回值说明】
    - int：实际更新的任务数量。
    """
    completed_at = _resolve_completed_at(occurred_at)
    task_date = _resolve_task_date(completed_at)

    tasks = DailyTask.objects.filter(
        patient_id=patient_id,
        task_date=task_date,
        task_type=choices.PlanItemCategory.CHECKUP,
        status=choices.TaskStatus.PENDING,
    )
    return tasks.update(
        status=choices.TaskStatus.COMPLETED,
        completed_at=completed_at,
    )
