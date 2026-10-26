import csv
import io
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.errors import CsvAnalysisError


@dataclass
class NumericSummary:
    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)

    def as_dict(self) -> dict[str, float | int]:
        return {
            "count": self.count,
            "min": self.minimum,
            "max": self.maximum,
            "mean": self.total / self.count,
        }


@dataclass
class ColumnProfile:
    missing_values: int = 0
    non_empty_values: int = 0
    non_numeric_values: int = 0
    all_integers: bool = True
    numeric_summary: NumericSummary = field(default_factory=NumericSummary)

    def add(self, raw_value: str | None) -> None:
        value = (raw_value or "").strip()
        if not value:
            self.missing_values += 1
            return
        self.non_empty_values += 1
        try:
            numeric_value = float(value)
        except ValueError:
            self.non_numeric_values += 1
            return
        if not math.isfinite(numeric_value):
            self.non_numeric_values += 1
            return
        if not numeric_value.is_integer():
            self.all_integers = False
        self.numeric_summary.add(numeric_value)

    @property
    def estimated_type(self) -> str:
        if self.non_empty_values == 0:
            return "unknown"
        if self.non_numeric_values:
            return "string"
        return "integer" if self.all_integers else "number"


def _reader_for_csv(content: bytes) -> csv.DictReader:
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise CsvAnalysisError("The CSV must be encoded as UTF-8") from error
    if not decoded.strip():
        raise CsvAnalysisError("The CSV file is empty")
    sample = decoded[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(decoded), dialect=dialect)
    if not reader.fieldnames:
        raise CsvAnalysisError("The CSV must include a header row")
    headers = [header.strip() if header else "" for header in reader.fieldnames]
    if not all(headers) or len(headers) != len(set(header.casefold() for header in headers)):
        raise CsvAnalysisError("CSV header columns must be non-empty and unique")
    reader.fieldnames = headers
    return reader


def analyze_csv(content: bytes, task_id: str) -> dict:
    reader = _reader_for_csv(content)
    assert reader.fieldnames is not None
    profiles = {header: ColumnProfile() for header in reader.fieldnames}
    row_count = 0
    try:
        for row_number, row in enumerate(reader, start=2):
            if None in row or len(row) != len(reader.fieldnames):
                raise CsvAnalysisError(f"Row {row_number} has a different number of fields than the header")
            row_count += 1
            for header, profile in profiles.items():
                profile.add(row.get(header))
    except csv.Error as error:
        raise CsvAnalysisError("The CSV contains malformed rows") from error

    return {
        "taskId": task_id,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "rowCount": row_count,
        "columns": reader.fieldnames,
        "estimatedTypes": {header: profile.estimated_type for header, profile in profiles.items()},
        "missingValues": {header: profile.missing_values for header, profile in profiles.items()},
        "numericStatistics": {
            header: profile.numeric_summary.as_dict()
            for header, profile in profiles.items()
            if profile.estimated_type in {"integer", "number"} and profile.numeric_summary.count
        },
    }
