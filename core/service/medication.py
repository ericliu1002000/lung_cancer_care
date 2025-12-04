"""药物知识库相关业务服务。

【角色定位】
- 面向上层业务（如 web_doctor 管理设置），提供“可用药物列表”等查询能力；
- 保持 fat service / thin views，避免在视图中直接拼 ORM 细节。
"""

from __future__ import annotations

from typing import Iterable, List, TypedDict

from django.db.models import Q

from core.models import Medication


class MedicationPlanItem(TypedDict):
    """用于前端展示的用药计划条目结构。"""

    lib_id: int
    name: str
    type: str
    default_dosage: str
    default_frequency: str
    keywords: str
    schedule: list[int]


def get_active_medication_library() -> List[MedicationPlanItem]:
    """
    【功能说明】
    - 查询所有启用中的药物（is_active=True），并按名称排序；
    - 将药物基础信息转换为前端展示友好的结构，用于“医院计划设置”中的用药计划区域。

    【返回参数说明】
    - 返回 MedicationPlanItem 列表，每项包含：
      - lib_id: 药物库主键 ID；
      - name: 药物名称（通用名）；
      - type: 药物类型展示文本；
      - default_dosage: 默认剂量描述；
      - default_frequency: 默认频次描述；
      - schedule: 推荐执行天数模板（若为空则返回 []）。
    """

    qs: Iterable[Medication] = Medication.objects.filter(is_active=True).order_by("name")

    items: List[MedicationPlanItem] = []
    for med in qs:
        keywords = " ".join(
            [
                med.name or "",
                med.trade_names or "",
                med.name_abbr or "",
                med.trade_names_abbr or "",
            ]
        ).strip()
        items.append(
            MedicationPlanItem(
                lib_id=med.id,
                name=med.name,
                type=med.get_drug_type_display(),
                default_dosage=med.default_dosage or "",
                default_frequency=med.default_frequency or "",
                keywords=keywords,
                schedule=list(med.schedule_days_template or []),
            )
        )
    return items


def search_medications(keyword: str, limit: int = 10) -> List[MedicationPlanItem]:
    """
    【功能说明】
    - 按名称/商品名/拼音简码在药物知识库中进行模糊检索，返回匹配的药物列表。

    【参数说明】
    - keyword: 搜索关键字，支持中文名、商品名或拼音首字母简码；
    - limit: 返回的最大条目数，默认 10。

    【返回参数说明】
    - 与 get_active_medication_library 相同的 MedicationPlanItem 列表，仅包含匹配结果。
    """

    qs = Medication.objects.filter(is_active=True)
    keyword = (keyword or "").strip()
    if keyword:
        qs = qs.filter(
            Q(name__icontains=keyword)
            | Q(trade_names__icontains=keyword)
            | Q(name_abbr__icontains=keyword)
            | Q(trade_names_abbr__icontains=keyword)
        )
    qs = qs.order_by("name")[:limit]

    items: List[MedicationPlanItem] = []
    for med in qs:
        keywords_full = " ".join(
            [
                med.name or "",
                med.trade_names or "",
                med.name_abbr or "",
                med.trade_names_abbr or "",
            ]
        ).strip()
        items.append(
            MedicationPlanItem(
                lib_id=med.id,
                name=med.name,
                type=med.get_drug_type_display(),
                default_dosage=med.default_dosage or "",
                default_frequency=med.default_frequency or "",
                keywords=keywords_full,
                schedule=list(med.schedule_days_template or []),
            )
        )
    return items
