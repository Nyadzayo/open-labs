"""Lab 15: KYC Document Pipeline — marimo notebook."""

import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # Lab 15: KYC Document Pipeline

    **Role**: Fintech Backend / Compliance Engineering
    **Tier**: 2 — App + Pipeline Logic

    ---

    ## Why KYC?

    **Know Your Customer (KYC)** is a legal obligation under AML (Anti-Money Laundering) laws.
    Every financial services company — banks, neobanks, payment processors, exchanges — must verify
    customer identity before allowing financial transactions.

    **Regulatory frameworks requiring KYC:**
    - Bank Secrecy Act (BSA) — USA
    - 5th Anti-Money Laundering Directive (5AMLD) — EU
    - FCA regulations — UK
    - FinCEN rules — USA

    **Business cost of non-compliance:** Fines up to $1B+ (see HSBC 2012: $1.9B fine).

    **What KYC requires:**
    - Identity document collection (passport, national ID, driver's license)
    - Document validation (authentic, readable, not expired)
    - Audit trail of every submission and decision
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Pipeline Pattern

    A **pipeline** is a sequence of processing stages where each stage transforms data
    and passes it to the next. Think Unix pipes: `upload | validate | decide`.

    ```
    Customer Upload
         │
         ▼
    [UPLOADED] ──────► [VALIDATING] ──► [APPROVED]
                                   └──► [REJECTED] ──► [UPLOADED] (re-upload)
    ```

    **Why a pipeline over a single function?**
    - Each stage is independently testable
    - State is auditable at each transition
    - Failures are localised (validation fails, not the whole system)
    - Easy to add stages (OCR check, liveness detection, sanctions screening)
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Document Validation Rules

    Validation is the first gate. Rules are intentionally simple in this lab but
    map directly to real compliance requirements:

    | Rule | Reason |
    |------|--------|
    | Allowed types: PDF, JPEG, PNG | Prevent executable uploads; ensure readability |
    | Max size: 10MB | Prevent storage abuse; most ID scans are <5MB |
    | Non-empty file | Empty upload = processing error |
    | Non-empty filename | Required for audit trail and case reference |

    In production, additional checks include:
    - Image quality (DPI, blur detection)
    - Document expiry date extraction via OCR
    - Face match against selfie (biometric check)
    - Sanctions list screening
    """)
    return


@app.cell
def _():
    # Demonstrate validation rules
    import sys
    sys.path.insert(0, ".")
    from pipeline import ALLOWED_TYPES, MAX_SIZE, validate_document

    cases = [
        ("passport.pdf", "application/pdf", 1024 * 500),
        ("id.jpg", "image/jpeg", 1024 * 2048),
        ("selfie.png", "image/png", 1024 * 3000),
        ("virus.exe", "application/exe", 1024),
        ("empty.pdf", "application/pdf", 0),
        ("huge.pdf", "application/pdf", 20 * 1024 * 1024),
        ("", "application/pdf", 1024),
    ]

    results = []
    for filename, ct, size in cases:
        r = validate_document(filename, ct, size)
        results.append({
            "file": filename or "(empty)",
            "type": ct,
            "size_kb": size // 1024,
            "valid": r.valid,
            "reason": r.reason,
        })

    return ALLOWED_TYPES, MAX_SIZE, cases, ct, filename, r, results, size, sys, validate_document


@app.cell
def _(mo):
    mo.md("""
    ## State Machine

    A **state machine** enforces valid transitions between document states.
    Invalid transitions raise an exception — this prevents bugs like skipping validation
    or approving a document that was never reviewed.

    ### Transition table

    | From | To | Allowed? | Reason |
    |------|----|----------|--------|
    | UPLOADED | VALIDATING | Yes | Normal flow |
    | VALIDATING | APPROVED | Yes | Validation passed |
    | VALIDATING | REJECTED | Yes | Validation failed |
    | REJECTED | UPLOADED | Yes | Customer can re-submit |
    | APPROVED | anything | No | Terminal state |
    | UPLOADED | APPROVED | No | Can't skip validation |

    **Why enforce transitions in code?**
    - State machines make illegal states unrepresentable
    - Easier to audit: every state change is intentional
    - Prevents race conditions in async workflows
    """)
    return


@app.cell
def _():
    from models import DocumentState, InvalidDocumentTransition, transition_document

    # Walk through the happy path
    states = []
    current = DocumentState.UPLOADED
    states.append(current)

    current = transition_document(current, DocumentState.VALIDATING)
    states.append(current)

    current = transition_document(current, DocumentState.APPROVED)
    states.append(current)

    print("Happy path:", " → ".join(states))

    # Demonstrate rejection path
    rej_states = []
    s = DocumentState.UPLOADED
    rej_states.append(s)
    s = transition_document(s, DocumentState.VALIDATING)
    rej_states.append(s)
    s = transition_document(s, DocumentState.REJECTED)
    rej_states.append(s)
    s = transition_document(s, DocumentState.UPLOADED)
    rej_states.append(s)

    print("Rejection + re-upload path:", " → ".join(rej_states))

    # Demonstrate invalid transition
    try:
        transition_document(DocumentState.APPROVED, DocumentState.UPLOADED)
    except InvalidDocumentTransition as e:
        print(f"Blocked: {e}")

    return (
        DocumentState,
        InvalidDocumentTransition,
        current,
        rej_states,
        s,
        states,
        transition_document,
    )


@app.cell
def _(mo):
    mo.md("""
    ## Live Demo: Pipeline in Action

    Simulating the full pipeline flow: create document, validate, transition to final state.
    """)
    return


@app.cell
async def _():
    import asyncio
    import os
    import tempfile

    from db import create_document, get_document, init_db, update_document_status
    from models import DocumentState
    from pipeline import validate_document

    # Use a temp DB for demo
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as f:
        demo_db = f.name

    await init_db(demo_db)

    async def process_document(customer_id, filename, content_type, size_bytes):
        doc = await create_document(demo_db, customer_id, filename, content_type, size_bytes)
        await update_document_status(demo_db, doc["id"], DocumentState.VALIDATING)
        result = validate_document(filename, content_type, size_bytes)
        if result.valid:
            await update_document_status(demo_db, doc["id"], DocumentState.APPROVED)
        else:
            await update_document_status(demo_db, doc["id"], DocumentState.REJECTED, result.reason)
        doc_record = await get_document(demo_db, doc["id"])
        return doc_record

    # Process a valid doc
    valid_result = await process_document("cust_001", "passport.pdf", "application/pdf", 500_000)
    print(f"Valid doc: id={valid_result['id']}, status={valid_result['status']}")

    # Process an invalid doc
    invalid_result = await process_document("cust_002", "virus.exe", "application/exe", 1024)
    print(f"Invalid doc: id={invalid_result['id']}, status={invalid_result['status']}, reason={invalid_result['rejection_reason']}")

    os.unlink(demo_db)
    return (
        asyncio,
        create_document,
        demo_db,
        f,
        get_document,
        init_db,
        invalid_result,
        os,
        process_document,
        tempfile,
        update_document_status,
        valid_result,
        validate_document,
    )


@app.cell
def _(mo):
    mo.md("""
    ## Compliance Context: Audit Trail

    Every state change is stored with a timestamp and reason. This is the **audit trail** —
    a non-negotiable requirement in regulated fintech.

    **What regulators require:**
    - Who submitted the document (customer_id)
    - When it was submitted (created_at)
    - What was submitted (filename, content_type, size)
    - What decision was made (status)
    - Why it was rejected (rejection_reason)
    - When the decision was made (updated_at)

    **This lab stores all of it in SQLite.** In production:
    - Immutable audit log (append-only, never update)
    - Event sourcing (every state change is an event)
    - Encrypted at rest (PII protection)
    - Retention policy (e.g., 7 years under BSA)

    **API surface:**
    ```
    POST /documents         — Upload + validate
    GET  /documents/{id}    — Query status + rejection reason
    GET  /health            — Liveness probe
    ```
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    **What this lab demonstrates:**
    - Document validation pipeline with clear separation of concerns
    - State machine that enforces legal compliance workflows
    - Async FastAPI + SQLite persistence
    - Audit trail: every document decision is stored with reason and timestamp

    **What a real KYC system adds:**
    - OCR + machine learning for document data extraction
    - Liveness/selfie matching (biometric verification)
    - Third-party identity verification services (Jumio, Onfido, Persona)
    - Sanctions and PEP (Politically Exposed Persons) screening
    - Risk scoring per customer
    - Manual review queue for edge cases

    ---

    **Confidence score: 8/10**

    The pipeline pattern, state machine enforcement, and audit trail storage are
    production-grade patterns. The validation rules are intentionally minimal for
    the lab scope. Real compliance engineers extend this with ML and third-party APIs.
    """)
    return


if __name__ == "__main__":
    app.run()
