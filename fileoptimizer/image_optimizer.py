from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

from exceptions import OptimizationError, UnsupportedFormatError


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
        """Проверяет параметры и возвращает их нормализованный вид."""
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
    def build_output_path(
        input_path: Path,
        output_dir: Path,
        output_format: str,
    ) -> Path:
        """Строит путь для выходного файла."""
        return output_dir / f"{input_path.stem}_optimized.{output_format}"

    @staticmethod
    def get_pillow_save_format(output_format: str) -> str:
        """Вовзращает формат для pillow для сохранения."""
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

    def optimize(
        self,
        input_path: Path,
        output_dir: Path,
        output_format: str = "webp",
        quality: int = 75,
        max_width: int | None = None,
        max_height: int | None = None,
        enhance_contrast: bool = False,
        enhance_sharpness: bool = False,
        enhance_brightness: bool = False,
    ) -> bool:
        """Оптимизирует фотографии и сохраняет ее.
        
        Args:
            input_path: Путь к исходной фотографии.
            output_dir: Путь к папке для сохраненния фотографии.
            output_format: Формат сохраненной фотографии. ["webp", "jpg", "png", "jpeg"]
            quality: качество от исходной фотографии. 1 <= quality <= 100
            max_width: максимальная ширина.
            max_height: максимальная высота.
            enhance_contrast: улучшения контраста.
            enhance_sharpness: улучшение остроты.
            enhance_brightness: улучшение яркости.

        Raises:
            TODO: исключение при отсутсвии/проблемами с файлом.
            TODO: исключение при ошибки во время оптимизации.
        """ 
        output_format = self._validate_optimize_params(
            input_path=input_path,
            output_dir=output_dir,
            output_format=output_format,
            quality=quality,
        )

        output_path = self.build_output_path(
            input_path=input_path,
            output_dir=output_dir,
            output_format=output_format,
        )

        try:
            with Image.open(input_path) as image:
                processed_image = ImageOps.exif_transpose(image)
                processed_image = self.prepare_image_for_format(
                    image=processed_image,
                    output_format=output_format,
                )

                pillow_format = self.get_pillow_save_format(output_format)
                save_options = self.get_save_options(output_format, quality)

                processed_image.save(
                    output_path,
                    format=pillow_format,
                    **save_options,
                )

        except OSError as error:
            raise OptimizationError("Problems with optimization.")

        return output_path
        

