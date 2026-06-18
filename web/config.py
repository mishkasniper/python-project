"""Конфигурация приложения."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
LOCALES_DIR = BASE_DIR / "locales"
DOCS_DIR = STATIC_DIR / 'docs'
JOBS_BASE_DIR = Path("tmp/jobs")

# Максимальный размер загружаемого файла (в байтах) - 50 МБ
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

# Доступные языки
LANGUAGES = ["ru", "en"]
DEFAULT_LANGUAGE = "ru"
