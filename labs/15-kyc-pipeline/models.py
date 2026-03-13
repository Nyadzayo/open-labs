"""KYC document models and state machine."""

from __future__ import annotations

from enum import StrEnum


class DocumentState(StrEnum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


VALID_TRANSITIONS: dict[DocumentState, set[DocumentState]] = {
    DocumentState.UPLOADED: {DocumentState.VALIDATING},
    DocumentState.VALIDATING: {DocumentState.APPROVED, DocumentState.REJECTED},
    DocumentState.APPROVED: set(),
    DocumentState.REJECTED: {DocumentState.UPLOADED},  # Can re-upload
}


class InvalidDocumentTransition(Exception):
    """Raised when a document state transition is not allowed."""

    def __init__(self, from_state: DocumentState, to_state: DocumentState) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Invalid transition: {from_state} -> {to_state}")


def transition_document(
    current: DocumentState, target: DocumentState
) -> DocumentState:
    """Transition document state or raise InvalidDocumentTransition."""
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidDocumentTransition(current, target)
    return target
