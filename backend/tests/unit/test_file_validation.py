"""Unit tests for file upload validation."""
import pytest
from app.core.exceptions import AppException
from app.utils.file_validation import validate_upload, MAX_FILE_SIZE_BYTES


@pytest.mark.parametrize("filename,content_type,expected", [
    ("report.pdf", "application/pdf", "pdf"),
    ("doc.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx"),
    ("notes.txt", "text/plain", "txt"),
    ("readme.md", "text/markdown", "markdown"),
    ("readme.markdown", None, "markdown"),
    ("notes.md", None, "markdown"),
    ("plain.txt", None, "txt"),
    ("doc.pdf", None, "pdf"),  # extension fallback
])
def test_valid_file_types(filename, content_type, expected):
    result = validate_upload(filename, content_type, 1024)
    assert result == expected


def test_rejects_file_exceeding_size_limit():
    with pytest.raises(AppException) as exc_info:
        validate_upload("big.pdf", "application/pdf", MAX_FILE_SIZE_BYTES + 1)
    assert exc_info.value.code == "file_too_large"
    assert exc_info.value.status_code == 413


def test_rejects_unsupported_mime_type():
    with pytest.raises(AppException) as exc_info:
        validate_upload("video.mp4", "video/mp4", 1000)
    assert exc_info.value.code == "unsupported_file_type"
    assert exc_info.value.status_code == 415


def test_rejects_unsupported_extension_with_no_mime():
    with pytest.raises(AppException) as exc_info:
        validate_upload("image.png", None, 1000)
    assert exc_info.value.code == "unsupported_file_type"


def test_accepts_file_exactly_at_size_limit():
    result = validate_upload("ok.pdf", "application/pdf", MAX_FILE_SIZE_BYTES)
    assert result == "pdf"


def test_rejects_file_with_no_extension_and_no_mime():
    with pytest.raises(AppException):
        validate_upload("noextension", None, 1000)
