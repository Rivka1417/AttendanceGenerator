import pytest
from pathlib import Path
from src.parsing.ocr import extract_text_from_pdf

def test_ocr_extraction():
    """Validates that the OCR successfully extracts text from a sample PDF file."""
    base_dir = Path(__file__).resolve().parent.parent
    pdf_file_path = base_dir / "input" / "n_r_10_n.pdf"

    if pdf_file_path.exists():
        text_result = extract_text_from_pdf(str(pdf_file_path))
        assert isinstance(text_result, str)
        assert len(text_result) > 0
    else:
        pytest.skip(f"Test file not found: {pdf_file_path}")