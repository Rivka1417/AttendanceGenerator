import random
from datetime import datetime, timedelta
from typing import Optional

from src.config.settings import (
    RANDOMIZE_ROW_PROBABILITY,
    ENTRY_TIME_MIN,
    ENTRY_TIME_MAX,
    WORK_HOURS_MIN,
    WORK_HOURS_MAX,
    MAX_DAILY_HOURS,
)

from src.domain.models import (
    AttendanceReport,
    TypeBRow,
    TypeBSummary,
)

from src.transformation.base_strategy import BaseTransformationStrategy


class TypeBTransformationStrategy(BaseTransformationStrategy):

    def _parse_time(self, value: Optional[str]):
        if not value:
            return None

        try:
            return datetime.strptime(value.strip(), "%H:%M")
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _format_time(value: datetime) -> str:
        return value.strftime("%H:%M")

    def _random_entry(self, rng: random.Random) -> datetime:
        start = datetime.strptime(ENTRY_TIME_MIN, "%H:%M")
        end = datetime.strptime(ENTRY_TIME_MAX, "%H:%M")

        span = int((end - start).total_seconds() // 60)

        return start + timedelta(
            minutes=rng.randint(0, max(0, span))
        )

    def _random_duration(self, rng: random.Random) -> int:
        low = max(1, int(round(WORK_HOURS_MIN * 60)))
        high = max(low, int(round(WORK_HOURS_MAX * 60)))

        return rng.randint(low, high)

    def _fill_missing_times(
        self,
        entry: Optional[str],
        exit_time: Optional[str],
        rng: random.Random,
    ):
        entry_dt = self._parse_time(entry)
        exit_dt = self._parse_time(exit_time)

        if entry_dt is None and exit_dt is None:
            entry_dt = self._random_entry(rng)
            exit_dt = entry_dt + timedelta(
                minutes=self._random_duration(rng)
            )

        elif entry_dt is None:
            entry_dt = exit_dt - timedelta(
                minutes=self._random_duration(rng)
            )

        elif exit_dt is None:
            exit_dt = entry_dt + timedelta(
                minutes=self._random_duration(rng)
            )

        return (
            self._format_time(entry_dt),
            self._format_time(exit_dt),
        )

    def _calculate_hours(
        self,
        entry: str,
        exit_time: str,
    ) -> float:
        entry_dt = self._parse_time(entry)
        exit_dt = self._parse_time(exit_time)

        if entry_dt is None or exit_dt is None:
            return 0.0

        if exit_dt <= entry_dt:
            exit_dt += timedelta(days=1)

        minutes = (exit_dt - entry_dt).total_seconds() / 60

        return round(
            min(minutes / 60, MAX_DAILY_HOURS),
            2,
        )

    @staticmethod
    def _is_shabbat(row: TypeBRow) -> bool:
        if (row.day_of_week or "").strip() in ("שבת", "יום שבת"):
            return True

        if row.date:
            for fmt in (
                "%d/%m/%Y", "%d/%m/%y",
                "%d.%m.%Y", "%d.%m.%y",
            ):
                try:
                    return (
                        datetime.strptime(
                            row.date.strip(), fmt
                        ).weekday() == 5
                    )
                except ValueError:
                    continue

        return False

    def transform(
        self,
        report: AttendanceReport,
        rules: dict,
        seed: int = None,
    ) -> AttendanceReport:

        rng = random.Random(seed)
        rules = rules or {}

        probability = float(
            rules.get(
                "randomize_row_probability",
                RANDOMIZE_ROW_PROBABILITY,
            )
        )

        probability = min(1.0, max(0.0, probability))

        transformed_rows = []
        total_monthly_hours = 0.0
        total_days = 0

        for row in report.rows:

            if not isinstance(row, TypeBRow):
                continue

            if self._is_shabbat(row):
                continue

            # שלב ראשון: השלמת שעות חסרות.
            new_entry, new_exit = self._fill_missing_times(
                row.entry_time,
                row.exit_time,
                rng,
            )

            # שלב שני: שינוי קטן רק באחוז השורות שהוגדר.
            if rng.random() < probability:
                shift_minutes = rng.randint(-10, 10)

                entry_dt = self._parse_time(new_entry)
                exit_dt = self._parse_time(new_exit)

                if entry_dt and exit_dt:
                    new_entry = self._format_time(
                        entry_dt + timedelta(minutes=shift_minutes)
                    )

                    new_exit = self._format_time(
                        exit_dt + timedelta(minutes=shift_minutes)
                    )

            new_total_hours = self._calculate_hours(
                new_entry,
                new_exit,
            )

            total_monthly_hours += new_total_hours

            if new_total_hours > 0:
                total_days += 1

            transformed_rows.append(
                TypeBRow(
                    date=row.date,
                    day_of_week=row.day_of_week,
                    entry_time=new_entry,
                    exit_time=new_exit,
                    total_hours=new_total_hours,
                    notes=row.notes,
                )
            )

        old_summary = report.summary

        hourly_rate = float(
            old_summary.hourly_rate or 0.0
        )

        rounded_hours = round(total_monthly_hours, 2)

        # חישוב מחדש של התשלום לפי השעות המעודכנות.
        total_payment = round(
            hourly_rate * rounded_hours,
            2,
        )

        new_summary = TypeBSummary(
            employee_name=old_summary.employee_name,
            total_days=total_days,
            total_monthly_hours=rounded_hours,
            hourly_rate=hourly_rate,
            total_payment=total_payment,
        )

        return AttendanceReport(
            report_type=report.report_type,
            rows=transformed_rows,
            summary=new_summary,
            company_name=report.company_name,
            employee_name=report.employee_name,
            employee_id=report.employee_id,
        )