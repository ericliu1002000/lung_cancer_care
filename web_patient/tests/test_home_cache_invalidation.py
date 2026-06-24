from datetime import timedelta

from django.core.cache import cache
from django.test import SimpleTestCase
from django.utils import timezone

from web_patient.services.home_cache import (
    build_patient_home_cache_key,
    invalidate_patient_home_plan_cache,
)


class PatientHomePlanCacheInvalidationTests(SimpleTestCase):
    def tearDown(self):
        cache.clear()

    def test_invalidate_patient_home_plan_cache_deletes_plan_and_metric_keys(self):
        patient_id = 123
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)

        for target_date in (today, yesterday):
            date_key = target_date.strftime("%Y%m%d")
            cache.set(
                build_patient_home_cache_key("daily_plan_summary", patient_id, date_key),
                {"old": "plan"},
            )
            cache.set(
                build_patient_home_cache_key("last_metric", patient_id, date_key),
                {"old": "metric"},
            )

        invalidate_patient_home_plan_cache(patient_id, dates=[today, yesterday.strftime("%Y-%m-%d")])

        for target_date in (today, yesterday):
            date_key = target_date.strftime("%Y%m%d")
            self.assertIsNone(
                cache.get(build_patient_home_cache_key("daily_plan_summary", patient_id, date_key))
            )
            self.assertIsNone(
                cache.get(build_patient_home_cache_key("last_metric", patient_id, date_key))
            )

