import re
from typing import List, Optional, Tuple

from src.domain.enums import ReportType
from src.domain.models import AttendanceReport, TypeARow, TypeASummary
from src.parsing.parser import BaseParser


class TypeAParser(BaseParser):
    """Parse Type A attendance reports."""

    DAYS = (
        "ראשון",
        "שני",
        "שלישי",
        "רביעי",
        "חמישי",
        "שישי",
        "שבת",
    )

    def __init__(self):
        super().__init__(ReportType.TYPE_A)
        self.company_name = ""
        self.employee_name = ""
        self.employee_id = ""

    def parse(self, raw_text: str) -> AttendanceReport:
        lines = [
            line.strip()
            for line in raw_text.splitlines()
            if line.strip()
        ]

        self.company_name = self._parse_company_name(lines)
        self.employee_name, self.employee_id = (
            self._parse_employee_info(lines)
        )

        report = super().parse(raw_text)
        report.company_name = self.company_name
        report.employee_name = self.employee_name
        report.employee_id = self.employee_id

        return report

    def _parse_company_name(self, lines: List[str]) -> str:
        for line in lines[:15]:
            if 'בע"מ' in line or 'בע״מ' in line:
                return line.strip()

        return ""

    def _parse_employee_info(
        self,
        lines: List[str],
    ) -> Tuple[str, str]:
        for line in lines:
            match = re.search(r"(?<!\d)\d{9}(?!\d)", line)

            if not match:
                continue

            employee_id = match.group()
            employee_name = line.replace(employee_id, "")
            employee_name = re.sub(
                r"[^\w\sא-ת-]",
                " ",
                employee_name,
            )
            employee_name = " ".join(employee_name.split())

            return employee_name, employee_id

        return "", ""

    @staticmethod
    def _normalize_number(value: str) -> Optional[float]:
        value = value.strip().replace(",", ".")

        try:
            return float(value)
        except ValueError:
            return None

    def _is_header_line(self, line: str) -> bool:
        normalized = " ".join(line.split())

        header_words = (
            "תאריך",
            "כניסה",
            "יציאה",
            "הפסקה",
            'סה"כ שעות',
            'סה״כ שעות',
            "שעות 100%",
            "שעות 125%",
            "שעות 150%",
            "נסיעות",
            "בונוס",
        )

        summary_words = (
            'לתשלום סה"כ',
            'סה"כ לתשלום',
            'סהכ לתשלום',
            'סך הכל',
            'ימיי עבודה',
            'ימי עבודה',
            'סה"כ ימים',
            'סה"כ שעות',
            'סהכ שעות',
        )

        return any(
            word in normalized
            for word in header_words + summary_words
        )

    def _find_date(self, line: str) -> Optional[str]:
        """
        Find a valid full date when OCR recognizes one.
        If only the day number appears before the first time,
        preserve that day number without inventing a month or year.
        """

        full_dates = re.finditer(
            r"(?<!\d)"
            r"(\d{1,2})([./])(\d{1,2})"
            r"(?:(?:[./])(\d{2,4}))?"
            r"(?!\d)",
            line,
        )

        for match in full_dates:
            day = int(match.group(1))
            separator = match.group(2)
            month_text = match.group(3)
            month = int(month_text)
            year = match.group(4)

            # Reject invalid day or month values.
            if not (1 <= day <= 31 and 1 <= month <= 12):
                continue

            # Without a year, a dot-separated date must have
            # a two-digit month to avoid matching decimal hours
            # such as 7.5 or 7.50.
            if not year and separator == "." and len(month_text) == 1:
                continue

            return match.group(0)

        first_time = re.search(
            r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)",
            line,
        )

        if not first_time:
            return None

        # In the OCR row layout, the day number appears before
        # the entry time. Only accept a leading day number here.
        prefix = line[:first_time.start()].strip()
        leading_day = re.match(r"^(\d{1,2})(?![\d./])", prefix)

        if leading_day:
            day_number = int(leading_day.group(1))
            if 1 <= day_number <= 31:
                return leading_day.group(1)

        return None

    def _parse_row(self, line: str) -> Optional[TypeARow]:
        date = self._find_date(line)

        if not date:
            return None

        times = re.findall(
            r"(?<!\d)(?:[01]?\d|2[0-3]):[0-5]\d(?!\d)",
            line,
        )

        if len(times) < 2:
            return None

        day_of_week = ""

        for day in self.DAYS:
            if re.search(
                rf"(?<!\w){re.escape(day)}(?!\w)",
                line,
            ):
                day_of_week = (
                    "שבת" if day == "שבת" else f"יום {day}"
                )
                break

        numeric_text = line.replace(date, " ", 1)

        for time_value in times:
            numeric_text = numeric_text.replace(
                time_value,
                " ",
                1,
            )

        numeric_text = re.sub(
            r"(?<!\d)(?:100|125|150)\s*%",
            " ",
            numeric_text,
        )

        decimal_matches = re.findall(
            r"(?<![\d.])\d+[.,]\d{1,3}(?!\d)",
            numeric_text,
        )

        values = [
            self._normalize_number(value)
            for value in decimal_matches
        ]
        values = [
            value for value in values
            if value is not None
        ]

        # Do not discard a row merely because OCR missed one or
        # more of its numeric columns. Keep the values that were
        # recognized and use zero for missing numeric fields.
        values = (values + [0.0] * 5)[:5]

        (
            total_hours,
            hours_100,
            hours_125,
            hours_150,
            shabbat_hours,
        ) = values

        location_text = line.replace(date, " ", 1)

        for time_value in times:
            location_text = location_text.replace(
                time_value,
                " ",
                1,
            )

        location_text = re.sub(
            r"\d+(?:[.,]\d+)?",
            " ",
            location_text,
        )
        location_text = re.sub(
            r"[₪\[\]/|%]",
            " ",
            location_text,
        )

        for day in self.DAYS:
            location_text = re.sub(
                rf"(?<!\w)(?:יום\s*)?{re.escape(day)}(?!\w)",
                " ",
                location_text,
            )

        ignored_words = {
            "תאריך",
            "כניסה",
            "יציאה",
            "הפסקה",
            "סהכ",
            "שעות",
            "יום",
        }

        location_words = re.findall(
            r"[א-ת]{2,}",
            location_text,
        )

        location = next(
            (
                word for word in location_words
                if word not in ignored_words
            ),
            "",
        )

        return TypeARow(
            date=date,
            day_of_week=day_of_week,
            location=location,
            entry_time=times[0],
            exit_time=times[1],
            break_time=times[2] if len(times) >= 3 else None,
            total_hours=total_hours,
            hours_100=hours_100,
            hours_125=hours_125,
            hours_150=hours_150,
            shabbat_hours=shabbat_hours,
        )

    def _parse_summary(self, lines: List[str]) -> TypeASummary:
        full_text = "\n".join(lines)

        def extract_value(label_pattern: str) -> float:
            patterns = (
                rf"(?:{label_pattern})\s*[:\-]?\s*"
                rf"([\d]+(?:[.,]\d+)?)",
                rf"([\d]+(?:[.,]\d+)?)\s*"
                rf"(?:₪\s*)?(?:{label_pattern})",
            )

            for pattern in patterns:
                match = re.search(
                    pattern,
                    full_text,
                    flags=re.IGNORECASE,
                )

                if match:
                    raw_value = match.group(1)

                    if raw_value is None:
                        continue

                    value = self._normalize_number(raw_value)

                    if value is not None:
                        return value

            return 0.0

        total_days = int(
            extract_value(r"(?:סה[\"״]?כ\s*)?ימים?")
        )

        total_monthly_hours = extract_value(
            r"סה[\"״]?כ\s*שעות"
        )

        total_100 = extract_value(
            r"שעות\s*100\s*%|100\s*%"
        )

        total_125 = extract_value(
            r"שעות\s*125\s*%|125\s*%"
        )

        total_150 = extract_value(
            r"שעות\s*150\s*%|150\s*%"
        )

        total_shabbat = extract_value(r"שבת")
        bonus = extract_value(r"בונוס")
        travel_expenses = extract_value(r"נסיעות")

        return TypeASummary(
            total_days=total_days,
            total_monthly_hours=total_monthly_hours,
            total_100=total_100,
            total_125=total_125,
            total_150=total_150,
            total_shabbat=total_shabbat,
            bonus=bonus,
            travel_expenses=travel_expenses,
        )