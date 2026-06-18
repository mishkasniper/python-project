"""Тесты для оптимизации изображений."""

from pathlib import Path

import pytest
from PIL import Image

from fileoptimizer.exceptions import UnsupportedFormatError
from fileoptimizer.image_optimizer import ImageOptimizer
from fileoptimizer.models import ImageOptimizeResult


def create_test_image(path: Path, size: tuple[int, int] = (800, 600)) -> None:
    """Создаёт тестовое изображение."""
    image = Image.new("RGB", size, color="red")
    image.save(path)


def test_optimize_jpg_creates_output_file(tmp_path: Path) -> None:
    """Проверяет, что JPG оптимизируется и сохраняется."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path)

    result = ImageOptimizer().optimize(
        input_path=input_path,
        output_dir=output_dir,
        output_format="webp",
        quality=75,
    )

    assert isinstance(result, ImageOptimizeResult)
    assert result.output_path.exists()
    assert result.output_format == "webp"
    assert result.size_info.original_size > 0
    assert result.size_info.processed_size > 0
    assert result.width == 800
    assert result.height == 600


def test_optimize_resizes_image_by_width(tmp_path: Path) -> None:
    """Проверяет уменьшение изображения по ширине."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path, size=(1000, 500))

    result = ImageOptimizer().optimize(
        input_path=input_path,
        output_dir=output_dir,
        output_format="jpg",
        quality=80,
        max_width=500,
    )

    assert result.output_path.exists()
    assert result.width == 500
    assert result.height == 250


def test_optimize_resizes_image_by_height(tmp_path: Path) -> None:
    """Проверяет уменьшение изображения по высоте."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path, size=(1000, 500))

    result = ImageOptimizer().optimize(
        input_path=input_path,
        output_dir=output_dir,
        output_format="jpg",
        quality=80,
        max_height=250,
    )

    assert result.output_path.exists()
    assert result.width == 500
    assert result.height == 250


def test_output_directory_is_created(tmp_path: Path) -> None:
    """Проверяет, что выходная папка создаётся автоматически."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "nested" / "output"

    create_test_image(input_path)

    result = ImageOptimizer().optimize(
        input_path=input_path,
        output_dir=output_dir,
    )

    assert output_dir.exists()
    assert result.output_path.exists()


def test_invalid_input_format_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку для неподдерживаемого входного формата."""
    input_path = tmp_path / "input.txt"
    output_dir = tmp_path / "output"

    input_path.write_text("not an image", encoding="utf-8")

    with pytest.raises(UnsupportedFormatError):
        ImageOptimizer().optimize(
            input_path=input_path,
            output_dir=output_dir,
        )


def test_invalid_output_format_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку для неподдерживаемого выходного формата."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path)

    with pytest.raises(UnsupportedFormatError):
        ImageOptimizer().optimize(
            input_path=input_path,
            output_dir=output_dir,
            output_format="gif",
        )


def test_invalid_quality_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку при некорректном качестве."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path)

    with pytest.raises(ValueError):
        ImageOptimizer().optimize(
            input_path=input_path,
            output_dir=output_dir,
            quality=0,
        )


def test_invalid_resize_params_raise_error(tmp_path: Path) -> None:
    """Проверяет ошибку при некорректном размере."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path)

    with pytest.raises(ValueError):
        ImageOptimizer().optimize(
            input_path=input_path,
            output_dir=output_dir,
            max_width=-100,
        )


def test_invalid_enhancement_factor_raises_error(tmp_path: Path) -> None:
    """Проверяет ошибку при некорректном коэффициенте улучшения."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path)

    with pytest.raises(ValueError):
        ImageOptimizer().optimize(
            input_path=input_path,
            output_dir=output_dir,
            contrast_factor=3.0,
        )


def test_enhancement_factors_do_not_break_optimization(tmp_path: Path) -> None:
    """Проверяет, что коэффициенты улучшения не ломают оптимизацию."""
    input_path = tmp_path / "input.jpg"
    output_dir = tmp_path / "output"

    create_test_image(input_path)

    result = ImageOptimizer().optimize(
        input_path=input_path,
        output_dir=output_dir,
        contrast_factor=1.2,
        sharpness_factor=1.3,
        brightness_factor=1.1,
    )

    assert result.output_path.exists()
    assert result.width == 800
    assert result.height == 600
