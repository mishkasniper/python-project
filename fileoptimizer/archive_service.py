"""Сервис для создания архивов."""

import tarfile
import zipfile
from pathlib import Path

from fileoptimizer.exceptions import ArchiveCreationError, UnsupportedFormatError
from fileoptimizer.models import ArchiveResult, SizeInfo
from fileoptimizer.storage import StorageService
from fileoptimizer.utils import calculate_saved_percent, get_file_size

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

    @staticmethod
    def _create_zip_archive(input_paths: list[Path], output_path: Path) -> None:
        """Создаёт ZIP-архив из списка файлов."""
        with zipfile.ZipFile(
            output_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
        ) as archive:
            for input_path in input_paths:
                archive.write(input_path, arcname=input_path.name)

    @staticmethod
    def _create_tar_archive(
        input_paths: list[Path],
        output_path: Path,
        archive_format: str,
    ) -> None:
        """Создаёт TAR или TAR.GZ архив из списка файлов."""
        mode = "w:gz" if archive_format == "tar.gz" else "w"

        with tarfile.open(output_path, mode=mode) as archive:
            for input_path in input_paths:
                archive.add(input_path, arcname=input_path.name)

    def create_archive(
        self,
        input_paths: list[Path],
        output_dir: Path,
        archive_name: str = "archive",
        archive_format: str = "zip",
    ) -> ArchiveResult:
        """Создаёт архив из списка файлов.

        Args:
            input_paths: Список файлов для архивации.
            output_dir: Папка для сохранения архива.
            archive_name: Имя создаваемого архива.
            archive_format: Формат архива: zip, tar или tar.gz.

        Returns:
            Информация о созданном архиве.

        Raises:
            FileNotFoundError: Если один из файлов не найден.
            ValueError: Если список файлов пустой или путь не является файлом.
            UnsupportedFormatError: Если формат архива не поддерживается.
            ArchiveCreationError: Если произошла ошибка при создании архива.

        """
        archive_format = self._normalize_archive_format(archive_format)

        self._validate_input_paths(input_paths)

        output_path = self.build_archive_path(
            output_dir=output_dir,
            archive_name=archive_name,
            archive_format=archive_format,
        )

        original_size = self._get_total_size(input_paths)

        try:
            if archive_format == "zip":
                self._create_zip_archive(
                    input_paths=input_paths,
                    output_path=output_path,
                )
            else:
                self._create_tar_archive(
                    input_paths=input_paths,
                    output_path=output_path,
                    archive_format=archive_format,
                )
        except OSError as error:
            raise ArchiveCreationError("Problems with archive creation.") from error

        processed_size = get_file_size(output_path)

        return ArchiveResult(
            output_path=output_path,
            size_info=SizeInfo(
                original_size=original_size,
                processed_size=processed_size,
                saved_percent=calculate_saved_percent(
                    original_size=original_size,
                    processed_size=processed_size,
                ),
            ),
            archive_format=archive_format,
            files_count=len(input_paths),
        )
