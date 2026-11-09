import pytest
from pathlib import Path
from src.parsing.ocr import extract_text_from_pdf
from src.parsing.classifier import classify_report
from src.domain.enums import ReportType

@pytest.mark.parametrize("filename, expected_type", [
    ("a_r_9.pdf", ReportType.TYPE_A),
    ("a_r_25.pdf", ReportType.TYPE_A),
    ("n_r_5_n.pdf", ReportType.TYPE_B),
    ("n_r_10_n.pdf", ReportType.TYPE_B),
])
def test_report_classification(filename, expected_type):
    """
    Validates classification with dynamically resolved absolute paths.
    """
    base_dir = Path(__file__).resolve().parent.parent / "input"
    file_path = base_dir / filename

    if file_path.exists():
        raw_text = extract_text_from_pdf(str(file_path))
        report_type = classify_report(raw_text)
        assert report_type == expected_type
    else:
        pytest.skip(f"Test file not found: {file_path}")