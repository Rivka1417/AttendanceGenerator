from pydantic import BaseModel, Field
from typing import List, Optional, Union
from .enums import ReportType

class BaseRow(BaseModel):
    """
    Base model for a single attendance row, containing fields common to all report types.
    """
    date: str = Field(...)
    day_of_week: str = Field(...)
    entry_time: Optional[str] = Field(default=None)
    exit_time: Optional[str] = Field(default=None)
    total_hours: float = Field(default=0.0)


class TypeARow(BaseRow):
    """
    Row model specific to Type A reports, inheriting from BaseRow.
    """
    location: Optional[str] = Field(default=None)
    break_time: Optional[str] = Field(default=None)
    hours_100: float = Field(default=0.0)
    hours_125: float = Field(default=0.0)
    hours_150: float = Field(default=0.0)
    shabbat_hours: float = Field(default=0.0)


class TypeBRow(BaseRow):
    """
    Row model specific to Type B reports, inheriting from BaseRow.
    """
    notes: Optional[str] = Field(default=None)


class BaseSummary(BaseModel):
    """
    Base model for the monthly summary section.
    """
    total_days: int = Field(...)
    total_monthly_hours: float = Field(...)


class TypeASummary(BaseSummary):
    """
    Summary model specific to Type A reports.
    """
    total_100: float = Field(default=0.0)
    total_125: float = Field(default=0.0)
    total_150: float = Field(default=0.0)
    total_shabbat: float = Field(default=0.0)
    bonus: float = Field(default=0.0)
    travel_expenses: float = Field(default=0.0)


class TypeBSummary(BaseSummary):
    """
    Summary model specific to Type B reports.
    """
    employee_name: str = Field(...)
    hourly_rate: float = Field(default=0.0)
    total_payment: float = Field(default=0.0)


class AttendanceReport(BaseModel):
    """
    The complete attendance report, containing the type, rows, summary, and metadata.
    """
    report_type: ReportType = Field(...)
    rows: List[Union[TypeARow, TypeBRow]] = Field(...)
    summary: Union[TypeASummary, TypeBSummary] = Field(...)
    company_name: Optional[str] = Field(default="")
    employee_name: Optional[str] = Field(default="")
    employee_id: Optional[str] = Field(default="")