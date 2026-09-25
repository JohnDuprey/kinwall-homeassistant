"""Coordinator: only re-fetches members/calendars/events/chores when /api/rev changes."""
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.kinwall.api import KinwallClient
from custom_components.kinwall.coordinator import KinwallCoordinator

BASE_URL = "http://kinwall.local:8080"


def _mock_full_refresh(aioclient_mock, rev: int):
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": rev})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[{"id": "m1", "name": "Alice", "pointsToday": 0, "pointsWeek": 0}])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])


async def test_no_refetch_when_rev_unchanged(hass, aioclient_mock):
    _mock_full_refresh(aioclient_mock, rev=1)
    client = KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)

    await coordinator.async_refresh()
    assert len(coordinator.data.members) == 1
    assert coordinator.data.rev == 1

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1})
    await coordinator.async_refresh()
    # rev unchanged: no members/calendars/events/chores calls were made (would raise if mocked missing).
    assert coordinator.data.rev == 1
    assert len(coordinator.data.members) == 1


async def test_refetch_when_rev_changes(hass, aioclient_mock):
    _mock_full_refresh(aioclient_mock, rev=1)
    client = KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)
    await coordinator.async_refresh()
    assert coordinator.data.rev == 1

    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 2})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[{"id": "m1", "name": "Alice", "pointsToday": 5, "pointsWeek": 5}])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])

    await coordinator.async_refresh()
    assert coordinator.data.rev == 2
    assert coordinator.data.members[0]["pointsToday"] == 5


async def test_fetches_lists_and_one_detail_per_list(hass, aioclient_mock):
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[{"id": "l1", "name": "Groceries", "kind": "shopping"}])
    aioclient_mock.get(
        f"{BASE_URL}/api/lists/l1",
        json={"list": {"id": "l1"}, "items": [{"id": "i1", "title": "Milk"}], "groups": [], "suggestions": {"stores": [], "categories": []}},
    )

    client = KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)
    await coordinator.async_refresh()

    assert coordinator.data.lists == [{"id": "l1", "name": "Groceries", "kind": "shopping"}]
    assert coordinator.data.list_items == {"l1": [{"id": "i1", "title": "Milk"}]}
