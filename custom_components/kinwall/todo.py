"""Kinwall todo platform.

Two kinds of to-do entities:
- one per member (+ 'Anyone') showing today's chores
- one per Kinwall list (server/src/routes/lists.ts), added/removed dynamically as lists
  are created/deleted/archived
"""
from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.todo import TodoItem, TodoItemStatus, TodoListEntity, TodoListEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import KinwallApiError
from .const import DOMAIN
from .coordinator import KinwallCoordinator
from .entity import KinwallEntity, family_device_info, member_device_info

ANYONE_ID = "_anyone"

# Generated "Store · Category · qty" description line for shopping items is prefixed with this
# marker so it can be told apart from the item's own notes and stripped back out on write.
_META_PREFIX = "\U0001f6d2 "  # shopping-cart emoji


def _today() -> str:
    return date.today().isoformat()


def _to_todo_item(chore: dict[str, Any]) -> TodoItem:
    status = TodoItemStatus.COMPLETED if chore.get("completed") else TodoItemStatus.NEEDS_ACTION
    summary = f"{chore['emoji']} {chore['title']}" if chore.get("emoji") else chore["title"]
    # A linked checklist gates completion (the server answers 409 until it's fully ticked); say so.
    cl = chore.get("checklist")
    description = f"Checklist: {cl['name']} {cl['done']}/{cl['total']}" if cl else None
    return TodoItem(uid=chore["id"], summary=summary, status=status, description=description)


def _meta_line(item: dict[str, Any]) -> str | None:
    """Compact 'Store · Category · qty' line, skipping any empty parts."""
    parts = [p for p in (item.get("store"), item.get("category"), item.get("quantity")) if p]
    return " · ".join(parts) if parts else None


def _list_item_description(item: dict[str, Any], kind: str) -> str | None:
    """notes plus, for shopping lists, a generated store/category/qty line."""
    notes = (item.get("notes") or "").strip()
    meta = _META_PREFIX + _meta_line(item) if kind == "shopping" and _meta_line(item) else None
    if notes and meta:
        return f"{notes}\n{meta}"
    return notes or meta or None


def _notes_from_description(description: str | None) -> str | None:
    """Strip the generated meta line back out, leaving only the user's own notes."""
    if not description:
        return None
    lines = [line for line in description.split("\n") if not line.startswith(_META_PREFIX)]
    notes = "\n".join(lines).strip()
    return notes or None


def _to_list_todo_item(item: dict[str, Any], kind: str) -> TodoItem:
    due = date.fromisoformat(item["dueDate"]) if item.get("dueDate") else None
    status = TodoItemStatus.COMPLETED if item.get("done") else TodoItemStatus.NEEDS_ACTION
    return TodoItem(
        uid=item["id"],
        summary=item["title"],
        status=status,
        due=due,
        description=_list_item_description(item, kind),
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KinwallCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[TodoListEntity] = [KinwallChoreList(coordinator, entry, ANYONE_ID, "Anyone")]
    for member in coordinator.data.members:
        entities.append(KinwallChoreList(coordinator, entry, member["id"], member["name"]))
    async_add_entities(entities)

    # Kinwall lists (shopping/todo/reusable) are user-created, so entities for them are added
    # and removed dynamically as the coordinator's data changes, rather than once at setup.
    known_ids: set[str] = set()
    list_entities: dict[str, KinwallList] = {}

    @callback
    def _sync_lists() -> None:
        current = {lst["id"]: lst for lst in coordinator.data.lists}
        new_entities = []
        for list_id, lst in current.items():
            if list_id not in known_ids:
                entity = KinwallList(coordinator, entry, list_id, lst["name"], lst["kind"], lst.get("emoji"))
                list_entities[list_id] = entity
                new_entities.append(entity)
        if new_entities:
            async_add_entities(new_entities)

        for list_id in known_ids - current.keys():
            removed = list_entities.pop(list_id, None)
            if removed is not None:
                hass.async_create_task(removed.async_remove(force_remove=True))

        known_ids.clear()
        known_ids.update(current.keys())

    _sync_lists()
    entry.async_on_unload(coordinator.async_add_listener(_sync_lists))


class KinwallChoreList(KinwallEntity, TodoListEntity):
    """Today's chores for one member (or unassigned, for 'Anyone')."""

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
    )

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, member_id: str, member_name: str) -> None:
        super().__init__(coordinator, entry, f"{entry.entry_id}_todo_{member_id}")
        self._member_id = member_id
        self._attr_name = None
        if member_id == ANYONE_ID:
            self._attr_device_info = family_device_info(entry, "Family")
        else:
            self._attr_device_info = member_device_info(entry, member_id, member_name, coordinator.family_device_id)

    def _chores(self) -> list[dict[str, Any]]:
        if self._member_id == ANYONE_ID:
            return [c for c in self.coordinator.data.chores_today if not c.get("memberId")]
        return [c for c in self.coordinator.data.chores_today if c.get("memberId") == self._member_id]

    @property
    def todo_items(self) -> list[TodoItem]:
        return [_to_todo_item(c) for c in self._chores()]

    async def async_update_todo_item(self, item: TodoItem) -> None:
        today = _today()
        if item.status == TodoItemStatus.COMPLETED:
            member_id = None if self._member_id == ANYONE_ID else self._member_id
            try:
                await self.coordinator.client.complete_chore(item.uid, today, member_id)
            except KinwallApiError as err:
                # e.g. 409 "Checklist not finished (2 left)": surface the server's reason, not a stack trace.
                raise HomeAssistantError(err.reason or str(err)) from err
        else:
            await self.coordinator.client.uncomplete_chore(item.uid, today)
        await self.coordinator.async_request_refresh()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        payload: dict[str, Any] = {"title": item.summary, "dueDate": _today()}
        if self._member_id != ANYONE_ID:
            payload["memberId"] = self._member_id
        await self.coordinator.client.create_chore(payload)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            await self.coordinator.client.delete_chore(uid)
        await self.coordinator.async_request_refresh()


class KinwallList(KinwallEntity, TodoListEntity):
    """A Kinwall list (shopping/todo/reusable), one to-do entity per list.

    Lets voice assistants and the HA to-do card add/check/move items, e.g.
    "add milk to the groceries list".
    """

    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.MOVE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(
        self,
        coordinator: KinwallCoordinator,
        entry: ConfigEntry,
        list_id: str,
        name: str,
        kind: str,
        emoji: str | None,
    ) -> None:
        super().__init__(coordinator, entry, f"{entry.entry_id}_list_{list_id}")
        self._list_id = list_id
        self._kind = kind
        self._attr_name = f"{emoji} {name}" if emoji else name
        self._attr_device_info = family_device_info(entry, "Family")

    def _items(self) -> list[dict[str, Any]]:
        return self.coordinator.data.list_items.get(self._list_id, [])

    @property
    def todo_items(self) -> list[TodoItem]:
        return [_to_list_todo_item(i, self._kind) for i in self._items()]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        # Only send what was actually given - an omitted store/category lets the server
        # "remember" the last one used for that title.
        payload: dict[str, Any] = {"title": item.summary}
        if item.due:
            payload["dueDate"] = item.due.isoformat()
        notes = _notes_from_description(item.description)
        if notes:
            payload["notes"] = notes
        await self.coordinator.client.create_list_items(self._list_id, payload)
        await self.coordinator.async_request_refresh()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        # HA hands us the item's full, merged state, so map every field - but only write
        # notes back (never clobber a remembered store/category with the generated line).
        payload: dict[str, Any] = {
            "title": item.summary,
            "done": item.status == TodoItemStatus.COMPLETED,
            "dueDate": item.due.isoformat() if item.due else None,
            "notes": _notes_from_description(item.description),
        }
        await self.coordinator.client.update_list_item(self._list_id, item.uid, payload)
        await self.coordinator.async_request_refresh()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        for uid in uids:
            await self.coordinator.client.delete_list_item(self._list_id, uid)
        await self.coordinator.async_request_refresh()

    async def async_move_todo_item(self, uid: str, previous_uid: str | None = None) -> None:
        order = [i["id"] for i in self._items() if i["id"] != uid]
        index = order.index(previous_uid) + 1 if previous_uid else 0
        order.insert(index, uid)
        await self.coordinator.client.reorder_list_items(self._list_id, order)
        await self.coordinator.async_request_refresh()
