from io import BytesIO

import pytest
from fastapi import UploadFile

from app.application.upload_validation import read_validated_upload
from app.core.errors import UploadValidationError


@pytest.mark.asyncio
async def test_upload_validation_rejects_empty_file():
    upload = UploadFile(filename="empty.csv", file=BytesIO(b""), headers={"content-type": "text/csv"})

    with pytest.raises(UploadValidationError, match="empty"):
        await read_validated_upload(upload)


@pytest.mark.asyncio
async def test_upload_validation_does_not_use_path_in_filename():
    upload = UploadFile(
        filename="../../customers.csv",
        file=BytesIO(b"name,age\nAda,31\n"),
        headers={"content-type": "text/csv"},
    )

    validated = await read_validated_upload(upload)
    try:
        assert validated.original_filename == "customers.csv"
        assert validated.size_bytes > 0
    finally:
        validated.stream.close()
