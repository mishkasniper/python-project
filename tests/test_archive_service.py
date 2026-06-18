"""Тесты для сервиса создания архивов."""

import tarfile
import zipfile
from pathlib import Path

import pytest

from fileoptimizer.archive_service import ArchiveService
from fileoptimizer.exceptions import UnsupportedFormatError
from fileoptimizer.models import ArchiveResult


def create_text_file(path: Path, content: str = "test content") -> None:
    """Создаёт текстовый файл для тестов."""
    path.write_text(content, encoding="utf-8")


def test_create_zip_archive_creates_output_file(tmp_path: Path) -> None:
    """Проверяет создание ZIP-архива."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1, "hello")
    create_text_file(file2, "world")

    result = ArchiveService().create_archive(
        input_paths=[file1, file2],
        output_dir=output_dir,
        archive_name="my_archive",
        archive_format="zip",
    )

    assert isinstance(result, ArchiveResult)
    assert result.output_path.exists()
    assert result.output_path.name == "my_archive.zip"
    assert result.archive_format == "zip"
    assert result.files_count == 2
    assert result.size_info.original_size > 0
    assert result.size_info.processed_size > 0


def test_zip_archive_contains_input_files(tmp_path: Path) -> None:
    """Проверяет, что ZIP-архив содержит исходные файлы."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1, "hello")
    create_text_file(file2, "world")

    result = ArchiveService().create_archive(
        input_paths=[file1, file2],
        output_dir=output_dir,
        archive_name="archive",
        archive_format="zip",
    )

    with zipfile.ZipFile(result.output_path) as archive:
        names = archive.namelist()

    assert "file1.txt" in names
    assert "file2.txt" in names


def test_create_tar_archive_creates_output_file(tmp_path: Path) -> None:
    """Проверяет создание TAR-архива."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1, "hello")
    create_text_file(file2, "world")

    result = ArchiveService().create_archive(
        input_paths=[file1, file2],
        output_dir=output_dir,
        archive_name="my_archive",
        archive_format="tar",
    )

    assert result.output_path.exists()
    assert result.output_path.name == "my_archive.tar"
    assert result.archive_format == "tar"
    assert result.files_count == 2


def test_tar_archive_contains_input_files(tmp_path: Path) -> None:
    """Проверяет, что TAR-архив содержит исходные файлы."""
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1, "hello")
    create_text_file(file2, "world")

    result = ArchiveService().create_archive(
        input_paths=[file1, file2],
        output_dir=output_dir,
        archive_name="archive",
        archive_format="tar",
    )

    with tarfile.open(result.output_path) as archive:
        names = archive.getnames()

    assert "file1.txt" in names
    assert "file2.txt" in names


def test_create_tar_gz_archive_creates_output_file(tmp_path: Path) -> None:
    """Проверяет создание TAR.GZ-архива."""
    file1 = tmp_path / "file1.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1, "hello")

    result = ArchiveService().create_archive(
        input_paths=[file1],
        output_dir=output_dir,
        archive_name="backup",
        archive_format="tar.gz",
    )

    assert result.output_path.exists()
    assert result.output_path.name == "backup.tar.gz"
    assert result.archive_format == "tar.gz"
    assert result.files_count == 1


def test_tgz_format_is_normalized_to_tar_gz(tmp_path: Path) -> None:
    """Проверяет, что формат TGZ нормализуется в TAR.GZ."""
    file1 = tmp_path / "file1.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1, "hello")

    result = ArchiveService().create_archive(
        input_paths=[file1],
        output_dir=output_dir,
        archive_name="backup",
        archive_format="tgz",
    )

    assert result.output_path.exists()
    assert result.output_path.name == "backup.tar.gz"
    assert result.archive_format == "tar.gz"


def test_archive_name_is_sanitized(tmp_path: Path) -> None:
    """Проверяет очистку имени архива."""
    file1 = tmp_path / "file1.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1)

    result = ArchiveService().create_archive(
        input_paths=[file1],
        output_dir=output_dir,
        archive_name="../../my archive!!!.zip",
        archive_format="zip",
    )

    assert result.output_path.name == "my_archive.zip"


def test_archive_name_with_extension_does_not_duplicate_extension(
    tmp_path: Path,
) -> None:
    """Проверяет, что расширение архива не дублируется."""
    file1 = tmp_path / "file1.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1)

    result = ArchiveService().create_archive(
        input_paths=[file1],
        output_dir=output_dir,
        archive_name="backup.zip",
        archive_format="zip",
    )

    assert result.output_path.name == "backup.zip"


def test_empty_input_paths_raise_error(tmp_path: Path) -> None:
    """Проверяет ошибку при пустом списке файлов."""
    with pytest.raises(ValueError):
        ArchiveService().create_archive(
            input_paths=[],
            output_dir=tmp_path / "output",
        )


def test_missing_input_file_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку, если один из файлов не существует."""
    missing_file = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        ArchiveService().create_archive(
            input_paths=[missing_file],
            output_dir=tmp_path / "output",
        )


def test_input_directory_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку, если вместо файла передана папка."""
    input_dir = tmp_path / "input_dir"
    input_dir.mkdir()

    with pytest.raises(ValueError):
        ArchiveService().create_archive(
            input_paths=[input_dir],
            output_dir=tmp_path / "output",
        )


def test_unsupported_archive_format_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку для неподдерживаемого формата архива."""
    file1 = tmp_path / "file1.txt"
    output_dir = tmp_path / "output"

    create_text_file(file1)

    with pytest.raises(UnsupportedFormatError):
        ArchiveService().create_archive(
            input_paths=[file1],
            output_dir=output_dir,
            archive_format="rar",
        )


def test_output_directory_is_created(tmp_path: Path) -> None:
    """Проверяет, что выходная папка создается автоматически."""
    file1 = tmp_path / "file1.txt"
    output_dir = tmp_path / "nested" / "output"

    create_text_file(file1)

    result = ArchiveService().create_archive(
        input_paths=[file1],
        output_dir=output_dir,
        archive_name="archive",
        archive_format="zip",
    )

    assert output_dir.exists()
    assert result.output_path.exists()
