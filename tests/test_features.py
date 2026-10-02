"""Kinwall's family feature switches: switched-off features have no entities and refuse actions."""
import pytest
from homeassistant.components.todo import TodoItem, TodoItemStatus
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kinwall.const import DOMAIN

BASE_URL = "http://kinwall.local:8080"


def _mock(aioclient_mock, rev: int, features: dict | None, rewards: bool | None = None):
    aioclient_mock.clear_requests()
    settings = {"features": features} if features is not None else {}
    if rewards is not None:
        settings["rewardsEnabled"] = rewards
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": rev, "revs": {"events": rev, "lists": 1, "chores": 1}})
    aioclient_mock.get(f"{BASE_URL}/api/settings", json=settings)
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[{"id": "m1", "name": "Alice", "pointsToday": 0, "pointsWeek": 0}])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[{"id": "c1", "title": "Bins", "memberId": "m1", "points": 5, "active": True}])
    aioclient_mock.get(f"{BASE_URL}/api/lists/l1", json={"list": {"id": "l1"}, "items": [], "groups": []})
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[{"id": "l1", "name": "Groceries", "kind": "shopping", "itemsRev": 1}])
    aioclient_mock.get(f"{BASE_URL}/api/displays/night-screen", status=404)
    aioclient_mock.post(f"{BASE_URL}/api/webhooks", json={"id": "wh1"})
    aioclient_mock.delete(f"{BASE_URL}/api/webhooks/wh1", json={"ok": True})


async def _setup(hass, aioclient_mock, features):
    _mock(aioclient_mock, 1, features)
    hass.config.internal_url = "http://192.168.1.10:8123"
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_URL: BASE_URL, CONF_API_KEY: "key"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


CHORE_ENTITIES = ("sensor.alice_points_today", "sensor.alice_points_this_week", "sensor.alice_chores_remaining_today", "binary_sensor.alice_bins", "todo.alice", "todo.family")


def _paths(aioclient_mock) -> set[str]:
    return {str(url.path) for _, url, _, _ in aioclient_mock.mock_calls}


async def test_everything_on_with_a_server_that_has_no_switches(hass, aioclient_mock):
    await _setup(hass, aioclient_mock, None)
    for entity_id in (*CHORE_ENTITIES, "todo.family_groceries"):
        assert hass.states.get(entity_id) is not None, entity_id


async def test_switched_off_features_get_no_entities_and_are_not_fetched(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, {"chores": False, "lists": False, "checkIns": True})
    for entity_id in (*CHORE_ENTITIES, "todo.family_groceries"):
        assert hass.states.get(entity_id) is None, entity_id
    assert not _paths(aioclient_mock) & {"/api/chores", "/api/chores/day", "/api/lists", "/api/lists/l1"}
    assert hass.states.get("calendar.family") is not None
    assert hass.data[DOMAIN][entry.entry_id].data.rewards_enabled is True  # missing = on


async def test_rewards_switch_is_read(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, {})
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _mock(aioclient_mock, 2, {}, rewards=False)
    await coordinator.async_refresh()
    assert coordinator.data.rewards_enabled is False


async def test_turning_a_feature_off_and_on_removes_and_brings_back_its_entities(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, {"chores": True})
    registry = er.async_get(hass)
    assert registry.async_get("sensor.alice_points_today") is not None

    _mock(aioclient_mock, 2, {"chores": False})
    await hass.data[DOMAIN][entry.entry_id].async_refresh()
    await hass.async_block_till_done()  # one reload
    for entity_id in CHORE_ENTITIES:
        assert hass.states.get(entity_id) is None, entity_id
        assert registry.async_get(entity_id) is None, entity_id  # not left behind as unavailable
    assert hass.states.get("todo.family_groceries") is not None

    _mock(aioclient_mock, 3, {"chores": True})
    await hass.data[DOMAIN][entry.entry_id].async_refresh()
    await hass.async_block_till_done()
    for entity_id in CHORE_ENTITIES:
        assert hass.states.get(entity_id) is not None, entity_id


async def test_other_switches_do_not_reload(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, {})
    coordinator = hass.data[DOMAIN][entry.entry_id]
    _mock(aioclient_mock, 2, {"paint": False, "meals": False})
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.data[DOMAIN][entry.entry_id] is coordinator  # same coordinator: no reload


async def test_actions_on_a_switched_off_feature_explain_why(hass, aioclient_mock):
    entry = await _setup(hass, aioclient_mock, {"meals": False})
    with pytest.raises(HomeAssistantError, match="Meals are turned off in Kinwall"):
        await hass.services.async_call(DOMAIN, "plan_meal", {"date": "2026-10-06", "title": "Soup"}, blocking=True, return_response=True)
    with pytest.raises(HomeAssistantError, match="Meals are turned off in Kinwall"):
        await hass.services.async_call(DOMAIN, "import_recipe", {"external_id": "a", "name": "Soup"}, blocking=True, return_response=True)

    # A chore to-do between the switch going off and the reload: unavailable, and refuses writes.
    from custom_components.kinwall.todo import KinwallChoreList

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.data.features = {"chores": False}
    entity = KinwallChoreList(coordinator, entry, "m1", "Alice")
    assert entity.available is False
    with pytest.raises(HomeAssistantError, match="Chores are turned off in Kinwall"):
        await entity.async_update_todo_item(TodoItem(uid="c1", summary="Bins", status=TodoItemStatus.COMPLETED))
