import re
from datetime import datetime
from typing import List, Optional
import random
from src.domain.enums import ReportType
from src.domain.models import TypeBRow, TypeBSummary, AttendanceReport
from src.parsing.parser import BaseParser

from src.config.settings import (
    DEFAULT_HOURLY_RATE,
    MIN_HOURLY_RATE,
    MAX_HOURLY_RATE
)

class TypeBParser(BaseParser):

    DAYS = (
        "ראשון", "שני", "שלישי", "רביעי",
        "חמישי", "שישי", "שבת",
    )

    DATE_RE = re.compile(
        r"(?<!\d)(\d{1,2}[./]\d{1,2}[./]\d{2,4})(?!\d)"
    )

    TIME_RE = re.compile(
        r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)"
    )

    def __init__(self):
        super().__init__(ReportType.TYPE_B)

    @staticmethod
    def _normalize_number(value: str) -> Optional[float]:
        value = value.strip().replace(" ", "")

        if "," in value and "." not in value:
            value = value.replace(",", ".")
        elif "," in value and "." in value:
            value = value.replace(",", "")

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_date(value: str):
        value = value.replace(".", "/")

        for fmt in ("%d/%m/%Y", "%d/%m/%y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                pass

        return None

    def _is_header_line(self, line: str) -> bool:
        if self.DATE_RE.search(line):
            return False

        keywords = (
            "שם עובד", "שם העובד", "ימי עבודה",
            "שעות חודשיות", "מחיר לשעה",
            "תעריף לשעה", "לתשלום", "כרטיס עובד",
            "הערות",
        )

        return any(word in line for word in keywords)

    def _parse_row(self, line: str) -> Optional[TypeBRow]:
        date_match = self.DATE_RE.search(line)

        if not date_match:
            return None

        date_str = date_match.group(1)

        day_of_week = ""

        for day in self.DAYS:
            if re.search(rf"(?<!\w){re.escape(day)}(?!\w)", line):
                day_of_week = day
                break

        if not day_of_week:
            parsed_date = self._parse_date(date_str)

            if parsed_date:
                day_of_week = self.DAYS[
                    (parsed_date.weekday() + 1) % 7
                ]

        times = self.TIME_RE.findall(line)

        entry_time = times[0] if times else None
        exit_time = times[1] if len(times) > 1 else None

        remainder = (
            line[:date_match.start()]
            + " "
            + line[date_match.end():]
        )

        for time_value in times:
            remainder = remainder.replace(time_value, " ", 1)

        for day in self.DAYS:
            remainder = re.sub(
                rf"(?<!\w){re.escape(day)}(?!\w)",
                " ",
                remainder,
            )

        remainder = re.sub(
            r"(?<!\d)(?:100|125|150)\s*%",
            " ",
            remainder,
        )

        decimals = re.findall(
            r"(?<![\d.])\d+[.,]\d{1,3}(?!\d)",
            remainder,
        )

        values = [
            self._normalize_number(value)
            for value in decimals
        ]
        values = [v for v in values if v is not None]

        total_hours = values[0] if values else 0.0

        notes_text = re.sub(
            r"\d+(?:[.,]\d+)?",
            " ",
            remainder,
        )
        notes_text = re.sub(
            r"[|₪%\[\]:=]",
            " ",
            notes_text,
        )
        notes_text = re.sub(
            r"(?:כניסה|יציאה|תאריך|הערות|שעות|סה[\"״]?כ)",
            " ",
            notes_text,
        )
        notes_text = re.sub(r"\s+", " ", notes_text).strip()

        tokens = [
            token for token in notes_text.split()
            if len(re.sub(r"[^א-תA-Za-z]", "", token)) >= 2
        ]

        notes = " ".join(tokens) if tokens else None

        return TypeBRow(
            date=date_str,
            day_of_week=day_of_week,
            entry_time=entry_time,
            exit_time=exit_time,
            total_hours=total_hours,
            notes=notes,
        )

    @staticmethod
    def _row_quality(row: TypeBRow) -> int:
        return (
            int(bool(row.entry_time))
            + int(bool(row.exit_time))
            + int(row.total_hours > 0)
            + int(bool(row.notes))
        )

    def parse(self, raw_text: str):
        lines = raw_text.splitlines()
        summary = self._parse_summary(lines)

        rows_by_date = {}

        for line in lines:
            if not line.strip() or self._is_header_line(line):
                continue

            row = self._parse_row(line)

            if row is None:
                continue

            parsed_date = self._parse_date(row.date)

            key = (
                parsed_date.strftime("%Y-%m-%d")
                if parsed_date
                else row.date.replace(".", "/")
            )

            existing = rows_by_date.get(key)

            if existing is None:
                rows_by_date[key] = row

            elif self._row_quality(row) > self._row_quality(existing):
                rows_by_date[key] = row

            else:
                rows_by_date[key] = TypeBRow(
                    date=existing.date,
                    day_of_week=existing.day_of_week or row.day_of_week,
                    entry_time=existing.entry_time or row.entry_time,
                    exit_time=existing.exit_time or row.exit_time,
                    total_hours=max(
                        existing.total_hours,
                        row.total_hours,
                    ),
                    notes=existing.notes or row.notes,
                )

        rows = sorted(
            rows_by_date.values(),
            key=lambda row: self._parse_date(row.date) or datetime.max,
        )

        return AttendanceReport(
            report_type=self.report_type,
            rows=rows,
            summary=summary,
        )

    def _parse_summary(self, lines: List[str]) -> TypeBSummary:
        full_text = "\n".join(
            " ".join(line.split())
            for line in lines
            if line.strip()
        )

        def extract_labeled_value(labels: tuple) -> float:

            for idx, line in enumerate(lines):
                for label in labels:
                    if label not in line:
                        continue

                    numbers = re.findall(r"(?<![\d])\d+(?:[.,]\d+)*", line)
                    for number in numbers:
                        value = self._normalize_number(number)
                        if value is not None:
                            return value

                    for offset in (-1, 1, -2, 2, -3, 3):
                        n_idx = idx + offset
                        if 0 <= n_idx < len(lines):
                            adj_line = lines[n_idx]

                            if any(k in adj_line for k in ("ימים", "שעות", "לתשלום", "מחיר", "תעריף")):
                                continue

                            adj_numbers = re.findall(r"(?<![\d])\d+(?:[.,]\d+)*", adj_line)
                            for number in adj_numbers:
                                value = self._normalize_number(number)
                                if value is not None:
                                    return value

            for label in labels:
                escaped = re.escape(label)
                patterns = (
                    rf"{escaped}\s*[:|=\-]?\s*(?:₪\s*)?([\d]+(?:[.,]\d+)*)",
                    rf"₪\s*([\d]+(?:[.,]\d+)*)\s*{escaped}",
                    rf"([\d]+(?:[.,]\d+)*)\s*₪?\s*{escaped}",
                    rf"{escaped}[^\d]{{0,80}}?([\d]+(?:[.,]\d+)*)",
                    rf"([\d]+(?:[.,]\d+)*)[^\d]{{0,80}}?{escaped}",
                )
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        value = self._normalize_number(match.group(1))
                        if value is not None:
                            return value

            return 0.0

        employee_name = ""

        total_days = int(extract_labeled_value((
            "ימי עבודה", "סה\"כ ימים", "סה״כ ימים",
        )))

        total_monthly_hours = extract_labeled_value((
            "שעות חודשיות", "סה\"כ שעות",
            "סה״כ שעות", "סהכ שעות",
        ))

        def extract_hourly_rate():
            for line in lines:
                normalized_line = re.sub(r"\s+", "", line)

                if not any(
                        label in normalized_line
                        for label in ("מחירלשעה", "תעריףלשעה")
                ):
                    continue

                currency_values = re.findall(
                    r"(\d[\d,]*(?:[.,]\d{1,2})?)\s*₪",
                    line,
                )

                if currency_values:
                    value = self._normalize_number(currency_values[-1])
                    if value is not None:
                        return value

                decimal_values = re.findall(
                    r"\d+[.,]\d{1,2}",
                    line,
                )

                if decimal_values:
                    value = self._normalize_number(decimal_values[-1])
                    if value is not None:
                        return value

            return 0.0

        hourly_rate = extract_hourly_rate()


        if not hourly_rate or hourly_rate <= 0:
            hourly_rate = hourly_rate = round(random.uniform(MIN_HOURLY_RATE, MAX_HOURLY_RATE), 2)

        total_payment = extract_labeled_value((
            "סה\"כ לתשלום", "סה״כ לתשלום", "סהכ לתשלום",
        ))

        return TypeBSummary(
            employee_name=employee_name,
            total_days=total_days,
            total_monthly_hours=total_monthly_hours,
            hourly_rate=hourly_rate,
            total_payment=total_payment,
        )