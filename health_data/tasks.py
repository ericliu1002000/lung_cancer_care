try:
    from celery import shared_task
except ImportError:  # pragma: no cover - fallback for environments without celery installed
    def shared_task(*_args, **_kwargs):
        def decorator(func):
            func.delay = func
            return func

        return decorator

from health_data.models import CheckupOrphanField, ReportImage
from health_data.services.checkup_results import reprocess_orphan_fields, sync_lab_results_from_ai_json


@shared_task(name="health_data.sync_lab_results_from_ai_json")
def sync_lab_results_from_ai_json_task(image_id: int) -> dict:
    report_image = ReportImage.objects.select_related("upload", "checkup_item").get(pk=image_id)
    return sync_lab_results_from_ai_json(report_image)


@shared_task(name="health_data.reprocess_orphan_fields")
def reprocess_orphan_fields_task(
    orphan_ids: list[int] | None = None,
    normalized_names: list[str] | None = None,
) -> dict:
    queryset = None
    if orphan_ids:
        queryset = CheckupOrphanField.objects.filter(id__in=list(orphan_ids))
    return reprocess_orphan_fields(queryset=queryset, normalized_names=normalized_names)
