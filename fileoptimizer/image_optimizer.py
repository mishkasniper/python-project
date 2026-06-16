import os
import PIL
from pathlib import Path
from exceptions import UnsupportedFormatError



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
        """Проверяет параметра и возвращает их нормализованный вид."""
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



        

