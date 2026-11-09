
from pathlib import Path
from typing import Tuple, List
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.domain.models import AttendanceReport
from src.domain.enums import ReportType
from src.generation.base_renderer import BaseRenderer


def _rtl_text(text: str) -> str:
    """Return text reordered for right-to-left display."""
    return get_display(str(text))


def _rtl_paragraph_text(text: str) -> str:
    """Reorder paragraph text while preserving supported bold markup."""
    if text.startswith("<b>") and text.endswith("</b>"):
        content = text[3:-4]
        return f"<b>{get_display(content)}</b>"

    return get_display(text)

class PdfRenderer(BaseRenderer):
    """
    Concrete renderer implementation for generating PDF attendance reports.
    """

    def __init__(self, output_dir: str = "output"):
        super().__init__(output_dir)

        self._formatters = {
            ReportType.TYPE_A: self._format_type_a,
            ReportType.TYPE_B: self._format_type_b,
        }

        font_path = Path("assets/fonts/arial.ttf")

        if not font_path.exists():
            raise FileNotFoundError(
                f"Required font file was not found: {font_path}"
            )

        if "ArialHebrew" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(
                TTFont("ArialHebrew", str(font_path))
            )

        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            name="HebrewTitle",
            parent=self.styles["Heading1"],
            fontName="ArialHebrew",
            fontSize=18,
            leading=22,
            alignment=1,
            textColor=colors.HexColor("#2c3e50"),
        )

        self.subtitle_style = ParagraphStyle(
            name="HebrewSubtitle",
            parent=self.styles["Normal"],
            fontName="ArialHebrew",
            fontSize=12,
            leading=16,
            alignment=1,
            textColor=colors.HexColor("#34495e"),
        )

        self.summary_style = ParagraphStyle(
            name="SummaryStyle",
            parent=self.styles["Normal"],
            fontName="ArialHebrew",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#2c3e50"),
        )

    def render(self, report: AttendanceReport, original_filename: str) -> Path:
        output_path = self._get_output_filename(original_filename, "pdf")
        formatter = self._formatters.get(report.report_type)

        if not formatter:
            raise ValueError(
                f"PDF format not supported for {report.report_type}"
            )

        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30,
        )

        elements = []

        elements.append(
            Paragraph(
                _rtl_text('דו"ח נוכחות מבוקר ומעודכן'),
                self.title_style,
            )
        )
        elements.append(Spacer(1, 10))

        elements.append(
            Paragraph(
                _rtl_text(
                    f"חברה: {report.company_name} | "
                    f"עובד: {report.employee_name} "
                    f"(ת.ז: {report.employee_id})"
                ),
                self.subtitle_style,
            )
        )
        elements.append(Spacer(1, 20))

        table_data, summary_texts = formatter(report)

        table_data = [
            [_rtl_text(cell) for cell in row]
            for row in table_data
        ]
        table_data = [list(reversed(row)) for row in table_data]

        summary_texts = [
            _rtl_paragraph_text(line)
            for line in summary_texts
        ]

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f3640")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "ArialHebrew"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcdde1")),
                    ("FONTNAME", (0, 1), (-1, -1), "ArialHebrew"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )

        elements.append(table)
        elements.append(Spacer(1, 20))

        for line in summary_texts:
            elements.append(Paragraph(line, self.summary_style))

        doc.build(elements)
        return output_path

    def _format_type_a(
        self, report: AttendanceReport
    ) -> Tuple[List[List[str]], List[str]]:
        table_data = [[
            "תאריך", "יום", "מיקום", "כניסה", "יציאה",
            "סה\"כ", "הפסקה", "100%", "125%", "150%", "שבת"
        ]]

        for row in report.rows:
            table_data.append([
                str(row.date),
                str(row.day_of_week),
                str(getattr(row, "location", "-")),
                str(row.entry_time or "-"),
                str(row.exit_time or "-"),
                str(row.total_hours),
                str(row.break_time or "-"),
                str(row.hours_100),
                str(row.hours_125),
                str(row.hours_150),
                str(row.shabbat_hours),
            ])

        summary_texts = [
            "<b>סיכום נתונים חודשי:</b>",
            f"סה\"כ ימים פעילים: {report.summary.total_days}",
            f"סה\"כ שעות חודשיות: {report.summary.total_monthly_hours}",
            f"סה\"כ 100%: {report.summary.total_100} | "
            f"125%: {report.summary.total_125} | "
            f"150%: {report.summary.total_150} | "
            f"שבת: {report.summary.total_shabbat}",
            f"בונוס: {report.summary.bonus} | "
            f"החזרי נסיעות: {report.summary.travel_expenses}",
        ]

        return table_data, summary_texts

    def _format_type_b(
        self, report: AttendanceReport
    ) -> Tuple[List[List[str]], List[str]]:
        table_data = [[
            "תאריך", "יום בשבוע", "כניסה", "יציאה", "סה\"כ שעות", "הערות"
        ]]

        for row in report.rows:
            table_data.append([
                str(row.date),
                str(row.day_of_week),
                str(row.entry_time or "-"),
                str(row.exit_time or "-"),
                str(row.total_hours),
                str(getattr(row, "notes", "") or ""),
            ])

        summary_texts = [
            "<b>סיכום נתונים חודשי:</b>",
            f"סה\"כ ימים פעילים: {report.summary.total_days}",
            f"סה\"כ שעות חודשיות: {report.summary.total_monthly_hours}",
            f"מחיר לשעה: {report.summary.hourly_rate} ₪",
            f"סה\"כ לתשלום: {report.summary.total_payment} ₪",
        ]

        return table_data, summary_texts
