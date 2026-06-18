"""Сервис для работы с временными файлами проекта."""

import re
import shutil
from pathlib import Path
from uuid import uuid4

from fileoptimizer.exceptions import StorageError


class StorageService:
    """Сервис для создания, хранения и удаления временных файлов."""

    def __init__(self, base_dir: Path = Path("tmp/jobs")) -> None:
        """Инициализирует сервис временного хранения файлов."""
        self.base_dir = base_dir

    def create_job_dir(self) -> Path:
        """Создаёт папку отдельной задачи обработки."""
        job_dir = self.base_dir / uuid4().hex

        self.get_input_dir(job_dir)
        self.get_output_dir(job_dir)

        return job_dir

    @staticmethod
    def get_input_dir(job_dir: Path) -> Path:
        """Возвращает папку для исходных файлов задачи."""
        input_dir = job_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        return input_dir

    @staticmethod
    def get_output_dir(job_dir: Path) -> Path:
        """Возвращает папку для обработанных файлов задачи."""
        output_dir = job_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        return output_dir

    @staticmethod
    def safe_filename(filename: str) -> str:
        """Возвращает безопасное имя файла."""
        name = Path(filename).name.strip()

        if not name:
            raise StorageError("Filename cannot be empty.")

        path = Path(name)
        stem = path.stem
        suffix = path.suffix.lower()

        safe_stem = re.sub(r"[^A-Za-zА-Яа-яЁё0-9._-]+", "_", stem)
        safe_stem = safe_stem.strip("._-")

        if not safe_stem:
            safe_stem = "file"

        return f"{safe_stem[:80]}{suffix}"

    def copy_to_input(
        self,
        source_path: Path,
        job_dir: Path,
        filename: str | None = None,
    ) -> Path:
        """Копирует файл в input-папку задачи.

        Args:
            source_path: Путь к исходному файлу.
            job_dir: Папка задачи обработки.
            filename: Имя файла после копирования.

        Returns:
            Путь к скопированному файлу.

        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {source_path}")

        if not source_path.is_file():
            raise ValueError(f"Source path is not a file: {source_path}")

        input_dir = self.get_input_dir(job_dir)
        safe_name = self.safe_filename(filename or source_path.name)

        destination_path = input_dir / safe_name
        shutil.copy2(source_path, destination_path)

        return destination_path

    def cleanup_job_dir(self, job_dir: Path) -> None:
        """Удаляет папку задачи обработки."""
        resolved_base_dir = self.base_dir.resolve()
        resolved_job_dir = job_dir.resolve()

        try:
            resolved_job_dir.relative_to(resolved_base_dir)
        except ValueError as error:
            raise StorageError("Cannot cleanup directory outside base_dir.") from error

        if resolved_job_dir.exists():
            shutil.rmtree(resolved_job_dir)
