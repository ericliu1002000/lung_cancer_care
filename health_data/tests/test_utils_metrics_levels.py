from decimal import Decimal

from django.test import SimpleTestCase

from health_data.utils import (
    evaluate_spo2_level,
    evaluate_blood_pressure_level,
    evaluate_heart_rate_level,
    evaluate_temperature_level,
)


class EvaluateSpo2LevelTests(SimpleTestCase):
    def test_spo2_normal_above_95(self):
        self.assertEqual(evaluate_spo2_level(95), 0)
        self.assertEqual(evaluate_spo2_level(99), 0)

    def test_spo2_absolute_thresholds(self):
        self.assertEqual(evaluate_spo2_level(94), 1)
        self.assertEqual(evaluate_spo2_level(93), 1)
        self.assertEqual(evaluate_spo2_level(92), 2)
        self.assertEqual(evaluate_spo2_level(90), 2)
        self.assertEqual(evaluate_spo2_level(89), 3)
        self.assertEqual(evaluate_spo2_level(80), 3)

    def test_spo2_baseline_drop_promotes_level(self):
        # 绝对值本身正常，但相对基线下降≥3%
        self.assertEqual(
            evaluate_spo2_level(
                current_spo2=95,
                baseline_spo2=98,
                confirmed_drop=False,
            ),
            1,
        )

        # 下降≥5%，未确认：至少 1 级
        self.assertEqual(
            evaluate_spo2_level(
                current_spo2=93,
                baseline_spo2=98,
                confirmed_drop=False,
            ),
            1,
        )

        # 下降≥5%，且复测确认：提升为 2 级
        self.assertEqual(
            evaluate_spo2_level(
                current_spo2=93,
                baseline_spo2=98,
                confirmed_drop=True,
            ),
            2,
        )

    def test_spo2_returns_zero_when_value_invalid(self):
        self.assertEqual(evaluate_spo2_level(None), 0)
        self.assertEqual(evaluate_spo2_level("invalid"), 0)  # type: ignore[arg-type]


class EvaluateBloodPressureLevelTests(SimpleTestCase):
    def test_bp_within_range_is_normal(self):
        self.assertEqual(
            evaluate_blood_pressure_level(sbp=130, dbp=85),
            0,
        )

    def test_bp_slight_deviation_below_10_percent_is_normal(self):
        # 上限 140，10% 为 14，<10% 时视为 0 级
        self.assertEqual(
            evaluate_blood_pressure_level(sbp=153, dbp=85),
            0,
        )

    def test_bp_ten_percent_deviation_is_level_1(self):
        # 收缩压：140 * 1.10 = 154 -> 1 级
        self.assertEqual(
            evaluate_blood_pressure_level(sbp=154, dbp=90),
            1,
        )

    def test_bp_between_ten_and_twenty_percent_is_level_2(self):
        # 收缩压：140 * 1.15 -> 2 级
        self.assertEqual(
            evaluate_blood_pressure_level(sbp=161, dbp=90),
            2,
        )

    def test_bp_above_twenty_percent_is_level_3(self):
        # 收缩压：140 * 1.25 -> 3 级
        self.assertEqual(
            evaluate_blood_pressure_level(sbp=175, dbp=90),
            3,
        )

    def test_bp_uses_max_level_between_systolic_and_diastolic(self):
        # 收缩压轻度异常，舒张压重度异常，应取 3 级
        level = evaluate_blood_pressure_level(
            sbp=150,  # 约 7% 偏高 -> 0 级
            dbp=120,  # 90 上限，偏高 33% -> 3 级
        )
        self.assertEqual(level, 3)


class EvaluateHeartRateLevelTests(SimpleTestCase):
    def test_hr_within_range_is_normal(self):
        self.assertEqual(evaluate_heart_rate_level(70), 0)

    def test_hr_ten_percent_deviation_is_level_1(self):
        # 上限 90，10% 为 9 -> 99
        self.assertEqual(evaluate_heart_rate_level(99), 1)

    def test_hr_between_ten_and_twenty_percent_is_level_2(self):
        # 90 * 1.15 -> 103.5
        self.assertEqual(evaluate_heart_rate_level(104), 2)

    def test_hr_above_twenty_percent_is_level_3(self):
        # 90 * 1.25 -> 112.5
        self.assertEqual(evaluate_heart_rate_level(113), 3)

    def test_hr_low_deviation_also_counts(self):
        # 下限 51，下降幅度 >20%
        self.assertEqual(evaluate_heart_rate_level(35), 3)


class EvaluateTemperatureLevelTests(SimpleTestCase):
    def test_temperature_value_based_levels(self):
        self.assertEqual(evaluate_temperature_level(37.5), 0)
        self.assertEqual(evaluate_temperature_level(38.1), 1)
        self.assertEqual(evaluate_temperature_level(38.5), 2)
        self.assertEqual(evaluate_temperature_level(39.0), 2)
        self.assertEqual(evaluate_temperature_level(39.5), 3)
        self.assertEqual(evaluate_temperature_level(35.0), 3)

    def test_temperature_time_based_flags_increase_level(self):
        # 单次略高但 <38.5，正常情况下为 1 级
        base = evaluate_temperature_level(Decimal("38.2"))
        self.assertEqual(base, 1)

        # 连续 24 小时高于 38°C：至少 2 级
        self.assertEqual(
            evaluate_temperature_level(
                Decimal("38.2"), has_24h_persistent_high=True
            ),
            2,
        )

        # 连续 48 小时高于 38°C：至少 3 级
        self.assertEqual(
            evaluate_temperature_level(
                Decimal("38.2"), has_48h_persistent_high=True
            ),
            3,
        )

    def test_temperature_none_relies_on_time_flags_only(self):
        self.assertEqual(
            evaluate_temperature_level(None, has_24h_persistent_high=False), 0
        )
        self.assertEqual(
            evaluate_temperature_level(None, has_24h_persistent_high=True), 2
        )
        self.assertEqual(
            evaluate_temperature_level(None, has_48h_persistent_high=True), 3
        )
