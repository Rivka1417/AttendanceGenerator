from src.domain.enums import ReportType
from src.domain.exceptions import ParserNotFoundError
from src.parsing.parser import BaseParser
from src.parsing.type_a_parser import TypeAParser
from src.parsing.type_b_parser import TypeBParser


def get_parser(report_type: ReportType) -> BaseParser:
    parsers = {
        ReportType.TYPE_A: TypeAParser,
        ReportType.TYPE_B: TypeBParser
    }

    parser_class = parsers.get(report_type)
    if not parser_class:
        raise ParserNotFoundError(f"No parser implemented for report type: {report_type}")

    return parser_class()