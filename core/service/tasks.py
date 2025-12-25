from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from core.models import DailyTask, choices
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
