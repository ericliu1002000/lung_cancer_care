from __future__ import annotations

import logging
from datetime import date, timedelta

try:
    import chinese_calendar
except ImportError:  # pragma: no cover - 依赖缺失时的兜底
    chinese_calendar = None


logger = logging.getLogger(__name__)


class ChinaCalendarService:
    """中国节假日/周末判定服务。"""

    _MISSING_DEPENDENCY_WARNED = False
    _UNSUPPORTED_YEARS_WARNED: set[int] = set()
    _WEEKEND_NAME_MAP = {
        5: "周六",
        6: "周日",
    }
    _HOLIDAY_NAME_MAP = {
        "New Year's Day": "元旦",
        "Spring Festival": "春节",
        "Tomb-sweeping Day": "清明节",
        "Labour Day": "劳动节",
        "Dragon Boat Festival": "端午节",
        "National Day": "国庆节",
        "Mid-autumn Festival": "中秋节",
        "Anti-Fascist 70th Day": "中国人民抗日战争暨世界反法西斯战争胜利70周年纪念日",
    }

    @classmethod
    def get_day_meta(cls, target_date: date) -> dict:
        weekday = target_date.weekday()
        is_weekend = weekday >= 5
        weekend_name = cls._WEEKEND_NAME_MAP.get(weekday, "")
        is_statutory_holiday = False
        holiday_name = ""

        if chinese_calendar is None:
            cls._warn_missing_dependency_once()
        else:
            try:
                is_holiday, holiday_name_raw = chinese_calendar.get_holiday_detail(target_date)
            except NotImplementedError as exc:
                cls._warn_unsupported_year_once(target_date.year, exc)
            except Exception as exc:  # pragma: no cover - 防守日志
                logger.warning("节假日查询失败，按仅周末规则降级：date=%s err=%s", target_date, exc)
            else:
                holiday_name = cls._translate_holiday_name(holiday_name_raw)
                is_statutory_holiday = bool(is_holiday and holiday_name)

        reason_parts: list[str] = []
        if weekend_name:
            reason_parts.append(weekend_name)
        if is_statutory_holiday and holiday_name:
            reason_parts.append(holiday_name)

        return {
            "date": target_date,
            "date_display_md": f"{target_date.month}-{target_date.day}",
            "date_display_mmdd": target_date.strftime("%m/%d"),
            "date_display_full": f"{target_date.year}-{target_date.month}-{target_date.day}",
            "weekday": weekday,
            "is_weekend": is_weekend,
            "weekend_name": weekend_name,
            "is_statutory_holiday": is_statutory_holiday,
            "holiday_name": holiday_name,
            "should_highlight": is_weekend or is_statutory_holiday,
            "highlight_reason": " / ".join(reason_parts),
        }

    @classmethod
    def build_cycle_header_meta(cls, start_date: date, cycle_days: int) -> dict:
        try:
            cycle_days_int = int(cycle_days)
        except (TypeError, ValueError):
            cycle_days_int = 0

        if cycle_days_int <= 0:
            return {"header_days": [], "header_week_ranges": []}

        header_days: list[dict] = []
        for offset in range(cycle_days_int):
            target_date = start_date + timedelta(days=offset)
            day_meta = cls.get_day_meta(target_date)
            day_meta["day_index"] = offset + 1
            header_days.append(day_meta)

        header_week_ranges: list[dict] = []
        for start_idx in range(0, len(header_days), 7):
            week_days = header_days[start_idx : start_idx + 7]
            if not week_days:
                continue
            first_day = week_days[0]
            last_day = week_days[-1]
            header_week_ranges.append(
                {
                    "start_day": first_day["day_index"],
                    "end_day": last_day["day_index"],
                    "span": len(week_days),
                    "start_offset": first_day["day_index"] - 1,
                    "end_offset": last_day["day_index"] - 1,
                    "start_date_display": first_day["date_display_md"],
                    "end_date_display": last_day["date_display_md"],
                    "title": f"{first_day['date_display_full']} 至 {last_day['date_display_full']}",
                }
            )

        return {
            "header_days": header_days,
            "header_week_ranges": header_week_ranges,
        }

    @classmethod
    def _translate_holiday_name(cls, holiday_name: str | None) -> str:
        if not holiday_name:
            return ""
        return cls._HOLIDAY_NAME_MAP.get(holiday_name, holiday_name)

    @classmethod
    def _warn_missing_dependency_once(cls) -> None:
        if cls._MISSING_DEPENDENCY_WARNED:
            return
        logger.warning("未安装 chinesecalendar，疗程表头节假日判断降级为仅标记周末。")
        cls._MISSING_DEPENDENCY_WARNED = True

    @classmethod
    def _warn_unsupported_year_once(cls, year: int, exc: Exception) -> None:
        if year in cls._UNSUPPORTED_YEARS_WARNED:
            return
        logger.warning("节假日库不支持年份 %s，疗程表头节假日判断降级为仅标记周末：%s", year, exc)
        cls._UNSUPPORTED_YEARS_WARNED.add(year)
