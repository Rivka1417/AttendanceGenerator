from abc import ABC, abstractmethod
from src.domain.models import AttendanceReport

class BaseTransformationStrategy(ABC):
    """
    Abstract base class defining the interface for report transformation strategies.
    Ensures a consistent contract for applying deterministic rules across different report types.
    """

    @abstractmethod
    def transform(self, report: AttendanceReport, rules: dict, seed: int = None) -> AttendanceReport:
        """
        Applies deterministic transformation rules and invariants to an attendance report,
        returning a new AttendanceReport instance without modifying the original.
        """
        pass