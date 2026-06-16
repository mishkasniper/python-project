"""Сервис для создания архивов."""

from pathlib import Path

from fileoptimizer.exceptions import UnsupportedFormatError
from fileoptimizer.storage import StorageService
from fileoptimizer.utils import get_file_size


SUPPORTED_ARCHIVE_FORMATS = {"zip", "tar", "tar.gz"}


class ArchiveService:
    """Сервис для создания архивов разных форматов."""

    @staticmethod
    def _normalize_archive_format(archive_format: str) -> str:
        """Возвращает нормализованный формат архива."""
        normalized_format = archive_format.lower().lstrip(".")

        if normalized_format == "tgz":
            normalized_format = "tar.gz"

        if normalized_format not in SUPPORTED_ARCHIVE_FORMATS:
            raise UnsupportedFormatError(
                f"Archive format '{archive_format}' is not supported. "
                f"Available formats: {', '.join(sorted(SUPPORTED_ARCHIVE_FORMATS))}."
            )

        return normalized_format

    @staticmethod
    def _validate_input_paths(input_paths: list[Path]) -> None:
        """Проверяет список файлов для архивации."""
        if not input_paths:
            raise ValueError("Input paths list cannot be empty.")

        for input_path in input_paths:
            if not input_path.exists():
                raise FileNotFoundError(f"Input file does not exist: {input_path}")

            if not input_path.is_file():
                raise ValueError(f"Input path is not a file: {input_path}")

    @staticmethod
    def _normalize_archive_name(archive_name: str) -> str:
        """Возвращает безопасное имя архива без расширения."""
        name = Path(archive_name).name.strip()

        if not name:
            return "archive"

        lower_name = name.lower()

        for suffix in (".tar.gz", ".tgz", ".zip", ".tar"):
            if lower_name.endswith(suffix):
                name = name[: -len(suffix)]
                break

        safe_name = StorageService.safe_filename(name)

        return Path(safe_name).stem or "archive"

    @classmethod
    def build_archive_path(
        cls,
        output_dir: Path,
        archive_name: str,
        archive_format: str,
    ) -> Path:
        """Строит путь для создаваемого архива."""
        output_dir.mkdir(parents=True, exist_ok=True)

        normalized_format = cls._normalize_archive_format(archive_format)
        normalized_name = cls._normalize_archive_name(archive_name)

        return output_dir / f"{normalized_name}.{normalized_format}"

    @staticmethod
    def _get_total_size(input_paths: list[Path]) -> int:
        """Возвращает общий размер исходных файлов."""
        return sum(get_file_size(path) for path in input_paths)