import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 11: API Contract Testing

    ## Why does this exist?

    Your payment system calls Stripe, Adyen, or an internal payments API.
    The provider changes their response shape — drops a field, changes a type.
    Your code hits production, tries to access a field that no longer exists,
    and crashes with an unhandled exception.

    **Without contract testing:** The breakage reaches production. Payments fail.
    On-call gets paged. Revenue is lost.

    **With contract testing:** CI catches the schema drift before deploy.
    You get a clear error: "provider response missing required field `status`."
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## What is a Contract?

    A **contract** is the agreed shape of a request or response between two systems.

    In fintech integrations, contracts matter because:
    - You don't own the provider — they can change their API without warning
    - HTTP responses are untyped by default — JSON accepts anything
    - Bugs appear far from the source — the field is missing in the response,
      but the crash happens three function calls later in business logic

    A Pydantic schema is an executable contract. It validates at parse time,
    not at use time.
    """)
    return


@app.cell
def _():
    from datetime import datetime
    from decimal import Decimal

    from pydantic import BaseModel, ValidationError

    # The contract for what we expect back from the provider
    class ChargeResponse(BaseModel):
        id: str
        amount: Decimal
        currency: str
        status: str
        created_at: datetime

    # A well-formed response — passes
    valid = {
        "id": "ch_abc123",
        "amount": "50.00",
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    charge = ChargeResponse.model_validate(valid)
    print(f"Valid response parsed: id={charge.id}, amount={charge.amount}, status={charge.status}")
    return ChargeResponse, Decimal, ValidationError, charge, datetime, valid


@app.cell
def _(mo):
    mo.md("""
    ## Breaking vs Non-Breaking Changes

    | Change | Breaking? | Why |
    |--------|-----------|-----|
    | Remove required field | Yes | Existing clients crash |
    | Change field type | Yes | Type coercion fails or corrupts data |
    | Add required field | Yes | Existing clients don't send it |
    | Add optional field | No | Clients ignore it safely |
    | Add new endpoint | No | Existing clients don't call it |
    | Rename a field | Yes | Old name no longer present |

    Contract tests verify your assumptions about which fields exist and what types they carry.
    """)
    return


@app.cell
def _(ChargeResponse, ValidationError):
    # Breaking change 1: missing required field
    broken_missing_field = {
        "id": "ch_broken",
        "amount": "50.00",
        "currency": "USD",
        # "status" removed by provider — breaking change
        "created_at": "2024-01-01T00:00:00+00:00",
    }

    try:
        ChargeResponse.model_validate(broken_missing_field)
        print("ERROR: should have raised")
    except ValidationError as e:
        print("Caught breaking change (missing field):")
        for err in e.errors():
            print(f"  field={err['loc']}, msg={err['msg']}")
    return (broken_missing_field,)


@app.cell
def _(ChargeResponse, ValidationError):
    # Breaking change 2: wrong type
    broken_wrong_type = {
        "id": "ch_broken",
        "amount": "not_a_number",   # provider changed type
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2024-01-01T00:00:00+00:00",
    }

    try:
        ChargeResponse.model_validate(broken_wrong_type)
        print("ERROR: should have raised")
    except ValidationError as e:
        print("Caught breaking change (wrong type):")
        for err in e.errors():
            print(f"  field={err['loc']}, msg={err['msg']}")
    return (broken_wrong_type,)


@app.cell
def _(ChargeResponse):
    # Non-breaking change: provider adds a new optional field
    response_with_extra = {
        "id": "ch_extra",
        "amount": "50.00",
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2024-01-01T00:00:00+00:00",
        "risk_score": 0.02,          # new field added by provider
        "processor_id": "proc_xyz",  # another new field
    }

    charge = ChargeResponse.model_validate(response_with_extra)
    print(f"Non-breaking change handled safely: id={charge.id}")
    print("Extra fields ignored — client continues working")
    return (charge,)


@app.cell
def _(mo):
    mo.md("""
    ## The Contract Test Pattern

    ```
    1. Start the provider (real or fake)
    2. Make a real HTTP request via your client
    3. Parse the response through your Pydantic schema
    4. If parsing fails → contract violation detected
    5. If parsing succeeds → response matches contract
    ```

    The key insight: **the test doesn't assert business logic**.
    It asserts that the provider speaks the same language as your client.

    Use `httpx.ASGITransport` to run a FastAPI app in-process — no network,
    no ports, full integration fidelity.
    """)
    return


@app.cell
def _():
    import asyncio
    import os

    # Import the fake provider and client
    import sys
    from decimal import Decimal

    from httpx import ASGITransport, AsyncClient
    sys.path.insert(0, os.path.dirname(__file__))

    from client import ProviderClient
    from provider import app as provider_app

    async def demo_contract_test():
        transport = ASGITransport(app=provider_app)
        async with AsyncClient(transport=transport, base_url="http://test") as http:
            client = ProviderClient(http)

            # Happy path — provider response matches contract
            charge = await client.create_charge(
                amount=Decimal("99.99"),
                currency="GBP",
                source="tok_gb_debit",
                description="Lab 11 demo",
            )
            print(f"Charge created: id={charge.id}, amount={charge.amount} {charge.currency}")
            print(f"Status: {charge.status}, created_at: {charge.created_at}")

            # Refund — chained call
            refund = await client.create_refund(
                charge_id=charge.id,
                amount=Decimal("49.99"),
            )
            print(f"Refund created: id={refund.id}, charge_id={refund.charge_id}")
            print(f"Refund amount: {refund.amount}, status: {refund.status}")

    asyncio.run(demo_contract_test())
    return (
        ASGITransport,
        AsyncClient,
        Decimal,
        ProviderClient,
        asyncio,
        demo_contract_test,
        os,
        provider_app,
        sys,
    )


@app.cell
def _(mo):
    mo.md("""
    ## Defensive Parsing

    Pydantic validates at the boundary — when the HTTP response comes in,
    before the data reaches any business logic.

    This is the correct layering:

    ```
    HTTP Response (raw JSON)
         ↓
    ChargeResponse.model_validate(data)   ← contract check here
         ↓
    Business logic (amount, status, etc.) ← never sees bad data
    ```

    Without this: your business logic receives `None` where it expected a `Decimal`,
    and the error message is "unsupported operand type(s) for +: 'NoneType' and 'Decimal'"
    — far from where the actual problem is.

    With contract tests: "ValidationError: status field required" — exact and actionable.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    **What I built:**
    - Pydantic schemas as executable contracts for a payment provider API
    - A fake FastAPI provider with `/v1/charges` and `/v1/refunds`
    - A typed client that validates every response against the contract
    - 7 tests covering happy paths, breaking changes, and non-breaking changes

    **What this proves to an employer:**
    > "Built API contract test suite for payment provider integration, detecting
    > schema drift before production. Caught missing required fields and type
    > changes in CI rather than in production."

    **When to use this in a real job:**
    - Any integration with an external payment provider (Stripe, Adyen, Checkout.com)
    - Internal service boundaries in a microservices payment platform
    - When upgrading a provider SDK — verify the new version's response shape

    **Confidence score: 9/10**
    The pattern is simple and the value is clear. The gap is that real-world
    contract testing (e.g., Pact) also verifies the provider side — here we
    own both sides since we wrote the fake provider.
    """)
    return


if __name__ == "__main__":
    app.run()
