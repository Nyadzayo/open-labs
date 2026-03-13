"""Tests for KYC document validation pipeline."""

from __future__ import annotations

import pytest
from models import (
    DocumentState,
    InvalidDocumentTransition,
    transition_document,
)
from pipeline import validate_document

# Validation tests

def test_valid_pdf() -> None:
    result = validate_document("id.pdf", "application/pdf", 1024)
    assert result.valid is True


def test_valid_jpeg() -> None:
    result = validate_document("photo.jpg", "image/jpeg", 2048)
    assert result.valid is True


def test_unsupported_type() -> None:
    result = validate_document("doc.exe", "application/exe", 1024)
    assert result.valid is False
    assert "Unsupported" in result.reason


def test_empty_file() -> None:
    result = validate_document("empty.pdf", "application/pdf", 0)
    assert result.valid is False
    assert "Empty" in result.reason


def test_file_too_large() -> None:
    result = validate_document("big.pdf", "application/pdf", 20 * 1024 * 1024)
    assert result.valid is False
    assert "too large" in result.reason


def test_missing_filename() -> None:
    result = validate_document("", "application/pdf", 1024)
    assert result.valid is False
    assert "filename" in result.reason.lower()


# State machine tests

def test_uploaded_to_validating() -> None:
    result = transition_document(DocumentState.UPLOADED, DocumentState.VALIDATING)
    assert result == DocumentState.VALIDATING


def test_validating_to_approved() -> None:
    result = transition_document(DocumentState.VALIDATING, DocumentState.APPROVED)
    assert result == DocumentState.APPROVED


def test_validating_to_rejected() -> None:
    result = transition_document(DocumentState.VALIDATING, DocumentState.REJECTED)
    assert result == DocumentState.REJECTED


def test_rejected_to_uploaded() -> None:
    """Can re-upload after rejection."""
    result = transition_document(DocumentState.REJECTED, DocumentState.UPLOADED)
    assert result == DocumentState.UPLOADED


def test_approved_is_terminal() -> None:
    with pytest.raises(InvalidDocumentTransition):
        transition_document(DocumentState.APPROVED, DocumentState.UPLOADED)


def test_uploaded_to_approved_invalid() -> None:
    """Can't skip validation."""
    with pytest.raises(InvalidDocumentTransition):
        transition_document(DocumentState.UPLOADED, DocumentState.APPROVED)
