"""Free time uses fresh server decisions, including when only the clock changes."""
from unittest.mock import AsyncMock

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kinwall.api import KinwallApiError, KinwallAuthError
from custom_components.kinwall.binary_sensor import KinwallFreeTimeSensor
from custom_components.kinwall.coordinator import KinwallCoordinator, KinwallData


@pytest.mark.parametrize(("reason", "locked", "expected"), [
    ("ready", False, True), ("routine", True, False), ("scheduled", False, False),
    ("bedtime", True, False), ("off", False, False), ("ready", True, False),
])
async def test_free_time_requires_an_enabled_ready_decision(hass, reason, locked, expected):
    client = AsyncMock()
    coordinator = KinwallCoordinator(hass, client, 30)
    coordinator.data = KinwallData(members=[{"id": "m1", "name": "Maya"}],
        routines={"m1": {"enabled": reason != "off", "locked": locked, "reason": reason}})
    coordinator.last_update_success = True
    sensor = KinwallFreeTimeSensor(coordinator, MockConfigEntry(domain="kinwall"), "m1", "Maya")
    assert sensor.is_on is expected
    assert sensor.available
    assert sensor.extra_state_attributes["reason"] == reason
    coordinator.data.routines = {}
    assert not sensor.available
    coordinator.data.features = {"chores": False}
    assert not sensor.available


async def test_clock_changes_refresh_decision_without_a_revision_change(hass):
    client = AsyncMock()
    client.get_rev_info.return_value = {"rev": 1}
    client.get_routine.return_value = {"enabled": True, "locked": False, "reason": "ready"}
    coordinator = KinwallCoordinator(hass, client, 30)
    coordinator._last_rev = 1
    coordinator._day = coordinator.today()
    coordinator.data = KinwallData(members=[{"id": "m1", "name": "Maya", "grownUp": False},
        {"id": "m2", "name": "Alex", "grownUp": True}])
    await coordinator.async_refresh()
    assert coordinator.data.routines["m1"]["reason"] == "ready"
    client.get_routine.assert_awaited_once_with("m1")
    client.get_routine.return_value = {"enabled": True, "locked": True, "reason": "routine"}
    await coordinator.async_refresh()
    assert coordinator.data.routines["m1"]["locked"]
    client.get_members.assert_not_awaited()


def _iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


async def test_unchanged_decision_is_reused_until_its_next_boundary(hass):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    client = AsyncMock()
    client.get_rev_info.return_value = {"rev": 1}
    client.get_routine.return_value = {"enabled": True, "locked": True, "reason": "routine",
        "checkedAt": _iso(now), "validUntil": _iso(now + timedelta(hours=2))}
    coordinator = KinwallCoordinator(hass, client, 30)
    coordinator._last_rev = 1
    coordinator._day = coordinator.today()
    coordinator.data = KinwallData(members=[{"id": "m1", "name": "Maya", "grownUp": False}])
    await coordinator.async_refresh()
    await coordinator.async_refresh()
    client.get_routine.assert_awaited_once_with("m1")  # same rev, before validUntil: no refetch
    coordinator.data.routines["m1"].update(checkedAt=_iso(now - timedelta(minutes=10)), validUntil=_iso(now - timedelta(seconds=1)))
    await coordinator.async_refresh()
    assert client.get_routine.await_count == 2  # the boundary passed


async def test_past_boundary_decision_rechecks_every_fifteen_minutes(hass):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    client = AsyncMock()
    client.get_rev_info.return_value = {"rev": 1}
    coordinator = KinwallCoordinator(hass, client, 30)
    coordinator._last_rev = 1
    coordinator._day = coordinator.today()
    bedtime = {"enabled": True, "locked": True, "reason": "bedtime",
        "checkedAt": _iso(now), "validUntil": _iso(now - timedelta(hours=1))}  # after cutoff
    coordinator.data = KinwallData(members=[{"id": "m1", "grownUp": False}], routines={"m1": bedtime})
    client.get_routine.return_value = bedtime
    await coordinator.async_refresh()
    client.get_routine.assert_not_awaited()
    coordinator.data.routines["m1"] = {**bedtime, "checkedAt": _iso(now - timedelta(minutes=16))}
    await coordinator.async_refresh()
    client.get_routine.assert_awaited_once_with("m1")


async def test_revision_change_refetches_a_fresh_decision(hass):
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    client = AsyncMock()
    client.get_rev_info.return_value = {"rev": 2, "revs": {"events": 1, "lists": 1, "chores": 2}}
    client.get_members.return_value = [{"id": "m1", "grownUp": False}]
    client.get_routine.return_value = {"enabled": True, "locked": False, "reason": "ready"}
    coordinator = KinwallCoordinator(hass, client, 30)
    coordinator._last_rev, coordinator._revs = 1, {"events": 1, "lists": 1, "chores": 1}
    coordinator._day = coordinator.today()
    coordinator.data = KinwallData(members=[{"id": "m1", "grownUp": False}], routines={"m1": {
        "enabled": True, "locked": True, "reason": "routine",
        "checkedAt": _iso(now), "validUntil": _iso(now + timedelta(hours=2))}})
    await coordinator.async_refresh()
    client.get_routine.assert_awaited_once_with("m1")  # a chore was done: ask again
    assert coordinator.data.routines["m1"]["reason"] == "ready"


@pytest.mark.parametrize("status", [403, 404])
async def test_older_servers_and_display_keys_omit_routines(hass, status):
    client = AsyncMock()
    client.get_routine.side_effect = KinwallApiError("unavailable", status)
    coordinator = KinwallCoordinator(hass, client, 30)
    data = KinwallData(members=[{"id": "m1", "grownUp": False}])
    assert await coordinator._routines(data) == {}
    data.features = {"chores": False}
    client.get_routine.reset_mock()
    assert await coordinator._routines(data) == {}
    client.get_routine.assert_not_awaited()


async def test_routine_failure_does_not_reuse_a_previous_grant(hass):
    client = AsyncMock()
    client.get_routine.side_effect = KinwallApiError("server failed", 500)
    coordinator = KinwallCoordinator(hass, client, 30)
    data = KinwallData(members=[{"id": "m1", "grownUp": False}], routines={"m1": {"reason": "ready"}})
    assert await coordinator._routines(data) == {}
    client.get_routine.side_effect = KinwallAuthError("expired")
    with pytest.raises(KinwallAuthError):
        await coordinator._routines(data)


async def test_child_sensor_appears_and_follows_feature_switch(hass, aioclient_mock):
    from .test_features import _mock, BASE_URL
    from homeassistant.const import CONF_URL, CONF_API_KEY
    from homeassistant.helpers import entity_registry as er
    _mock(aioclient_mock, 1, {}, members=[{"id": "m1", "name": "Maya", "grownUp": False}])
    aioclient_mock.get(f"{BASE_URL}/api/routine-mode/m1", json={"enabled": True, "locked": False, "reason": "ready"})
    entry = MockConfigEntry(domain="kinwall", data={CONF_URL: BASE_URL, CONF_API_KEY: "key"})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.maya_free_time").state == "on"
    coordinator = hass.data["kinwall"][entry.entry_id]
    _mock(aioclient_mock, 2, {"chores": False})
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.maya_free_time") is None
    assert er.async_get(hass).async_get("binary_sensor.maya_free_time") is None
