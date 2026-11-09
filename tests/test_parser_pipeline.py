from pathlib import Path
import pytest
from src.parsing.ocr import extract_text_from_pdf
from src.parsing.classifier import classify_report
from src.parsing.factory import get_parser


def test_full_parsing_pipeline():
    """
    Validates the complete parsing pipeline using robust absolute paths.
    """
    base_dir = Path(__file__).resolve().parent.parent / "input"

    test_files = [
        "a_r_9.pdf",
        "a_r_25.pdf",
        "n_r_5_n.pdf",
        "n_r_10_n.pdf"
    ]

    for filename in test_files:
        file_path = base_dir / filename

        if file_path.exists():
            raw_text = extract_text_from_pdf(str(file_path))
            report_type = classify_report(raw_text)
            parser = get_parser(report_type)
            report = parser.parse(raw_text)

            assert report is not None
            assert report.report_type == report_type
            assert len(report.rows) > 0
            assert report.summary is not None