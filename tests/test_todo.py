"""Todo entity: completing an item calls the right Kinwall API endpoint."""
from datetime import date

from homeassistant.components.todo import TodoItem, TodoItemStatus

from custom_components.kinwall.coordinator import KinwallCoordinator, KinwallData
from custom_components.kinwall.todo import (
    KinwallChoreList,
    KinwallList,
    _list_item_description,
    _notes_from_description,
    _to_list_todo_item,
)


class _FakeEntry:
    entry_id = "entry1"


# -- pure mapping logic: ListItem -> TodoItem, no hass needed --------------------


def test_meta_line_skips_empty_parts():
    assert _list_item_description({"store": "Aldi", "category": None, "quantity": "2"}, "shopping") == "\U0001f6d2 Aldi · 2"
    assert _list_item_description({}, "shopping") is None
    assert _list_item_description({"notes": "brand matters"}, "shopping") == "brand matters"


def test_meta_line_only_for_shopping_lists():
    assert _list_item_description({"store": "Aldi", "notes": "x"}, "todo") == "x"


def test_notes_plus_meta_combine_with_newline():
    item = {"notes": "get the big one", "store": "Aldi", "category": "Dairy", "quantity": "2"}
    desc = _list_item_description(item, "shopping")
    assert desc == "get the big one\n\U0001f6d2 Aldi · Dairy · 2"


def test_notes_from_description_strips_generated_line():
    desc = "get the big one\n\U0001f6d2 Aldi · Dairy · 2"
    assert _notes_from_description(desc) == "get the big one"
    assert _notes_from_description("\U0001f6d2 Aldi · Dairy") is None
    assert _notes_from_description(None) is None
    assert _notes_from_description("plain notes") == "plain notes"


def test_to_list_todo_item_maps_status_and_due():
    item = _to_list_todo_item(
        {"id": "i1", "title": "Milk", "done": True, "dueDate": "2026-01-05", "store": "Aldi", "category": None, "quantity": None},
        "shopping",
    )
    assert item.uid == "i1"
    assert item.summary == "Milk"
    assert item.status == TodoItemStatus.COMPLETED
    assert item.due == date(2026, 1, 5)
    assert item.description == "\U0001f6d2 Aldi"


def test_to_list_todo_item_open_no_due():
    item = _to_list_todo_item({"id": "i2", "title": "Bread", "done": False, "dueDate": None}, "todo")
    assert item.status == TodoItemStatus.NEEDS_ACTION
    assert item.due is None
    assert item.description is None


async def test_complete_calls_complete_api(hass, aioclient_mock):
    today = date.today().isoformat()
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from custom_components.kinwall.api import KinwallClient

    client = KinwallClient(async_get_clientsession(hass), "http://kinwall.local:8080", "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)
    coordinator.data = KinwallData(
        rev=1,
        members=[{"id": "m1", "name": "Alice"}],
        chores_today=[{"id": "c1", "title": "Dishes", "emoji": "🍽️", "memberId": "m1", "completed": False}],
    )
    coordinator._last_rev = 1  # avoid a full members/calendars/events/chores refetch below

    entity = KinwallChoreList(coordinator, _FakeEntry(), "m1", "Alice")
    entity.hass = hass

    aioclient_mock.post(f"http://kinwall.local:8080/api/chores/c1/complete", json={"ok": True})
    aioclient_mock.get(f"http://kinwall.local:8080/api/rev", json={"rev": 1})

    await entity.async_update_todo_item(TodoItem(uid="c1", summary="Dishes", status=TodoItemStatus.COMPLETED))

    complete_calls = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and "complete" in str(c[1])]
    assert len(complete_calls) == 1
    assert complete_calls[0][2] == {"date": today, "memberId": "m1"}


# -- KinwallList: create/update/delete/move call the right Kinwall list endpoints --------


def _make_list_entity(hass, aioclient_mock, kind="shopping", items=None):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    from custom_components.kinwall.api import KinwallClient

    client = KinwallClient(async_get_clientsession(hass), "http://kinwall.local:8080", "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)
    coordinator.data = KinwallData(
        rev=1,
        lists=[{"id": "l1", "name": "Groceries", "kind": kind, "emoji": None}],
        list_items={"l1": items or []},
    )
    coordinator._last_rev = 1

    entity = KinwallList(coordinator, _FakeEntry(), "l1", "Groceries", kind, None)
    entity.hass = hass
    aioclient_mock.get("http://kinwall.local:8080/api/rev", json={"rev": 1})
    return entity


async def test_create_sends_only_given_fields(hass, aioclient_mock):
    entity = _make_list_entity(hass, aioclient_mock)
    aioclient_mock.post("http://kinwall.local:8080/api/lists/l1/items", json=[{"id": "i1"}])

    await entity.async_create_todo_item(TodoItem(summary="Milk", status=TodoItemStatus.NEEDS_ACTION))

    calls = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and "items" in str(c[1])]
    assert len(calls) == 1
    assert calls[0][2] == {"title": "Milk"}


async def test_update_maps_fields_and_strips_generated_notes_line(hass, aioclient_mock):
    entity = _make_list_entity(hass, aioclient_mock)
    aioclient_mock.patch("http://kinwall.local:8080/api/lists/l1/items/i1", json={"id": "i1"})

    item = TodoItem(
        uid="i1",
        summary="Milk",
        status=TodoItemStatus.COMPLETED,
        due=date(2026, 1, 5),
        description="get the 2%\n\U0001f6d2 Aldi · Dairy",
    )
    await entity.async_update_todo_item(item)

    calls = [c for c in aioclient_mock.mock_calls if c[0] == "PATCH"]
    assert len(calls) == 1
    assert calls[0][2] == {"title": "Milk", "done": True, "dueDate": "2026-01-05", "notes": "get the 2%"}


async def test_delete_calls_api_for_each_uid(hass, aioclient_mock):
    entity = _make_list_entity(hass, aioclient_mock)
    aioclient_mock.delete("http://kinwall.local:8080/api/lists/l1/items/i1", json={"ok": True})
    aioclient_mock.delete("http://kinwall.local:8080/api/lists/l1/items/i2", json={"ok": True})

    await entity.async_delete_todo_items(["i1", "i2"])

    delete_calls = [c for c in aioclient_mock.mock_calls if c[0] == "DELETE"]
    assert len(delete_calls) == 2


async def test_move_posts_full_resulting_order(hass, aioclient_mock):
    items = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    entity = _make_list_entity(hass, aioclient_mock, items=items)
    aioclient_mock.post("http://kinwall.local:8080/api/lists/l1/reorder", json={"ok": True})

    # move "c" to right after "a": a, c, b
    await entity.async_move_todo_item("c", previous_uid="a")

    calls = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and "reorder" in str(c[1])]
    assert len(calls) == 1
    assert calls[0][2] == {"itemIds": ["a", "c", "b"]}


async def test_move_to_start_with_no_previous(hass, aioclient_mock):
    items = [{"id": "a"}, {"id": "b"}]
    entity = _make_list_entity(hass, aioclient_mock, items=items)
    aioclient_mock.post("http://kinwall.local:8080/api/lists/l1/reorder", json={"ok": True})

    await entity.async_move_todo_item("b", previous_uid=None)

    calls = [c for c in aioclient_mock.mock_calls if c[0] == "POST" and "reorder" in str(c[1])]
    assert calls[0][2] == {"itemIds": ["b", "a"]}
