"""Doit tasks for FileOptimizer."""

import shutil
from pathlib import Path

DOIT_CONFIG = {
    'default_tasks': ['lint', 'test', 'build'],
}

PROJECT_ROOT = Path(__file__).parent
WEB_DIR = PROJECT_ROOT / 'web'
FILEOPTIMIZER_DIR = PROJECT_ROOT / 'fileoptimizer'
TESTS_DIR = PROJECT_ROOT / 'tests'
DOCS_SOURCE = PROJECT_ROOT / 'docs' / 'source'
DOCS_BUILD = PROJECT_ROOT / 'docs' / '_build'
LOCALES_DIR = WEB_DIR / 'locales'


def task_lint():
    """Run ruff and pydocstyle on all Python files."""
    return {
        'actions': [
            f'ruff check {FILEOPTIMIZER_DIR} {WEB_DIR} {TESTS_DIR}',
            f'pydocstyle {FILEOPTIMIZER_DIR} {WEB_DIR}',
        ],
        'verbosity': 2,
    }


def task_test():
    """Run pytest with coverage."""
    return {
        'actions': [
            f'pytest --cov=fileoptimizer --cov=web --cov-report=term-missing {TESTS_DIR}',
        ],
        'verbosity': 2,
    }


def task_docs():
    """Build Sphinx documentation."""
    return {
        'actions': [
            f'sphinx-build -b html {DOCS_SOURCE} {DOCS_BUILD}',
        ],
        'file_dep': [DOCS_SOURCE / 'conf.py', DOCS_SOURCE / 'index.rst'],
        'targets': [DOCS_BUILD / 'index.html'],
        'verbosity': 2,
    }


def task_translate():
    """Extract messages and update .po files."""
    pot_file = LOCALES_DIR / 'messages.pot'
    py_files = list(FILEOPTIMIZER_DIR.glob('**/*.py')) + list(WEB_DIR.glob('**/*.py'))
    html_files = list(WEB_DIR.glob('templates/**/*.html'))
    all_files = py_files + html_files
    return {
        'actions': [
            f'pybabel extract -F babel.cfg -o {pot_file} {FILEOPTIMIZER_DIR} {WEB_DIR}',
            f'pybabel update -i {pot_file} -d {LOCALES_DIR}',
        ],
        'file_dep': all_files,
        'targets': [pot_file],
        'verbosity': 2,
    }


def task_compile():
    """Compile .mo files."""
    po_files = list(LOCALES_DIR.glob('*/LC_MESSAGES/*.po'))
    mo_files = [p.with_suffix('.mo') for p in po_files]
    return {
        'actions': [
            f'pybabel compile -d {LOCALES_DIR}',
        ],
        'file_dep': po_files,
        'targets': mo_files,
        'verbosity': 2,
    }


def task_clean_all():
    """Remove temporary and build artifacts."""
    dirs_to_remove = [
        PROJECT_ROOT / 'tmp',
        DOCS_BUILD,
        PROJECT_ROOT / 'dist',
        PROJECT_ROOT / 'build',
        PROJECT_ROOT / 'fileoptimizer.egg-info',
    ]
    actions = []
    for d in dirs_to_remove:
        actions.append(lambda d=d: shutil.rmtree(d, ignore_errors=True))
    actions.append(lambda: [p.unlink() for p in LOCALES_DIR.glob('**/*.mo') if p.exists()])
    actions.append(lambda: [shutil.rmtree(p, ignore_errors=True) for p in PROJECT_ROOT.glob('**/__pycache__')])
    return {
        'actions': actions,
        'verbosity': 2,
    }


def task_build():
    """Build wheel distribution."""
    return {
        'actions': [
            'python -m build --wheel',
        ],
        'file_dep': [
            PROJECT_ROOT / 'pyproject.toml',
            *list(FILEOPTIMIZER_DIR.glob('**/*.py')),
            *list(WEB_DIR.glob('**/*.py')),
            *list(WEB_DIR.glob('templates/**/*')),
            *list(WEB_DIR.glob('static/**/*')),
            *list(LOCALES_DIR.glob('**/*.mo')),
        ],
        'targets': [PROJECT_ROOT / 'dist' / '*.whl'],
        'verbosity': 2,
    }