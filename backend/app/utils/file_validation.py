from app.core.exceptions import AppException

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "markdown",
    "text/x-markdown": "markdown",
}

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB


def validate_upload(filename: str, content_type: str | None, size_bytes: int) -> str:
    """Returns the normalized source_type string, or raises AppException."""
    if size_bytes > MAX_FILE_SIZE_BYTES:
        raise AppException(f"File exceeds the {MAX_FILE_SIZE_BYTES // (1024*1024)}MB upload limit.", 413, "file_too_large")

    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    ext_map = {"pdf": "pdf", "docx": "docx", "txt": "txt", "md": "markdown", "markdown": "markdown"}

    if content_type in ALLOWED_MIME_TYPES:
        return ALLOWED_MIME_TYPES[content_type]
    if extension in ext_map:
        return ext_map[extension]

    raise AppException(
        "Unsupported file type. Allowed: PDF, DOCX, TXT, Markdown.", 415, "unsupported_file_type"
    )
