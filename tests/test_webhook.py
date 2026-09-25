"""Push webhook handler: rejects a request with a bad HMAC signature."""
import hashlib
import hmac
import json

from homeassistant.const import CONF_API_KEY, CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kinwall import _handle_webhook
from custom_components.kinwall.const import (
    CONF_KINWALL_WEBHOOK_SECRET,
    CONF_WEBHOOK_ID,
    DOMAIN,
)


def _make_entry(hass, secret: str) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_URL: "http://kinwall.local:8080",
            CONF_API_KEY: "fc_key",
            CONF_WEBHOOK_ID: "wh1",
            CONF_KINWALL_WEBHOOK_SECRET: secret,
        },
    )
    entry.add_to_hass(hass)
    return entry


class _FakeRequest:
    """Just enough of aiohttp.web.Request for _handle_webhook: .headers and .read()."""

    def __init__(self, body: bytes, signature: str) -> None:
        self.headers = {"X-Kinwall-Signature": signature, "Content-Type": "application/json"}
        self._body = body

    async def read(self) -> bytes:
        return self._body


def _request(body: bytes, signature: str) -> _FakeRequest:
    return _FakeRequest(body, signature)


async def test_webhook_rejects_bad_signature(hass):
    _make_entry(hass, secret="s3cret")
    body = json.dumps({"type": "chore.completed", "data": {"id": "c1"}, "at": "2026-01-01T00:00:00.000Z"}).encode()

    resp = await _handle_webhook(hass, "wh1", _request(body, "sha256=deadbeef"))
    assert resp.status == 401


async def test_webhook_accepts_good_signature_and_fires_event(hass):
    secret = "s3cret"
    _make_entry(hass, secret=secret)
    body = json.dumps({"type": "chore.completed", "data": {"id": "c1"}, "at": "2026-01-01T00:00:00.000Z"}).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    events = []
    hass.bus.async_listen("kinwall_chore_completed", lambda event: events.append(event))

    resp = await _handle_webhook(hass, "wh1", _request(body, signature))
    await hass.async_block_till_done()

    assert resp.status == 200
    assert len(events) == 1
    assert events[0].data == {"id": "c1"}
