
import re

from src.domain.enums import ReportType
from src.domain.exceptions import ClassificationError


def classify_report(raw_text: str) -> ReportType:
    """Classify attendance reports using OCR-tolerant patterns."""

    if not raw_text or not raw_text.strip():
        raise ClassificationError(
            "Cannot classify an empty OCR document."
        )

    normalized = " ".join(raw_text.split())
    compact = re.sub(r"[\s|:־\-]", "", normalized)

    type_a_patterns = {
        r"100\s*%": 5,
        r"125\s*%": 5,
        r"150\s*%": 5,
        r"שעות\s*100": 4,
        r"שעות\s*125": 4,
        r"שעות\s*150": 4,
        r"בונוס": 2,
        r"נסיעות": 2,
        r"הפסקה": 2,
    }

    type_b_patterns = {
        r"מחיר\s*לשעה": 5,
        r"תעריף\s*לשעה": 5,
        r"סה[\"״]?כ\s*לתשלום": 5,
        r"לתשלום": 3,
        r"ימי\s*עבודה": 4,
        r"שעות\s*חודשיות": 4,
        r"כרטיס\s*עובד": 3,
        r"יום\s+שעת\s+סה": 4,
        r"להודש": 3,
        r"לחודש": 3,
        r"הערות": 1,
    }

    def calculate_score(patterns: dict) -> int:
        score = 0

        for pattern, weight in patterns.items():
            matches = re.findall(
                pattern,
                normalized,
                flags=re.IGNORECASE,
            )
            score += len(matches) * weight

        return score

    score_a = calculate_score(type_a_patterns)
    score_b = calculate_score(type_b_patterns)

    # OCR sometimes removes spaces from Hebrew headings.
    compact_type_b_patterns = (
        ("ימיעבודה", 4),
        ("שעותחודשיות", 4),
        ("מחירלשעה", 5),
        ("תעריףלשעה", 5),
        ("כרטיסעובד", 3),
        ("להודש", 3),
        ("לחודש", 3),
        ("יוםשעתסה", 4),
    )

    for pattern, weight in compact_type_b_patterns:
        if pattern in compact:
            score_b += weight

    if score_a < 3 and score_b < 3:
        raise ClassificationError(
            "Not enough identifying information in OCR text. "
            f"Scores: TYPE_A={score_a}, TYPE_B={score_b}."
        )

    if score_a - score_b >= 2:
        return ReportType.TYPE_A

    if score_b - score_a >= 2:
        return ReportType.TYPE_B

    raise ClassificationError(
        "Report type is ambiguous. "
        f"Scores: TYPE_A={score_a}, TYPE_B={score_b}. "
        "Please verify the OCR text."
    )
