"""Payment provider client."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from httpx import AsyncClient
from schemas import ChargeResponse, RefundResponse


class ProviderClient:
    def __init__(self, http_client: AsyncClient) -> None:
        self._client = http_client

    async def create_charge(
        self,
        amount: Decimal,
        currency: str,
        source: str,
        description: str | None = None,
    ) -> ChargeResponse:
        """Create a charge and validate response against contract."""
        params: dict[str, Any] = {
            "amount": str(amount),
            "currency": currency,
            "source": source,
        }
        if description:
            params["description"] = description
        resp = await self._client.post("/v1/charges", params=params)
        resp.raise_for_status()
        return ChargeResponse.model_validate(resp.json())

    async def create_refund(
        self, charge_id: str, amount: Decimal
    ) -> RefundResponse:
        """Create a refund and validate response against contract."""
        resp = await self._client.post(
            "/v1/refunds",
            params={"charge_id": charge_id, "amount": str(amount)},
        )
        resp.raise_for_status()
        return RefundResponse.model_validate(resp.json())
