"""Doit tasks for FileOptimizer."""

import shutil
from pathlib import Path

DOIT_CONFIG = {
    'default_tasks': ['lint', 'test', 'docs', 'build'],
}

PROJECT_ROOT = Path(__file__).parent
WEB_DIR = PROJECT_ROOT / 'web'
WEB_DOCS_DIR = WEB_DIR / 'static' / 'docs'
FILEOPTIMIZER_DIR = PROJECT_ROOT / 'fileoptimizer'
TESTS_DIR = PROJECT_ROOT / 'tests'
DOCS_SOURCE = PROJECT_ROOT / 'docs' / 'source'
DOCS_BUILD = WEB_DIR / 'static' / 'docs'
DOCS_DOCTREES = PROJECT_ROOT / 'docs' / '_doctrees'
LOCALES_DIR = WEB_DIR / 'locales'


def task_lint():
    """Run ruff on all Python files."""
    return {
        'actions': [
            'ruff check .',
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
            f'sphinx-build -b html -d {DOCS_DOCTREES} {DOCS_SOURCE} {DOCS_BUILD}',
        ],
        'file_dep': [
            DOCS_SOURCE / 'conf.py',
            DOCS_SOURCE / 'index.rst',
        ],
        'targets': [DOCS_BUILD / 'index.html'],
        'verbosity': 2,
    }


def copy_docs_to_static():
    """Copy built documentation to web static directory."""
    if WEB_DOCS_DIR.exists():
        shutil.rmtree(WEB_DOCS_DIR)

    shutil.copytree(DOCS_BUILD, WEB_DOCS_DIR)


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


def remove_mo_files():
    """Remove compiled translation files."""
    for path in LOCALES_DIR.glob('**/*.mo'):
        if path.exists():
            path.unlink()


def remove_pycache_dirs():
    """Remove Python cache directories."""
    for path in PROJECT_ROOT.glob('**/__pycache__'):
        shutil.rmtree(path, ignore_errors=True)


def task_clean_all():
    """Remove temporary and build artifacts."""
    dirs_to_remove = [
        PROJECT_ROOT / 'tmp',
        DOCS_BUILD,
        DOCS_DOCTREES,
        PROJECT_ROOT / 'dist',
        PROJECT_ROOT / 'build',
        PROJECT_ROOT / 'fileoptimizer.egg-info',
        PROJECT_ROOT / '.pytest_cache',
        PROJECT_ROOT / '.ruff_cache',
    ]

    actions = []
    for directory in dirs_to_remove:
        actions.append(lambda directory=directory: shutil.rmtree(directory, ignore_errors=True))

    actions.append(lambda: (PROJECT_ROOT / '.coverage').unlink(missing_ok=True))
    actions.append(remove_mo_files)
    actions.append(remove_pycache_dirs)

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
        'task_dep': [
            'compile',
            'docs',
            ],
        'file_dep': [
            PROJECT_ROOT / 'pyproject.toml',
            *list(FILEOPTIMIZER_DIR.glob('**/*.py')),
            *list(WEB_DIR.glob('**/*.py')),
            *list(WEB_DIR.glob('templates/**/*')),
            *list(WEB_DIR.glob('static/**/*')),
        ],
        'targets': [PROJECT_ROOT / 'dist'],
        'verbosity': 2,
    }
