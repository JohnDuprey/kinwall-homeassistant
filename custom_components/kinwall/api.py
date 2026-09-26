"""Thin async client for the Kinwall API (see the kinwall repo's docs/integrations/rest-api.md)."""
from __future__ import annotations

import json
from typing import Any

from aiohttp import ClientSession, ClientTimeout


class KinwallAuthError(Exception):
    """Raised on 401 responses."""


class KinwallApiError(Exception):
    """Raised on other non-2xx responses. `reason` is the server's `error` field when it sent JSON."""

    def __init__(self, message: str, status: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.reason: str | None = None
        if body:
            try:
                parsed = json.loads(body)
                if isinstance(parsed, dict) and isinstance(parsed.get("error"), str):
                    self.reason = parsed["error"]
            except ValueError:
                pass


class KinwallClient:
    """Minimal REST client. JSON bodies are camelCase, matching the server."""

    def __init__(self, session: ClientSession, base_url: str, api_key: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key

    async def _request(
        self, method: str, path: str, *, json: dict[str, Any] | None = None, params: dict[str, Any] | None = None
    ) -> Any:
        url = f"{self._base_url}{path}"
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with self._session.request(
            method, url, headers=headers, json=json, params=params, timeout=ClientTimeout(total=15)
        ) as resp:
            if resp.status == 401:
                raise KinwallAuthError("invalid or expired API key")
            if resp.status >= 400:
                body = await resp.text()
                raise KinwallApiError(f"{method} {path} -> {resp.status}: {body}", resp.status, body)
            if resp.status == 204:
                return None
            return await resp.json()

    # -- system / settings -------------------------------------------------
    async def get_settings(self) -> dict[str, Any]:
        return await self._request("GET", "/api/settings")

    async def get_rev(self) -> int:
        data = await self._request("GET", "/api/rev")
        return data["rev"]

    # -- members -------------------------------------------------------
    async def get_members(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/members")

    # -- calendars / events ----------------------------------------------
    async def get_calendars(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/calendars")

    async def get_events(self, start: str, end: str, member_id: str | None = None) -> list[dict[str, Any]]:
        params = {"from": start, "to": end}
        if member_id:
            params["memberId"] = member_id
        return await self._request("GET", "/api/events", params=params)

    async def create_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/events", json=payload)

    async def update_event(self, event_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PATCH", f"/api/events/{event_id}", json=payload)

    async def delete_event(self, event_id: str) -> None:
        await self._request("DELETE", f"/api/events/{event_id}")

    # -- chores -------------------------------------------------------
    async def get_chores_day(self, date: str) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/chores/day", params={"date": date})

    async def create_chore(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", "/api/chores", json=payload)

    async def delete_chore(self, chore_id: str) -> None:
        await self._request("DELETE", f"/api/chores/{chore_id}")

    async def complete_chore(self, chore_id: str, date: str, member_id: str | None = None) -> None:
        payload: dict[str, Any] = {"date": date}
        if member_id:
            payload["memberId"] = member_id
        await self._request("POST", f"/api/chores/{chore_id}/complete", json=payload)

    async def uncomplete_chore(self, chore_id: str, date: str) -> None:
        await self._request("DELETE", f"/api/chores/{chore_id}/complete", params={"date": date})

    # -- lists -------------------------------------------------------
    async def get_lists(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/lists")

    async def get_list_detail(self, list_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/api/lists/{list_id}")

    async def create_list_items(self, list_id: str, items: dict[str, Any] | list[dict[str, Any]]) -> list[dict[str, Any]]:
        return await self._request("POST", f"/api/lists/{list_id}/items", json=items)

    async def update_list_item(self, list_id: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("PATCH", f"/api/lists/{list_id}/items/{item_id}", json=payload)

    async def delete_list_item(self, list_id: str, item_id: str) -> None:
        await self._request("DELETE", f"/api/lists/{list_id}/items/{item_id}")

    async def reorder_list_items(self, list_id: str, item_ids: list[str]) -> None:
        await self._request("POST", f"/api/lists/{list_id}/reorder", json={"itemIds": item_ids})

    async def clear_completed_list_items(self, list_id: str) -> dict[str, Any]:
        return await self._request("POST", f"/api/lists/{list_id}/clear-completed")

    # -- webhooks (admin only) --------------------------------------------
    async def create_webhook(self, url: str, secret: str, events: list[str]) -> dict[str, Any]:
        payload = {"url": url, "secret": secret, "events": events}
        return await self._request("POST", "/api/webhooks", json=payload)

    async def delete_webhook(self, webhook_id: str) -> None:
        await self._request("DELETE", f"/api/webhooks/{webhook_id}")
