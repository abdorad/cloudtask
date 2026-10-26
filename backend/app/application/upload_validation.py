import csv
import io
import os
from dataclasses import dataclass
from tempfile import SpooledTemporaryFile

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import UploadValidationError

ALLOWED_CONTENT_TYPES = {"", "application/octet-stream", "application/vnd.ms-excel", "text/csv", "text/plain"}
PREVIEW_BYTES = 64 * 1024


@dataclass
class ValidatedUpload:
    original_filename: str
    size_bytes: int
    stream: SpooledTemporaryFile


def _safe_display_name(filename: str | None) -> str:
    basename = os.path.basename((filename or "").replace("\\", "/"))
    cleaned = "".join(character for character in basename if character.isprintable()).strip()
    return cleaned[:255] or "upload.csv"


def _validate_header(preview: bytes) -> None:
    if not preview:
        raise UploadValidationError("The CSV file is empty")
    first_line_end = preview.find(b"\n")
    header_bytes = preview if first_line_end == -1 else preview[: first_line_end + 1]
    try:
        header_text = header_bytes.decode("utf-8-sig")
        header = next(csv.reader(io.StringIO(header_text)), None)
    except (UnicodeDecodeError, csv.Error) as error:
        raise UploadValidationError("The file must be a UTF-8 CSV with a readable header") from error
    if not header or not any(column.strip() for column in header):
        raise UploadValidationError("The CSV file must include at least one header column")
    normalized = [column.strip().casefold() for column in header]
    if any(not column for column in normalized) or len(normalized) != len(set(normalized)):
        raise UploadValidationError("CSV header columns must be non-empty and unique")


async def read_validated_upload(upload: UploadFile) -> ValidatedUpload:
    filename = _safe_display_name(upload.filename)
    if not filename.casefold().endswith(".csv"):
        raise UploadValidationError("Only files with a .csv extension are accepted")
    if (upload.content_type or "").casefold() not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError("The uploaded file must be sent as CSV")

    stream = SpooledTemporaryFile(max_size=1024 * 1024, mode="w+b")
    preview = bytearray()
    size_bytes = 0
    try:
        while chunk := await upload.read(64 * 1024):
            size_bytes += len(chunk)
            if size_bytes > settings.upload_max_bytes:
                raise UploadValidationError(
                    f"The CSV exceeds the {settings.upload_max_bytes} byte upload limit"
                )
            stream.write(chunk)
            if len(preview) < PREVIEW_BYTES:
                preview.extend(chunk[: PREVIEW_BYTES - len(preview)])
        _validate_header(bytes(preview))
        stream.seek(0)
        return ValidatedUpload(filename, size_bytes, stream)
    except Exception:
        stream.close()
        raise
    finally:
        await upload.close()
