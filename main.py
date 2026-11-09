
import sys
import traceback
from pathlib import Path

from src.parsing.ocr import extract_text_from_pdf
from src.parsing.classifier import classify_report
from src.parsing.factory import get_parser
from src.transformation.transformation_service import TransformationService
from src.generation.html_renderer import HtmlRenderer
from src.generation.pdf_renderer import PdfRenderer
from src.domain.exceptions import AttendanceSystemError


def process_single_pdf(
    input_pdf_path: str | Path,
    output_dir: str | Path
) -> tuple[Path, Path]:
    """
    Processes a single PDF file through the complete attendance pipeline.

    Returns:
        A tuple containing the generated PDF path and HTML path.
    """
    input_path = Path(input_pdf_path)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input PDF was not found: {input_path}"
        )

    if input_path.suffix.lower() != ".pdf":
        raise ValueError("The input file must be a PDF.")

    output_path.mkdir(parents=True, exist_ok=True)


    raw_text = extract_text_from_pdf(str(input_path))


    report_type = classify_report(raw_text)


    parser = get_parser(report_type)
    original_report = parser.parse(raw_text)


    transformation_service = TransformationService()
    transformed_report = transformation_service.process(
        original_report,
        rules={}
    )


    html_renderer = HtmlRenderer(output_dir=str(output_path))
    pdf_renderer = PdfRenderer(output_dir=str(output_path))

    html_out = html_renderer.render(
        transformed_report,
        input_path.name
    )

    pdf_out = pdf_renderer.render(
        transformed_report,
        input_path.name
    )

    return pdf_out, html_out


def process_directory(
    input_dir_name: str = "input",
    output_dir_name: str = "output"
):
    """
    Main entry point for the Attendance Generator System.
    Processes all PDF files in the input directory end-to-end.
    """
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / input_dir_name
    output_dir = base_dir / output_dir_name

    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    transformation_service = TransformationService()
    html_renderer = HtmlRenderer(output_dir=str(output_dir))
    pdf_renderer = PdfRenderer(output_dir=str(output_dir))

    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in '{input_dir}'.")
        return

    print(
        f"Found {len(pdf_files)} PDF files to process. "
        "Starting pipeline...\n"
    )

    for file_path in pdf_files:
        print(f"{'=' * 50}")
        print(f"Processing: {file_path.name}")

        try:
            print("  - Running OCR extraction...")
            raw_text = extract_text_from_pdf(str(file_path))

            print("  - Classifying report type...")
            report_type = classify_report(raw_text)
            print(f"    Detected type: {report_type.value}")

            print("  - Parsing report data...")
            parser = get_parser(report_type)
            original_report = parser.parse(raw_text)

            print(
                f"    Successfully parsed "
                f"{len(original_report.rows)} rows."
            )

            print("  - Applying transformation rules...")
            transformed_report = transformation_service.process(
                original_report,
                rules={}
            )

            print("  - Rendering HTML and PDF outputs...")

            html_out = html_renderer.render(
                transformed_report,
                file_path.name
            )

            pdf_out = pdf_renderer.render(
                transformed_report,
                file_path.name
            )

            print("  [V] Success! Outputs saved to:")
            print(f"      HTML: {html_out.name}")
            print(f"      PDF:  {pdf_out.name}")

        except AttendanceSystemError as e:
            print(
                f"  [X] Domain Error processing "
                f"{file_path.name}: {e}"
            )

        except Exception as e:
            traceback.print_exc()
            print(f"  [X] Error processing {file_path.name}: {e}")

    print(f"\n{'=' * 50}")
    print("Batch processing complete.")


if __name__ == "__main__":
    process_directory()

import sys
import traceback
from pathlib import Path

from src.parsing.ocr import extract_text_from_pdf
from src.parsing.classifier import classify_report
from src.parsing.factory import get_parser
from src.transformation.transformation_service import TransformationService
from src.generation.html_renderer import HtmlRenderer
from src.generation.pdf_renderer import PdfRenderer
from src.domain.exceptions import AttendanceSystemError


def process_single_pdf(
    input_pdf_path: str | Path,
    output_dir: str | Path
) -> tuple[Path, Path]:
    """
    Processes a single PDF file through the complete attendance pipeline.

    Returns:
        A tuple containing the generated PDF path and HTML path.
    """
    input_path = Path(input_pdf_path)
    output_path = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input PDF was not found: {input_path}"
        )

    if input_path.suffix.lower() != ".pdf":
        raise ValueError("The input file must be a PDF.")

    output_path.mkdir(parents=True, exist_ok=True)


    raw_text = extract_text_from_pdf(str(input_path))


    report_type = classify_report(raw_text)


    parser = get_parser(report_type)
    original_report = parser.parse(raw_text)


    transformation_service = TransformationService()
    transformed_report = transformation_service.process(
        original_report,
        rules={}
    )


    html_renderer = HtmlRenderer(output_dir=str(output_path))
    pdf_renderer = PdfRenderer(output_dir=str(output_path))

    html_out = html_renderer.render(
        transformed_report,
        input_path.name
    )

    pdf_out = pdf_renderer.render(
        transformed_report,
        input_path.name
    )

    return pdf_out, html_out


def process_directory(
    input_dir_name: str = "input",
    output_dir_name: str = "output"
):
    """
    Main entry point for the Attendance Generator System.
    Processes all PDF files in the input directory end-to-end.
    """
    base_dir = Path(__file__).resolve().parent
    input_dir = base_dir / input_dir_name
    output_dir = base_dir / output_dir_name

    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    transformation_service = TransformationService()
    html_renderer = HtmlRenderer(output_dir=str(output_dir))
    pdf_renderer = PdfRenderer(output_dir=str(output_dir))

    pdf_files = list(input_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in '{input_dir}'.")
        return

    print(
        f"Found {len(pdf_files)} PDF files to process. "
        "Starting pipeline...\n"
    )

    for file_path in pdf_files:
        print(f"{'=' * 50}")
        print(f"Processing: {file_path.name}")

        try:
            print("  - Running OCR extraction...")
            raw_text = extract_text_from_pdf(str(file_path))

            print("  - Classifying report type...")
            report_type = classify_report(raw_text)
            print(f"    Detected type: {report_type.value}")

            print("  - Parsing report data...")
            parser = get_parser(report_type)
            original_report = parser.parse(raw_text)

            print(
                f"    Successfully parsed "
                f"{len(original_report.rows)} rows."
            )

            print("  - Applying transformation rules...")
            transformed_report = transformation_service.process(
                original_report,
                rules={}
            )

            print("  - Rendering HTML and PDF outputs...")

            html_out = html_renderer.render(
                transformed_report,
                file_path.name
            )

            pdf_out = pdf_renderer.render(
                transformed_report,
                file_path.name
            )

            print("  [V] Success! Outputs saved to:")
            print(f"      HTML: {html_out.name}")
            print(f"      PDF:  {pdf_out.name}")

        except AttendanceSystemError as e:
            print(
                f"  [X] Domain Error processing "
                f"{file_path.name}: {e}"
            )

        except Exception as e:
            traceback.print_exc()
            print(f"  [X] Error processing {file_path.name}: {e}")

    print(f"\n{'=' * 50}")
    print("Batch processing complete.")


if __name__ == "__main__":
    process_directory()
