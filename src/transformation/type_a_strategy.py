from datetime import datetime, timedelta
from typing import Optional
import random

from src.domain.models import AttendanceReport, TypeARow, TypeASummary
from src.transformation.base_strategy import BaseTransformationStrategy
from src.config.settings import (
    RANDOMIZE_ROW_PROBABILITY,
    ENTRY_TIME_MIN,
    ENTRY_TIME_MAX,
    WORK_HOURS_MIN,
    WORK_HOURS_MAX,
    MAX_DAILY_HOURS,
    TYPE_A_BREAK_MIN_MINUTES,
    TYPE_A_BREAK_MAX_MINUTES,
)


class TypeATransformationStrategy(BaseTransformationStrategy):
    """Apply configured, reproducible transformations to Type A reports."""

    TIME_FORMAT = "%H:%M"

    @staticmethod
    def _parse_time(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), "%H:%M")
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _format_time(value: datetime) -> str:
        return value.strftime("%H:%M")

    @staticmethod
    def _minutes_between(start: datetime, end: datetime) -> int:
        if end <= start:
            end += timedelta(days=1)
        return int((end - start).total_seconds() // 60)

    @staticmethod
    def _break_minutes(value: Optional[str]) -> int:
        """Break values in Type A are represented as HH:MM durations."""
        if not value:
            return 0
        try:
            parsed = datetime.strptime(value.strip(), "%H:%M")
            return parsed.hour * 60 + parsed.minute
        except (ValueError, AttributeError):
            return 0

    def _randomize_break(self, rng: random.Random) -> str:
        """Generate a random break duration using configured limits."""
        minutes = rng.randint(
            TYPE_A_BREAK_MIN_MINUTES,
            TYPE_A_BREAK_MAX_MINUTES,
        )

        hours, remaining_minutes = divmod(minutes, 60)
        return f"{hours:02d}:{remaining_minutes:02d}"
    @staticmethod
    def _random_minutes(rng: random.Random, low: str, high: str) -> int:
        low_dt = datetime.strptime(low, "%H:%M")
        high_dt = datetime.strptime(high, "%H:%M")
        low_min = low_dt.hour * 60 + low_dt.minute
        high_min = high_dt.hour * 60 + high_dt.minute
        if high_min < low_min:
            raise ValueError(f"Invalid time range: {low} - {high}")
        return rng.randint(low_min, high_min)

    def _random_duration(self, rng: random.Random) -> int:
        low = int(float(WORK_HOURS_MIN) * 60)
        high = int(float(WORK_HOURS_MAX) * 60)
        if high < low:
            raise ValueError("WORK_HOURS_MAX must be >= WORK_HOURS_MIN")
        return rng.randint(low, high)

    def _is_shabbat(self, row: TypeARow) -> bool:
        day = (row.day_of_week or "").strip()
        if day in ("שבת", "יום שבת"):
            return True
        if row.date:
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    return datetime.strptime(row.date.strip(), fmt).weekday() == 5
                except ValueError:
                    continue
        return False

    def _make_missing_times(
        self,
        entry: Optional[str],
        exit_time: Optional[str],
        break_minutes: int,
        rng: random.Random,
    ) -> tuple[str, str]:
        """Fill only the missing endpoint; generate both when both are absent."""
        entry_dt = self._parse_time(entry)
        exit_dt = self._parse_time(exit_time)
        duration = self._random_duration(rng)

        if entry_dt is None and exit_dt is None:
            entry_minute = self._random_minutes(rng, ENTRY_TIME_MIN, ENTRY_TIME_MAX)
            entry_dt = datetime.strptime("00:00", "%H:%M") + timedelta(minutes=entry_minute)
            exit_dt = entry_dt + timedelta(minutes=duration + break_minutes)
        elif entry_dt is None:
            entry_dt = exit_dt - timedelta(minutes=duration + break_minutes)
        elif exit_dt is None:
            exit_dt = entry_dt + timedelta(minutes=duration + break_minutes)

        return self._format_time(entry_dt), self._format_time(exit_dt)

    def _calculate_hours(
        self,
        entry: Optional[str],
        exit_str: Optional[str],
        break_str: Optional[str],
    ) -> float:
        entry_dt = self._parse_time(entry)
        exit_dt = self._parse_time(exit_str)
        if entry_dt is None or exit_dt is None:
            return 0.0

        total_minutes = self._minutes_between(entry_dt, exit_dt)
        total_minutes -= self._break_minutes(break_str)
        if total_minutes <= 0:
            return 0.0

        return round(min(total_minutes / 60.0, float(MAX_DAILY_HOURS)), 2)

    def _randomize_complete_row(
        self,
        entry: str,
        exit_time: str,
        break_minutes: int,
        rng: random.Random,
    ) -> tuple[str, str]:
        """Make a modest change to both endpoints while keeping a plausible duration."""
        entry_dt = self._parse_time(entry)
        exit_dt = self._parse_time(exit_time)
        if entry_dt is None or exit_dt is None:
            return entry, exit_time

        original_duration = self._minutes_between(entry_dt, exit_dt) - break_minutes
        if original_duration <= 0:
            return entry, exit_time

        # Small changes: shift start by up to 30 minutes and duration by up to 30 minutes.
        start_shift = rng.randint(-30, 30)
        duration_shift = rng.randint(-30, 30)
        new_entry = entry_dt + timedelta(minutes=start_shift)
        new_duration = max(60, original_duration + duration_shift)
        new_duration = min(new_duration, int(float(MAX_DAILY_HOURS) * 60))
        new_exit = new_entry + timedelta(minutes=new_duration + break_minutes)
        return self._format_time(new_entry), self._format_time(new_exit)

    @staticmethod
    def _number(value) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def transform(
        self,
        report: AttendanceReport,
        rules: dict,
        seed: int = None,
    ) -> AttendanceReport:
        rng = random.Random(seed)
        probability = float(RANDOMIZE_ROW_PROBABILITY)
        probability = max(0.0, min(1.0, probability))

        transformed_rows = []
        total_monthly_hours = total_100 = total_125 = 0.0
        total_150 = total_shabbat = 0.0
        total_days = 0

        for row in report.rows:
            if not isinstance(row, TypeARow):
                continue
            if self._is_shabbat(row):
                continue

            should_randomize = rng.random() < probability

            new_break_time = (
                self._randomize_break(rng)
                if should_randomize
                else row.break_time
            )

            break_minutes = self._break_minutes(new_break_time)
            entry_dt = self._parse_time(row.entry_time)
            exit_dt = self._parse_time(row.exit_time)

            if entry_dt is None or exit_dt is None:
                new_entry, new_exit = self._make_missing_times(
                    row.entry_time, row.exit_time, break_minutes, rng
                )
            elif should_randomize:
                new_entry, new_exit = self._randomize_complete_row(
                    row.entry_time, row.exit_time, break_minutes, rng
                )
            else:
                new_entry, new_exit = row.entry_time, row.exit_time

            new_total_hours = self._calculate_hours(
                new_entry, new_exit, new_break_time
            )
            if new_total_hours > 0:
                total_days += 1

            old_100 = self._number(row.hours_100)
            old_125 = self._number(row.hours_125)
            old_150 = self._number(row.hours_150)
            old_shabbat = self._number(row.shabbat_hours)
            old_total = self._number(row.total_hours)
            old_categories = old_100 + old_125 + old_150 + old_shabbat

            if (
                old_categories > 0
                and abs(old_categories - old_total) <= 0.15
                and new_total_hours > 0
            ):
                scale = new_total_hours / old_categories
                h100 = round(old_100 * scale, 2)
                h125 = round(old_125 * scale, 2)
                h150 = round(old_150 * scale, 2)
            else:
                h100 = round(new_total_hours, 2)
                h125 = 0.0
                h150 = 0.0
            shabbat = 0.0

            total_monthly_hours += new_total_hours
            total_100 += h100
            total_125 += h125
            total_150 += h150
            total_shabbat += shabbat

            transformed_rows.append(
                TypeARow(
                    date=row.date,
                    day_of_week=row.day_of_week,
                    location=row.location,
                    entry_time=new_entry,
                    exit_time=new_exit,
                    break_time=new_break_time,
                    total_hours=new_total_hours,
                    hours_100=h100,
                    hours_125=h125,
                    hours_150=h150,
                    shabbat_hours=shabbat,
                )
            )

        old_summary = report.summary
        new_summary = TypeASummary(
            total_days=total_days,
            total_monthly_hours=round(total_monthly_hours, 2),
            total_100=round(total_100, 2),
            total_125=round(total_125, 2),
            total_150=round(total_150, 2),
            total_shabbat=round(total_shabbat, 2),
            bonus=old_summary.bonus,
            travel_expenses=old_summary.travel_expenses,
        )

        return AttendanceReport(
            report_type=report.report_type,
            rows=transformed_rows,
            summary=new_summary,
            company_name=report.company_name,
            employee_name=report.employee_name,
            employee_id=report.employee_id,
        )
