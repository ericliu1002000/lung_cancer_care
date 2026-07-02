from datetime import date, datetime

from django.core.cache import cache
from django.utils import timezone

HOME_CACHE_TTL_SECONDS = 30


def build_patient_home_cache_key(
    namespace: str,
    patient_id: int,
    date_key: str,
    user_id: int | None = None,
) -> str:
    """Build the shared patient-home cache key for one dashboard payload."""
    if user_id is None:
        return f"web_patient:home:{namespace}:{patient_id}:{date_key}"
    return f"web_patient:home:{namespace}:{patient_id}:{user_id}:{date_key}"


def _normalize_home_plan_cache_date_keys(dates=None) -> list[str]:
    if dates is None:
        dates = [timezone.localdate()]
    elif isinstance(dates, (date, datetime, str)):
        dates = [dates]

    date_keys = []
    for item in dates:
        if isinstance(item, datetime):
            date_keys.append(item.date().strftime("%Y%m%d"))
            continue
        if isinstance(item, date):
            date_keys.append(item.strftime("%Y%m%d"))
            continue

        value = str(item or "").strip()
        if not value:
            continue
        if len(value) == 8 and value.isdigit():
            date_keys.append(value)
            continue
        try:
            date_keys.append(datetime.strptime(value, "%Y-%m-%d").strftime("%Y%m%d"))
        except ValueError:
            continue

    return list(dict.fromkeys(date_keys))


def invalidate_patient_home_plan_cache(patient_id: int, dates=None) -> None:
    """Delete patient-home daily plan and last-metric cache entries."""
    if not patient_id:
        return

    cache_keys = []
    for date_key in _normalize_home_plan_cache_date_keys(dates):
        cache_keys.append(
            build_patient_home_cache_key("daily_plan_summary", int(patient_id), date_key)
        )
        cache_keys.append(
            build_patient_home_cache_key("last_metric", int(patient_id), date_key)
        )

    if cache_keys:
        cache.delete_many(cache_keys)


def get_patient_home_unread_cache_key(
    patient_id: int,
    user_id: int,
    date_key: str | None = None,
) -> str:
    """Build the patient-home unread-count cache key for one user."""
    normalized_date_key = date_key or timezone.localdate().strftime("%Y%m%d")
    return build_patient_home_cache_key(
        "unread_count",
        patient_id,
        normalized_date_key,
        user_id=user_id,
    )


def invalidate_patient_home_unread_cache(patient, user) -> None:
    """Delete today's patient-home unread-count cache for the current viewer."""
    patient_id = getattr(patient, "id", None)
    user_id = getattr(user, "id", None)
    if not patient_id or not user_id:
        return

    cache.delete(get_patient_home_unread_cache_key(int(patient_id), int(user_id)))
