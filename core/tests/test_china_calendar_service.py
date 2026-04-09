from datetime import date

from django.test import SimpleTestCase

from core.service.china_calendar import ChinaCalendarService


class ChinaCalendarServiceTests(SimpleTestCase):
    def test_regular_weekday_is_not_highlighted(self):
        meta = ChinaCalendarService.get_day_meta(date(2026, 4, 8))

        self.assertFalse(meta["is_weekend"])
        self.assertFalse(meta["is_statutory_holiday"])
        self.assertFalse(meta["should_highlight"])
        self.assertEqual(meta["highlight_reason"], "")

    def test_weekend_is_highlighted_as_weekend(self):
        meta = ChinaCalendarService.get_day_meta(date(2026, 4, 11))

        self.assertTrue(meta["is_weekend"])
        self.assertFalse(meta["is_statutory_holiday"])
        self.assertTrue(meta["should_highlight"])
        self.assertEqual(meta["holiday_name"], "")
        self.assertEqual(meta["weekend_name"], "周六")
        self.assertEqual(meta["highlight_reason"], "周六")

    def test_sunday_is_highlighted_as_sunday(self):
        meta = ChinaCalendarService.get_day_meta(date(2026, 4, 12))

        self.assertTrue(meta["is_weekend"])
        self.assertFalse(meta["is_statutory_holiday"])
        self.assertTrue(meta["should_highlight"])
        self.assertEqual(meta["weekend_name"], "周日")
        self.assertEqual(meta["highlight_reason"], "周日")

    def test_statutory_holiday_is_highlighted_with_holiday_name(self):
        meta = ChinaCalendarService.get_day_meta(date(2026, 5, 1))

        self.assertFalse(meta["is_weekend"])
        self.assertTrue(meta["is_statutory_holiday"])
        self.assertTrue(meta["should_highlight"])
        self.assertEqual(meta["holiday_name"], "劳动节")
        self.assertEqual(meta["highlight_reason"], "劳动节")

    def test_weekend_holiday_combines_reasons(self):
        meta = ChinaCalendarService.get_day_meta(date(2025, 2, 1))

        self.assertTrue(meta["is_weekend"])
        self.assertTrue(meta["is_statutory_holiday"])
        self.assertTrue(meta["should_highlight"])
        self.assertEqual(meta["weekend_name"], "周六")
        self.assertEqual(meta["holiday_name"], "春节")
        self.assertEqual(meta["highlight_reason"], "周六 / 春节")

    def test_unsupported_year_degrades_to_weekend_only(self):
        meta = ChinaCalendarService.get_day_meta(date(2027, 1, 2))

        self.assertTrue(meta["is_weekend"])
        self.assertFalse(meta["is_statutory_holiday"])
        self.assertTrue(meta["should_highlight"])
        self.assertEqual(meta["weekend_name"], "周六")
        self.assertEqual(meta["holiday_name"], "")
        self.assertEqual(meta["highlight_reason"], "周六")
