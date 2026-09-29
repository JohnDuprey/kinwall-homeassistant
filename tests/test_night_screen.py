"""Night screen: a switch per wall screen and one for all of them, and the kinwall.night_screen action."""
import pytest
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kinwall.const import DOMAIN

from .test_setup import BASE_URL, _mock_full_refresh

URL = f"{BASE_URL}/api/displays/night-screen"
LATER = "2099-01-01T00:00:00.000Z"


def _state(all_on=False, hallway_on=False, hallway_until=LATER):
    on = {"on": True, "since": "2026-09-29T08:00:00.000Z", "until": LATER}
    return {
        "all": on if all_on else None,
        "displays": [
            {"id": "d1", "name": "Hallway", "owner": "shared", "on": all_on or hallway_on, "since": None, "until": hallway_until if (all_on or hallway_on) else None},
            {"id": "d2", "name": "Kitchen", "owner": "shared", "on": all_on, "since": None, "until": LATER if all_on else None},
        ],
    }


async def _setup(hass, aioclient_mock, state=None):
    aioclient_mock.get(URL, json=state or _state())  # before the defaults: the first match wins
    _mock_full_refresh(aioclient_mock)
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh1"})
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "key"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


def _posts(aioclient_mock):
    return [call[2] for call in aioclient_mock.mock_calls if call[0] == "POST" and str(call[1]) == URL]


async def test_switches_reflect_the_state(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, _state(hallway_on=True))
    assert hass.states.get("switch.family_night_screen").state == "off"
    assert hass.states.get("switch.hallway_night_screen").state == "on"
    assert hass.states.get("switch.kitchen_night_screen").state == "off"


async def test_a_run_out_on_counts_as_off(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, _state(hallway_on=True, hallway_until="2000-01-01T00:00:00.000Z"))
    assert hass.states.get("switch.hallway_night_screen").state == "off"


async def test_switches_start_and_end_it(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(URL, json=_state(all_on=True))
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.family_night_screen"}, blocking=True)
    assert _posts(aioclient_mock)[-1] == {"on": True}
    assert hass.states.get("switch.family_night_screen").state == "on"
    assert hass.states.get("switch.kitchen_night_screen").state == "on"

    aioclient_mock.clear_requests()
    aioclient_mock.post(URL, json=_state(all_on=True))
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.hallway_night_screen"}, blocking=True)
    assert _posts(aioclient_mock)[-1] == {"on": False, "displays": ["d1"]}


async def test_action_targets_all_or_chosen_wall_screens(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(URL, json=_state(all_on=True))
    response = await hass.services.async_call(DOMAIN, "night_screen", {"on": True}, blocking=True, return_response=True)
    assert response["all"]["on"] is True
    assert _posts(aioclient_mock)[-1] == {"on": True}

    # Wall screens by their switch, by name or by Kinwall's display ID; hours passes through.
    await hass.services.async_call(DOMAIN, "night_screen", {"on": True, "displays": ["switch.hallway_night_screen", "Kitchen"], "hours": 4}, blocking=True, return_response=True)
    assert _posts(aioclient_mock)[-1] == {"on": True, "displays": ["d1", "d2"], "hours": 4}
    await hass.services.async_call(DOMAIN, "night_screen", {"on": False, "displays": "d2"}, blocking=True, return_response=True)
    assert _posts(aioclient_mock)[-1] == {"on": False, "displays": ["d2"]}
    await hass.services.async_call(DOMAIN, "night_screen", {"on": False, "displays": []}, blocking=True, return_response=True)
    assert _posts(aioclient_mock)[-1] == {"on": False}, "an empty list (the blueprint's default) means every wall screen"

    with pytest.raises(HomeAssistantError, match="Garage"):
        await hass.services.async_call(DOMAIN, "night_screen", {"on": True, "displays": ["Garage"]}, blocking=True, return_response=True)


async def test_action_explains_a_display_key(hass, aioclient_mock):
    await _setup(hass, aioclient_mock)
    aioclient_mock.post(URL, status=403, json={"error": "display key cannot access this route"})
    with pytest.raises(HomeAssistantError, match="admin key"):
        await hass.services.async_call(DOMAIN, "night_screen", {"on": True}, blocking=True, return_response=True)


async def test_older_server_has_no_switches(hass, aioclient_mock):
    """A server without the endpoint (or a display key) just gets no Night screen switches."""
    _mock_full_refresh(aioclient_mock)  # 404 for the Night screen, like a server older than 1.1.0
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh1"})
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "key"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("switch.family_night_screen") is None
    assert hass.states.get("sensor.alice_points_today") is not None
