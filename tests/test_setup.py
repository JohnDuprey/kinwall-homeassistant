"""End-to-end entry setup: registers the HA webhook and creates a Kinwall webhook."""
from homeassistant.const import CONF_API_KEY, CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kinwall.const import CONF_KINWALL_WEBHOOK_ID, CONF_WEBHOOK_ID, DOMAIN

BASE_URL = "http://kinwall.local:8080"


def _mock_full_refresh(aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[{"id": "m1", "name": "Alice", "pointsToday": 0, "pointsWeek": 0}])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])


async def test_setup_entry_registers_webhook(hass, aioclient_mock):
    _mock_full_refresh(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh_server_1"})

    hass.config.internal_url = "http://192.168.1.10:8123"

    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "fc_key"})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.data[CONF_KINWALL_WEBHOOK_ID] == "wh_server_1"
    assert entry.data[CONF_WEBHOOK_ID]

    assert hass.states.get("sensor.alice_points_today") is not None

    aioclient_mock.delete(f"{BASE_URL}/api/webhooks/wh_server_1", json={"ok": True})
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def test_private_host_detection() -> None:
    from custom_components.kinwall import _is_private_host

    for url in ("http://192.168.1.10:8080", "http://homeassistant.local:8080", "http://10.0.0.5", "http://localhost:8080", "http://[fd00::1]:8080", "http://100.64.0.1"):
        assert _is_private_host(url), url
    for url in ("https://duprey.kinwall.family", "http://8.8.8.8", "https://example.com:8443"):
        assert not _is_private_host(url), url


async def test_webhook_reregistered_when_ha_url_changes(hass, aioclient_mock):
    from custom_components.kinwall.const import CONF_KINWALL_WEBHOOK_SECRET, CONF_KINWALL_WEBHOOK_URL

    _mock_full_refresh(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh_new"})
    aioclient_mock.delete(f"{BASE_URL}/api/webhooks/wh_old", json={"ok": True})
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = MockConfigEntry(domain=DOMAIN, data={
        CONF_URL: BASE_URL, CONF_API_KEY: "fc_key", CONF_WEBHOOK_ID: "hook1",
        CONF_KINWALL_WEBHOOK_ID: "wh_old", CONF_KINWALL_WEBHOOK_SECRET: "s", CONF_KINWALL_WEBHOOK_URL: "http://10.0.0.1:8123/api/webhook/hook1",
    })
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.data[CONF_KINWALL_WEBHOOK_ID] == "wh_new"
    assert entry.data[CONF_KINWALL_WEBHOOK_URL] == "http://192.168.1.10:8123/api/webhook/hook1"
    assert any(m == "DELETE" and str(u).endswith("/api/webhooks/wh_old") for m, u, *_ in aioclient_mock.mock_calls)


async def test_chore_binary_sensor_reflects_todays_completion(hass, aioclient_mock):
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[{"id": "m1", "name": "Alice", "pointsToday": 0, "pointsWeek": 0}])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[
        {"id": "c1", "title": "After school checklist", "memberId": "m1", "points": 5, "active": True, "listId": "l1"},
        {"id": "c2", "title": "Bins", "memberId": "m1", "points": 5, "active": True, "listId": None},
    ])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[
        {"id": "c1", "title": "After school checklist", "memberId": "m1", "completed": True, "completedAt": "2026-09-28T20:00:00Z", "checklist": {"listId": "l1", "name": "After school", "total": 4, "done": 4}},
    ])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh"})
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "fc_key"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    done = hass.states.get("binary_sensor.alice_after_school_checklist")
    assert done is not None and done.state == "on"
    assert done.attributes["checklist_done"] == 4 and done.attributes["due_today"] is True
    bins = hass.states.get("binary_sensor.alice_bins")
    assert bins is not None and bins.state == "off" and bins.attributes["due_today"] is False
