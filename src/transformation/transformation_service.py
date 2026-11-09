from src.domain.models import AttendanceReport
from src.domain.enums import ReportType
from src.transformation.base_strategy import BaseTransformationStrategy
from src.transformation.type_a_strategy import TypeATransformationStrategy
from src.transformation.type_b_strategy import TypeBTransformationStrategy

class TransformationService:
    """
    Service class responsible for selecting and applying the appropriate
    transformation strategy based on the attendance report type.
    """

    def __init__(self):
        """
        Initializes the service and registers available report strategies in a dictionary.
        """
        self._strategies = {
            ReportType.TYPE_A: TypeATransformationStrategy(),
            ReportType.TYPE_B: TypeBTransformationStrategy()
        }

    def process(self, report: AttendanceReport, rules: dict, seed: int = None) -> AttendanceReport:
        """
        Selects the correct strategy for the given report type and executes the transformation,
        returning a brand new updated AttendanceReport object.
        """
        strategy: BaseTransformationStrategy = self._strategies.get(report.report_type)
        if not strategy:
            raise ValueError(f"Unsupported report type for transformation: {report.report_type}")

        return strategy.transform(report, rules, seed=seed)