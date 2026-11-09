from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models import AttendanceReport, BaseRow, BaseSummary
from src.domain.enums import ReportType


class BaseParser(ABC):
    """
    Abstract base class for parsing attendance reports.
    Implements the Template Method design pattern to enforce a unified
    parsing flow across different report types.
    """

    def __init__(self, report_type: ReportType):
        self.report_type = report_type

    def parse(self, raw_text: str) -> AttendanceReport:
        """
        The Template Method defining the exact skeleton of the parsing process.
        """
        lines = raw_text.splitlines()
        summary = self._parse_summary(lines)
        rows = []

        for line in lines:
            if not line.strip():
                continue

            if not self._is_header_line(line):
                parsed_row = self._parse_row(line)
                if parsed_row:
                    rows.append(parsed_row)

        return AttendanceReport(
            report_type=self.report_type,
            rows=rows,
            summary=summary
        )

    @abstractmethod
    def _parse_row(self, line: str) -> Optional[BaseRow]:
        """Parses a single text line into a domain row model."""
        pass

    @abstractmethod
    def _parse_summary(self, lines: List[str]) -> BaseSummary:
        """Locates and parses the summary values from the document lines."""
        pass

    @abstractmethod
    def _is_header_line(self, line: str) -> bool:
        """Returns True if the line is part of the table headers."""
        pass