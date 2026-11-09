from abc import ABC, abstractmethod
from pathlib import Path
from src.domain.models import AttendanceReport

class BaseRenderer(ABC):
    """
    Abstract base class defining the rendering interface for attendance reports.
    All format-specific renderers (e.g., HTML, PDF) must inherit from this class
    and implement the render method to generate output files safely.
    """

    def __init__(self, output_dir: str = "output"):
        """
        Initializes the renderer with a target output directory for generated files.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_output_filename(self, original_filename: str, extension: str) -> Path:
        """
        Generates the consistent output filename based on the source filename,
        appending '-new' and the target file extension, directed to the output folder.
        """
        path_obj = Path(original_filename)
        stem = path_obj.stem
        new_name = f"{stem}-new.{extension}"
        return self.output_dir / new_name

    @abstractmethod
    def render(self, report: AttendanceReport, original_filename: str) -> Path:
        """
        Renders the attendance report into a specific format and saves it
        to the designated output directory, returning the path of the generated file.
        """
        pass