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
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/displays/night-screen", status=404)  # a server older than 1.1.0


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
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/displays/night-screen", status=404)  # a server older than 1.1.0

    await coordinator.async_refresh()
    assert coordinator.data.rev == 2
    assert coordinator.data.members[0]["pointsToday"] == 5


async def test_fetches_lists_and_one_detail_per_list(hass, aioclient_mock):
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=[{"id": "l1", "name": "Groceries", "kind": "shopping"}])
    aioclient_mock.get(f"{BASE_URL}/api/displays/night-screen", status=404)  # a server older than 1.1.0
    aioclient_mock.get(
        f"{BASE_URL}/api/lists/l1",
        json={"list": {"id": "l1"}, "items": [{"id": "i1", "title": "Milk"}], "groups": [], "suggestions": {"stores": [], "categories": []}},
    )

    client = KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)
    await coordinator.async_refresh()

    assert coordinator.data.lists == [{"id": "l1", "name": "Groceries", "kind": "shopping"}]
    assert coordinator.data.list_items == {"l1": [{"id": "i1", "title": "Milk"}]}


# --- Refetch only what changed (Kinwall servers with per-area revs and list itemsRev) ------------

LISTS = [
    {"id": "l1", "name": "Groceries", "kind": "shopping", "itemsRev": 3},
    {"id": "l2", "name": "Chores", "kind": "todo", "itemsRev": 7},
]


def _detail(list_id: str, title: str) -> dict:
    return {"list": {"id": list_id}, "items": [{"id": f"{list_id}-i", "title": title}], "groups": [], "suggestions": {"stores": [], "categories": [], "aisles": []}}


def _mock_everything(aioclient_mock, rev: int, revs: dict | None, lists=LISTS, titles=("Milk", "Sweep")):
    aioclient_mock.clear_requests()
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": rev, **({"revs": revs} if revs is not None else {}), "nightScreen": None})
    aioclient_mock.get(f"{BASE_URL}/api/members", json=[{"id": "m1", "name": "Alice", "pointsToday": 0, "pointsWeek": 0}])
    aioclient_mock.get(f"{BASE_URL}/api/calendars", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/events", json=[{"id": "e1"}])
    aioclient_mock.get(f"{BASE_URL}/api/chores/day", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/chores", json=[])
    aioclient_mock.get(f"{BASE_URL}/api/lists/l1", json=_detail("l1", titles[0]))
    aioclient_mock.get(f"{BASE_URL}/api/lists/l2", json=_detail("l2", titles[1]))
    aioclient_mock.get(f"{BASE_URL}/api/lists", json=lists)
    aioclient_mock.get(f"{BASE_URL}/api/displays/night-screen", json={"all": False, "displays": []})


def _paths(aioclient_mock) -> list[str]:
    return sorted(str(url.path) + (f"?{url.query_string}" if url.query_string and "lists/" in url.path else "") for _, url, _, _ in aioclient_mock.mock_calls)


async def _started(hass, aioclient_mock):
    _mock_everything(aioclient_mock, rev=1, revs={"events": 1, "lists": 1, "chores": 1})
    coordinator = KinwallCoordinator(hass, KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key"), poll_interval=30)
    await coordinator.async_refresh()
    assert coordinator.data.list_items == {"l1": [{"id": "l1-i", "title": "Milk"}], "l2": [{"id": "l2-i", "title": "Sweep"}]}
    return coordinator


async def test_first_refresh_reads_list_items_without_suggestions(hass, aioclient_mock):
    await _started(hass, aioclient_mock)
    assert "/api/lists/l1?suggestions=false" in _paths(aioclient_mock)
    assert "/api/lists/l2?suggestions=false" in _paths(aioclient_mock)


async def test_only_changed_lists_are_refetched(hass, aioclient_mock):
    coordinator = await _started(hass, aioclient_mock)
    changed = [LISTS[0], {**LISTS[1], "itemsRev": 8}]
    _mock_everything(aioclient_mock, rev=2, revs={"events": 1, "lists": 2, "chores": 1}, lists=changed, titles=("Milk", "Mop"))
    await coordinator.async_refresh()
    assert _paths(aioclient_mock) == ["/api/lists", "/api/lists/l2?suggestions=false", "/api/rev"]
    assert coordinator.data.list_items["l2"] == [{"id": "l2-i", "title": "Mop"}]
    assert coordinator.data.list_items["l1"] == [{"id": "l1-i", "title": "Milk"}]  # kept
    assert coordinator.data.events == [{"id": "e1"}]  # kept
    assert coordinator.data.rev == 2


async def test_a_chore_change_refetches_chores_and_points_only(hass, aioclient_mock):
    coordinator = await _started(hass, aioclient_mock)
    _mock_everything(aioclient_mock, rev=2, revs={"events": 1, "lists": 1, "chores": 2})
    await coordinator.async_refresh()
    assert _paths(aioclient_mock) == ["/api/chores", "/api/chores/day", "/api/members", "/api/rev"]


async def test_other_changes_refetch_all_but_unchanged_list_items(hass, aioclient_mock):
    coordinator = await _started(hass, aioclient_mock)
    _mock_everything(aioclient_mock, rev=2, revs={"events": 2, "lists": 1, "chores": 1})
    await coordinator.async_refresh()
    assert _paths(aioclient_mock) == ["/api/calendars", "/api/chores", "/api/chores/day", "/api/displays/night-screen", "/api/events", "/api/lists", "/api/members", "/api/rev"]
    # A list removed in Kinwall leaves the cache.
    _mock_everything(aioclient_mock, rev=3, revs={"events": 2, "lists": 2, "chores": 1}, lists=LISTS[:1])
    await coordinator.async_refresh()
    assert list(coordinator.data.list_items) == ["l1"]


async def test_a_new_day_refetches_everything(hass, aioclient_mock, freezer):
    freezer.move_to("2026-10-01 12:00:00+00:00")
    coordinator = await _started(hass, aioclient_mock)
    freezer.move_to("2026-10-02 00:05:00+00:00")
    _mock_everything(aioclient_mock, rev=1, revs={"events": 1, "lists": 1, "chores": 1})
    await coordinator.async_refresh()
    assert "/api/events" in _paths(aioclient_mock) and "/api/lists/l1?suggestions=false" in _paths(aioclient_mock)


async def test_older_server_without_revs_refetches_everything(hass, aioclient_mock):
    no_revs = [{k: v for k, v in lst.items() if k != "itemsRev"} for lst in LISTS]
    _mock_everything(aioclient_mock, rev=1, revs=None, lists=no_revs)
    coordinator = KinwallCoordinator(hass, KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key"), poll_interval=30)
    await coordinator.async_refresh()
    _mock_everything(aioclient_mock, rev=2, revs=None, lists=no_revs, titles=("Eggs", "Sweep"))
    await coordinator.async_refresh()
    assert len(_paths(aioclient_mock)) == 10  # rev, members, calendars, events, chores x2, lists, 2 details, night screen
    assert coordinator.data.list_items["l1"] == [{"id": "l1-i", "title": "Eggs"}]
