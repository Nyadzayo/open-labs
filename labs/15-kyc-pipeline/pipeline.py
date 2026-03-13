"""KYC document validation pipeline."""

from __future__ import annotations

from dataclasses import dataclass

ALLOWED_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@dataclass
class ValidationResult:
    valid: bool
    reason: str


def validate_document(
    filename: str, content_type: str, size_bytes: int
) -> ValidationResult:
    """Validate a KYC document."""
    if not filename:
        return ValidationResult(False, "Missing filename")
    if content_type not in ALLOWED_TYPES:
        return ValidationResult(
            False, f"Unsupported type: {content_type}"
        )
    if size_bytes == 0:
        return ValidationResult(False, "Empty file")
    if size_bytes > MAX_SIZE:
        return ValidationResult(
            False, f"File too large: {size_bytes} bytes (max {MAX_SIZE})"
        )
    return ValidationResult(True, "Document valid")
