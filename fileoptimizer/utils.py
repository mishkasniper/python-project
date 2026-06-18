"""Вспомогательные функции для обработки файлов."""

from pathlib import Path


def get_file_size(path: Path) -> int:
    """Возвращает размер файла в байтах."""
    return path.stat().st_size


def calculate_saved_percent(original_size: int, processed_size: int) -> float:
    """Считает процент экономии размера файла."""
    if original_size <= 0:
        return 0.0

    saved_size = original_size - processed_size
    return round(saved_size / original_size * 100, 2)
