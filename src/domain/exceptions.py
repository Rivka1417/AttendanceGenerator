class AttendanceSystemError(Exception):
    """Base exception for all attendance system errors."""
    pass

class ClassificationError(AttendanceSystemError):
    """Raised when the report type cannot be determined from the OCR text."""
    pass

class ParserNotFoundError(AttendanceSystemError):
    """Raised when a parser factory cannot find a matching parser."""
    pass