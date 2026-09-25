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
