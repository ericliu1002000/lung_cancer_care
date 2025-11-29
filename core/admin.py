from django.contrib import admin

from core.models import Medication


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "trade_names",
        "abbr_display",
        "drug_type",
        "target_gene",
        "is_active",
    )
    search_fields = (
        "name",
        "trade_names",
        "name_abbr",
        "trade_names_abbr",
    )
    list_filter = ("drug_type", "method", "is_active")

    fieldsets = (
        (
            "基础信息",
            {
                "fields": (
                    "name",
                    "trade_names",
                    "drug_type",
                    "method",
                )
            },
        ),
        (
            "拼音简码（系统自动生成，仅展示）",
            {
                "fields": (
                    "name_abbr",
                    "trade_names_abbr",
                )
            },
        ),
        (
            "推荐用法",
            {
                "fields": (
                    "target_gene",
                    "default_dosage",
                    "default_frequency",
                    "default_cycle",
                )
            },
        ),
        (
            "其它",
            {
                "fields": (
                    "description",
                    "is_active",
                )
            },
        ),
    )

    def abbr_display(self, obj: Medication) -> str:
        parts = [obj.name_abbr or "", obj.trade_names_abbr or ""]
        # 显示为 "AXTN / TRS" 或单个简码
        return " / ".join([p for p in parts if p])

    abbr_display.short_description = "简码"

    readonly_fields = ("name_abbr", "trade_names_abbr")
