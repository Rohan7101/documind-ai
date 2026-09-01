from typing import Any, Optional


class AppException(Exception):
    """Base application exception with structured error code and status."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = 400,
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details


class InvalidFileTypeException(AppException):
    def __init__(self, message: str = "Only PDF files are supported.") -> None:
        super().__init__(message=message, error_code="INVALID_FILE_TYPE", status_code=400)


class InvalidPDFException(AppException):
    def __init__(self, message: str = "The uploaded file does not have a valid PDF header signature.") -> None:
        super().__init__(message=message, error_code="INVALID_PDF", status_code=400)


class FileTooLargeException(AppException):
    def __init__(self, message: str = "File size exceeds the maximum allowed upload limit.") -> None:
        super().__init__(message=message, error_code="FILE_TOO_LARGE", status_code=413)


class DocumentNotFoundException(AppException):
    def __init__(self, message: str = "The requested document was not found.") -> None:
        super().__init__(message=message, error_code="DOCUMENT_NOT_FOUND", status_code=404)


class UploadFailedException(AppException):
    def __init__(self, message: str = "Failed to process and store the uploaded document.") -> None:
        super().__init__(message=message, error_code="UPLOAD_FAILED", status_code=500)


class DocumentExtractionException(AppException):
    def __init__(self, message: str = "Unable to extract text from the document.") -> None:
        super().__init__(message=message, error_code="DOCUMENT_EXTRACTION_FAILED", status_code=400)

