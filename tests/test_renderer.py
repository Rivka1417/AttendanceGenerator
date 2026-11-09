import pytest
from pathlib import Path
from src.domain.models import AttendanceReport, TypeBRow, TypeBSummary
from src.domain.enums import ReportType
from src.generation.html_renderer import HtmlRenderer
from src.generation.pdf_renderer import PdfRenderer


def test_html_renderer_output_naming_and_creation(tmp_path):
    """
    Validates that the HTML renderer creates a new file with the expected '-new' suffix
    in the designated output directory without altering the source reference.
    """
    row = TypeBRow(
        date="02/10/2026",
        day_of_week="ראשון",
        entry_time="09:00",
        exit_time="17:00",
        total_hours=8.0,
        notes="תקין"
    )

    summary = TypeBSummary(
        employee_name="שרה כהן",
        total_days=1,
        total_monthly_hours=8.0,
        hourly_rate=50.0,
        total_payment=400.0
    )

    report = AttendanceReport(
        report_type=ReportType.TYPE_B,
        rows=[row],
        summary=summary,
        company_name="חברת טכנולוגיות",
        employee_name="שרה כהן",
        employee_id="987654321"
    )


    renderer = HtmlRenderer(output_dir=str(tmp_path))
    original_filename = "report_b.pdf"

    output_file = renderer.render(report, original_filename)


    assert output_file.name == "report_b-new.html"
    assert output_file.exists()

    content = output_file.read_text(encoding="utf-8")
    assert "שרה כהן" in content
    assert "400.0" in content


def test_pdf_renderer_output_naming_and_creation(tmp_path):
    """
    Validates that the PDF renderer creates a new file with the expected '-new' suffix
    in the designated output directory using ReportLab.
    """
    row = TypeBRow(
        date="02/10/2026",
        day_of_week="ראשון",
        entry_time="09:00",
        exit_time="17:00",
        total_hours=8.0,
        notes="תקין"
    )

    summary = TypeBSummary(
        employee_name="שרה כהן",
        total_days=1,
        total_monthly_hours=8.0,
        hourly_rate=50.0,
        total_payment=400.0
    )

    report = AttendanceReport(
        report_type=ReportType.TYPE_B,
        rows=[row],
        summary=summary,
        company_name="חברת טכנולוגיות",
        employee_name="שרה כהן",
        employee_id="987654321"
    )

    renderer = PdfRenderer(output_dir=str(tmp_path))
    original_filename = "report_b.pdf"

    output_file = renderer.render(report, original_filename)

    assert output_file.name == "report_b-new.pdf"
    assert output_file.exists()