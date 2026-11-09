
import re
from statistics import median
from typing import Dict, List

import pytesseract
from pdf2image import convert_from_path
from pytesseract import Output


def clean_text(raw_text: str) -> str:
    """Clean OCR text while preserving meaningful report data."""
    if not raw_text:
        return ""

    cleaned_lines = []

    for line in raw_text.splitlines():
        line = line.replace("|", " ")
        line = re.sub(r"[ \t]+", " ", line).strip()

        if not line:
            continue

        if not re.search(r"[0-9א-תA-Za-z₪/:.,\-]", line):
            continue

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _group_words_into_rows(words: List[Dict]) -> List[List[Dict]]:
    """Group OCR words into visual rows using vertical positions."""
    if not words:
        return []

    heights = [
        word["height"]
        for word in words
        if word["height"] > 0
    ]

    typical_height = median(heights) if heights else 12
    tolerance = max(4, min(typical_height * 0.45, 10))

    sorted_words = sorted(
        words,
        key=lambda word: word["center_y"],
    )

    rows = []

    for word in sorted_words:
        best_row = None
        best_distance = None

        for row in rows:
            row_center = median(
                item["center_y"] for item in row
            )
            distance = abs(word["center_y"] - row_center)

            if distance <= tolerance and (
                best_distance is None
                or distance < best_distance
            ):
                best_row = row
                best_distance = distance

        if best_row is None:
            rows.append([word])
        else:
            best_row.append(word)

    rows.sort(
        key=lambda row: median(
            item["center_y"] for item in row
        )
    )

    return rows


def _row_to_text(row: List[Dict]) -> str:
    """Reconstruct a visual row in right-to-left reading order."""
    ordered_words = sorted(
        row,
        key=lambda word: word["left"],
        reverse=True,
    )

    return " ".join(
        word["text"] for word in ordered_words
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text and improve date recognition from the date column."""
    pages = convert_from_path(pdf_path)

    if not pages:
        raise ValueError(
            f"No pages found in the provided PDF document: {pdf_path}"
        )

    extracted_pages = []

    for page_image in pages:
        page_width, page_height = page_image.size

        data = pytesseract.image_to_data(
            page_image,
            lang="heb",
            config="--psm 6",
            output_type=Output.DICT,
        )

        words = []

        for index, raw_word in enumerate(data["text"]):
            word_text = raw_word.strip()

            if not word_text:
                continue

            try:
                confidence = float(data["conf"][index])
                left = int(data["left"][index])
                top = int(data["top"][index])
                width = int(data["width"][index])
                height = int(data["height"][index])
            except (ValueError, TypeError, IndexError):
                continue

            if confidence < 0 or width <= 0 or height <= 0:
                continue

            words.append({
                "text": word_text,
                "left": left,
                "center_y": top + height / 2,
                "height": height,
                "width": width,
            })

        date_column_width = int(page_width * 0.30)
        date_column_left = page_width - date_column_width

        date_column = page_image.crop((
            date_column_left,
            0,
            page_width,
            page_height,
        ))

        date_candidates = {}

        for psm in (6, 11):
            date_data = pytesseract.image_to_data(
                date_column,
                lang="heb+eng",
                config=f"--psm {psm} -c tessedit_char_whitelist=0123456789/.-",
                output_type=Output.DICT,
            )

            date_words = []

            for index, raw_word in enumerate(date_data["text"]):
                word_text = raw_word.strip()

                if not word_text:
                    continue

                try:
                    confidence = float(date_data["conf"][index])
                    left = int(date_data["left"][index])
                    top = int(date_data["top"][index])
                    width = int(date_data["width"][index])
                    height = int(date_data["height"][index])
                except (ValueError, TypeError, IndexError):
                    continue

                if confidence < 0 or width <= 0 or height <= 0:
                    continue

                date_words.append({
                    "text": word_text,
                    "left": left,
                    "center_y": top + height / 2,
                    "height": height,
                    "width": width,
                    "confidence": confidence,
                })

            date_rows = _group_words_into_rows(date_words)

            for row in date_rows:
                row.sort(key=lambda word: word["left"])

                combined = "".join(word["text"] for word in row)
                combined = combined.replace(".", "/").replace("-", "/")

                match = re.search(
                    r"(?<!\d)(\d{1,2}/\d{1,2}/\d{2,4})(?!\d)",
                    combined,
                )

                if not match:
                    continue

                date = match.group(1)
                center_y = median(word["center_y"] for word in row)

                date_candidates.setdefault(center_y, []).append({
                    "date": date,
                    "confidence": sum(
                        word["confidence"] for word in row
                    ) / len(row),
                })

        for center_y, candidates in date_candidates.items():
            best = max(candidates, key=lambda item: item["confidence"])

            words.append({
                "text": best["date"],
                "left": date_column_left,
                "center_y": center_y,
                "height": 12,
                "width": date_column_width,
            })

        # Additional OCR for the summary section (Type B hourly rate)
        summary_left = int(page_width * 0.35)
        summary_right = int(page_width * 0.78)
        summary_top = int(page_height * 0.14)
        summary_bottom = int(page_height * 0.28)

        summary_image = page_image.crop((
            summary_left,
            summary_top,
            summary_right,
            summary_bottom,
        ))

        summary_image = summary_image.resize((
            summary_image.width * 2,
            summary_image.height * 2,
        ))

        summary_text = pytesseract.image_to_string(
            summary_image,
            lang="heb+eng",
            config="--psm 6",
        )


        if summary_text.strip():
            extracted_pages.append(summary_text)

        rows = _group_words_into_rows(words)

        page_lines = [
            _row_to_text(row)
            for row in rows
        ]

        extracted_pages.append("\n".join(page_lines))

    return clean_text("\n".join(extracted_pages))