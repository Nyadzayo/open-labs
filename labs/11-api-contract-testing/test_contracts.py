"""Contract tests for payment provider API."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from decimal import Decimal
from typing import Any

import pytest
from client import ProviderClient
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from schemas import ChargeResponse, RefundResponse


@pytest.fixture
async def provider_app() -> Any:
    from provider import app
    return app


@pytest.fixture
async def http_client(provider_app: Any) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=provider_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def provider(http_client: AsyncClient) -> ProviderClient:
    return ProviderClient(http_client)


@pytest.mark.asyncio
async def test_charge_matches_contract(provider: ProviderClient) -> None:
    """Provider charge response matches ChargeResponse schema."""
    charge = await provider.create_charge(
        amount=Decimal("50.00"), currency="USD", source="tok_visa"
    )
    assert isinstance(charge, ChargeResponse)
    assert charge.amount == Decimal("50.00")
    assert charge.currency == "USD"
    assert charge.status == "succeeded"


@pytest.mark.asyncio
async def test_refund_matches_contract(provider: ProviderClient) -> None:
    """Provider refund response matches RefundResponse schema."""
    charge = await provider.create_charge(
        amount=Decimal("50.00"), currency="USD", source="tok_visa"
    )
    refund = await provider.create_refund(
        charge_id=charge.id, amount=Decimal("25.00")
    )
    assert isinstance(refund, RefundResponse)
    assert refund.charge_id == charge.id
    assert refund.amount == Decimal("25.00")


@pytest.mark.asyncio
async def test_charge_has_required_fields(provider: ProviderClient) -> None:
    """All required fields present in charge response."""
    charge = await provider.create_charge(
        amount=Decimal("100.00"), currency="EUR", source="tok_mastercard"
    )
    assert charge.id is not None
    assert charge.created_at is not None


@pytest.mark.asyncio
async def test_broken_response_missing_field(http_client: AsyncClient) -> None:
    """Demonstrates catching a breaking change: missing required field."""
    # Simulate provider returning response without 'status' field
    broken_response = {
        "id": "ch_broken",
        "amount": "50.00",
        "currency": "USD",
        # "status" is missing — breaking change!
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    with pytest.raises(ValidationError, match="status"):
        ChargeResponse.model_validate(broken_response)


@pytest.mark.asyncio
async def test_broken_response_wrong_type(http_client: AsyncClient) -> None:
    """Demonstrates catching a breaking change: field type changed."""
    broken_response = {
        "id": "ch_broken",
        "amount": "not_a_number",  # Was Decimal, now string
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2024-01-01T00:00:00+00:00",
    }
    with pytest.raises(ValidationError):
        ChargeResponse.model_validate(broken_response)


@pytest.mark.asyncio
async def test_optional_field_accepted(provider: ProviderClient) -> None:
    """Adding an optional field is a non-breaking change."""
    charge = await provider.create_charge(
        amount=Decimal("50.00"),
        currency="USD",
        source="tok_visa",
        description="Test payment",
    )
    assert isinstance(charge, ChargeResponse)


@pytest.mark.asyncio
async def test_extra_field_ignored(http_client: AsyncClient) -> None:
    """Provider adding new fields shouldn't break our client."""
    response_with_extra = {
        "id": "ch_extra",
        "amount": "50.00",
        "currency": "USD",
        "status": "succeeded",
        "created_at": "2024-01-01T00:00:00+00:00",
        "new_field": "surprise!",  # Provider added a new field
    }
    # Should not raise — extra fields are ignored by default
    charge = ChargeResponse.model_validate(response_with_extra)
    assert charge.id == "ch_extra"
