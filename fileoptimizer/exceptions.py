class FileOptimizerError(Exception):
    """Base exception for all file optimizer errors."""


class UnsupportedFormatError(FileOptimizerError):
    """Raised when the file format is not supported."""


class OptimizationError(FileOptimizerError):
    """Raised when file optimization fails."""


class StorageError(FileOptimizerError):
    """Raised when an error occurs while working with temporary file storage."""


class ArchiveCreationError(FileOptimizerError):
    """Raised when archive creation fails."""
