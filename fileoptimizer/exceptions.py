class FileOptimizerError(Exception):
    """Base exception for all file optimizer errors."""


class UnsupportedFormatError(FileOptimizerError):
    """Raised when the file format is not supported."""


class OptimizationError(FileOptimizerError):
    """Raised when file optimization fails."""