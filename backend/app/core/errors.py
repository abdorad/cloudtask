from dataclasses import dataclass


@dataclass
class CloudTaskError(Exception):
    message: str
    status_code: int = 400


class UploadValidationError(CloudTaskError):
    def __init__(self, message: str):
        super().__init__(message, 422)


class NotFoundError(CloudTaskError):
    def __init__(self, message: str = "Task was not found"):
        super().__init__(message, 404)


class SubmissionError(CloudTaskError):
    def __init__(self, message: str = "The task could not be queued. Please try again."):
        super().__init__(message, 503)


class CsvAnalysisError(Exception):
    """A permanent, user-correctable CSV content error."""


class RetryableProcessingError(Exception):
    """An infrastructure error for which the worker may retry."""
