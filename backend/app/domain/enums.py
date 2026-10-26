from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingType(StrEnum):
    CSV_ANALYSIS = "CSV_ANALYSIS"
