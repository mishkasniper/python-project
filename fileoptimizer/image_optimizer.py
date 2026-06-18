from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from fileoptimizer.exceptions import OptimizationError, UnsupportedFormatError
from fileoptimizer.models import ImageOptimizeResult, SizeInfo
from fileoptimizer.utils import calculate_saved_percent, get_file_size

SUPPORTED_INPUT_FORMATS = {"jpg", "jpeg", "png", "webp"}
SUPPORTED_OUTPUT_FORMATS = {"jpg", "jpeg", "png", "webp"}


class ImageOptimizer:
    """Сервис для сжатия, конвертации и улучшения изображений."""

    @staticmethod
    def _validate_optimize_params(
        input_path: Path,
        output_dir: Path,
        output_format: str,
        quality: int,
    ) -> str:
        """Проверяет параметры и возвращает нормализованный выходной формат."""
        if not input_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {input_path}")

        if not input_path.is_file():
            raise ValueError(f"Input path is not a file: {input_path}")

        input_extension = input_path.suffix.lower().lstrip(".")

        if input_extension not in SUPPORTED_INPUT_FORMATS:
            raise UnsupportedFormatError(
                f"Input format '{input_extension}' is not supported. "
                f"Available formats: {', '.join(sorted(SUPPORTED_INPUT_FORMATS))}."
            )

        normalized_output_format = output_format.lower().lstrip(".")

        if normalized_output_format == "jpeg":
            normalized_output_format = "jpg"

        if normalized_output_format not in SUPPORTED_OUTPUT_FORMATS:
            raise UnsupportedFormatError(
                f"Output format '{output_format}' is not supported. "
                f"Available formats: {', '.join(sorted(SUPPORTED_OUTPUT_FORMATS))}."
            )

        if not 1 <= quality <= 100:
            raise ValueError("Quality must be between 1 and 100.")

        output_dir.mkdir(parents=True, exist_ok=True)

        return normalized_output_format

    @staticmethod
    def _validate_enhancement_factor(name: str, value: float) -> None:
        """Проверяет коэффициент визуального улучшения изображения."""
        if not 0.5 <= value <= 2.0:
            raise ValueError(f"{name} must be between 0.5 and 2.0.")

    @staticmethod
    def _validate_resize_params(
        max_width: int | None,
        max_height: int | None,
    ) -> None:
        """Проверяет параметры изменения размера изображения."""
        if max_width is not None and max_width <= 0:
            raise ValueError("max_width must be positive.")

        if max_height is not None and max_height <= 0:
            raise ValueError("max_height must be positive.")

    @staticmethod
    def build_output_path(
        input_path: Path,
        output_dir: Path,
        output_format: str,
    ) -> Path:
        """Строит путь для выходного файла."""
        return output_dir / f"{input_path.stem}_optimized.{output_format}"

    @staticmethod
    def get_pillow_save_format(output_format: str) -> str:
        """Возвращает формат Pillow для сохранения изображения."""
        if output_format == "jpg":
            return "JPEG"

        return output_format.upper()

    @staticmethod
    def get_save_options(output_format: str, quality: int) -> dict[str, int | bool]:
        """Подготавливает параметры оптимизации."""
        if output_format == "jpg":
            return {"quality": quality, "optimize": True}

        if output_format == "webp":
            return {"quality": quality, "method": 6}

        if output_format == "png":
            return {"optimize": True}

        return {}

    @staticmethod
    def prepare_image_for_format(
        image: Image.Image,
        output_format: str,
    ) -> Image.Image:
        """Подготавливает цветовой режим изображения для выбранного формата."""
        if output_format == "jpg":
            return image.convert("RGB")

        if image.mode not in {"RGB", "RGBA"}:
            return image.convert("RGBA")

        return image

    @staticmethod
    def resize_keep_aspect_ratio(
        image: Image.Image,
        max_width: int | None = None,
        max_height: int | None = None,
    ) -> Image.Image:
        """Изменяет размер изображения с сохранением пропорций."""
        if max_width is None and max_height is None:
            return image

        target_width = max_width or image.width
        target_height = max_height or image.height

        resized_image = image.copy()
        resized_image.thumbnail((target_width, target_height))

        return resized_image

    @staticmethod
    def apply_enhancements(
        image: Image.Image,
        contrast_factor: float = 1.0,
        sharpness_factor: float = 1.0,
        brightness_factor: float = 1.0,
    ) -> Image.Image:
        """Применяет визуальные улучшения изображения по заданным коэффициентам."""
        enhanced_image = image

        if contrast_factor != 1.0:
            enhanced_image = ImageEnhance.Contrast(enhanced_image).enhance(contrast_factor)

        if sharpness_factor != 1.0:
            enhanced_image = ImageEnhance.Sharpness(enhanced_image).enhance(sharpness_factor)

        if brightness_factor != 1.0:
            enhanced_image = ImageEnhance.Brightness(enhanced_image).enhance(brightness_factor)

        return enhanced_image

    def optimize(
        self,
        input_path: Path,
        output_dir: Path,
        output_format: str = "webp",
        quality: int = 75,
        max_width: int | None = None,
        max_height: int | None = None,
        contrast_factor: float = 1.0,
        sharpness_factor: float = 1.0,
        brightness_factor: float = 1.0,
    ) -> ImageOptimizeResult:
        """Оптимизирует изображение и сохраняет результат.

        Args:
            input_path: Путь к исходной фотографии.
            output_dir: Путь к папке для сохранения результата.
            output_format: Формат сохраненного изображения: webp, jpg, png, jpeg.
            quality: Качество сжатия для JPG и WebP. 1 <= quality <= 100.
            max_width: Максимальная ширина.
            max_height: Максимальная высота.
            contrast_factor: Коэффициент контраста. 0.5 <= factor <= 2.0 (1 - без изменений)
            sharpness_factor: Коэффициент остроты. 0.5 <= factor <= 2.0 (1 - без изменений)
            brightness_factor: Коэффициент яркости. 0.5 <= factor <= 2.0 (1 - без изменений)

        Raises:
            FileNotFoundError: Если исходный файл не найден.
            ValueError: Если путь не является файлом или параметры некорректны.
            UnsupportedFormatError: Если входной или выходной формат не поддерживается.
            OptimizationError: Если произошла ошибка при обработке изображения.

        Returns:
            Информация о сохранённом изображении и статистике оптимизации.

        """
        output_format = self._validate_optimize_params(
            input_path=input_path,
            output_dir=output_dir,
            output_format=output_format,
            quality=quality,
        )

        self._validate_resize_params(max_width, max_height)

        self._validate_enhancement_factor("contrast_factor", contrast_factor)
        self._validate_enhancement_factor("sharpness_factor", sharpness_factor)
        self._validate_enhancement_factor("brightness_factor", brightness_factor)

        output_path = self.build_output_path(
            input_path=input_path,
            output_dir=output_dir,
            output_format=output_format,
        )

        result_width = 0
        result_height = 0
        original_size = get_file_size(input_path)
        try:
            with Image.open(input_path) as image:
                processed_image = ImageOps.exif_transpose(image)

                processed_image = self.resize_keep_aspect_ratio(
                    image=processed_image,
                    max_width=max_width,
                    max_height=max_height,
                )

                processed_image = self.apply_enhancements(
                    image=processed_image,
                    contrast_factor=contrast_factor,
                    sharpness_factor=sharpness_factor,
                    brightness_factor=brightness_factor,
                )

                processed_image = self.prepare_image_for_format(
                    image=processed_image,
                    output_format=output_format,
                )

                result_width = processed_image.width
                result_height = processed_image.height

                pillow_format = self.get_pillow_save_format(output_format)
                save_options = self.get_save_options(output_format, quality)

                processed_image.save(
                    output_path,
                    format=pillow_format,
                    **save_options,
                )

        except OSError as error:
            raise OptimizationError("Problems with optimization.") from error

        processed_size = get_file_size(output_path)
        return ImageOptimizeResult(
            output_path=output_path,
            size_info=SizeInfo(
                original_size=original_size,
                processed_size=processed_size,
                saved_percent=calculate_saved_percent(
                    original_size=original_size,
                    processed_size=processed_size,
                ),
            ),
            output_format=output_format,
            width=result_width,
            height=result_height,
        )
