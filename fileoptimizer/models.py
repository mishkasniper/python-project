"""Модели данных для результатов обработки файлов."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SizeInfo:
    """Информация о размере файла до и после обработки."""

    original_size: int
    processed_size: int
    saved_percent: float


@dataclass(frozen=True)
class ImageOptimizeResult:
    """Результат оптимизации изображения."""

    output_path: Path
    size_info: SizeInfo
    output_format: str
    width: int
    height: int


@dataclass(frozen=True)
class ArchiveResult:
    """Результат создания архива."""

    output_path: Path
    size_info: SizeInfo
    archive_format: str
    files_count: int
