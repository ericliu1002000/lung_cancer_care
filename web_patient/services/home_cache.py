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
