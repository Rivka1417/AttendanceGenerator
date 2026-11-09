import pytest
from src.domain.models import AttendanceReport, TypeARow, TypeASummary
from src.domain.enums import ReportType
from src.transformation.type_a_strategy import TypeATransformationStrategy


def test_type_a_transformation_determinism_and_invariants():
    """
    Validates that Type A transformation is strictly deterministic (re-runs produce identical results)
    and enforces business invariants (e.g., no work on Shabbat, exit time validation).
    """
    initial_row = TypeARow(
        date="01/10/2026",
        day_of_week="שבת",
        location="תל אביב",
        entry_time="08:00",
        exit_time="17:00",
        total_hours=9.0,
        break_time="1:00",
        hours_100=9.0,
        hours_125=0.0,
        hours_150=0.0,
        shabbat_hours=0.0
    )

    summary = TypeASummary(
        total_days=1,
        total_monthly_hours=9.0,
        total_100=9.0,
        total_125=0.0,
        total_150=0.0,
        total_shabbat=0.0,
        bonus=0.0,
        travel_expenses=100.0
    )

    report = AttendanceReport(
        report_type=ReportType.TYPE_A,
        rows=[initial_row],
        summary=summary,
        company_name = 'חברה בדיקות בע"מ',
        employee_name = "ישראל ישראלי",
        employee_id = "123456789"
    )

    strategy = TypeATransformationStrategy()

    result_1 = strategy.transform(report, {})
    result_2 = strategy.transform(report, {})

    assert result_1.rows[0].total_hours == result_2.rows[0].total_hours
    assert result_1.summary.total_monthly_hours == result_2.summary.total_monthly_hours

    assert result_1.rows[0].entry_time is None
    assert result_1.rows[0].exit_time is None
    assert result_1.rows[0].total_hours == 0.0