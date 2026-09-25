"""Kinwall calendar platform: one per member, plus an aggregate 'Family' calendar."""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityFeature,
    CalendarEvent,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KinwallCoordinator
from .entity import KinwallEntity, family_device_info, member_device_info


def _parse_dt(value: str, all_day: bool) -> date | datetime:
    if all_day:
        return date.fromisoformat(value)
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _to_calendar_event(item: dict[str, Any]) -> CalendarEvent:
    all_day = item["allDay"]
    return CalendarEvent(
        start=_parse_dt(item["start"], all_day),
        end=_parse_dt(item["end"], all_day),
        summary=item["title"],
        description=item.get("description") or None,
        location=item.get("location") or None,
        uid=item["id"],
        rrule=item.get("rrule") or None,
    )


def _event_to_payload(event_input) -> dict[str, Any]:
    """Convert HA's create/update event dict (dateutil-parsed) to Kinwall's API body."""
    start = event_input["dtstart"]
    end = event_input["dtend"]
    all_day = isinstance(start, date) and not isinstance(start, datetime)
    payload: dict[str, Any] = {
        "title": event_input["summary"],
        "start": start.isoformat() if all_day else start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "end": end.isoformat() if all_day else end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "allDay": all_day,
    }
    if event_input.get("description"):
        payload["description"] = event_input["description"]
    if event_input.get("location"):
        payload["location"] = event_input["location"]
    if event_input.get("rrule"):
        payload["rrule"] = event_input["rrule"]
    return payload


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KinwallCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[CalendarEntity] = [KinwallFamilyCalendar(coordinator, entry)]
    for member in coordinator.data.members:
        entities.append(KinwallMemberCalendar(coordinator, entry, member["id"], member["name"]))
    async_add_entities(entities)


def _writable_calendar_id(calendars: list[dict], member_id: str | None) -> str | None:
    """Pick the member's first writable calendar, else a local writable calendar."""
    candidates = [c for c in calendars if c.get("writable")]
    if member_id:
        for cal in candidates:
            # memberIds (a calendar can now be assigned to several members) - falls back to the
            # older single memberId for a server that hasn't been upgraded yet.
            member_ids = cal.get("memberIds")
            if member_ids is None:
                member_ids = [cal["memberId"]] if cal.get("memberId") else []
            if member_id in member_ids:
                return cal["id"]
    for cal in candidates:
        if cal.get("kind") == "local":
            return cal["id"]
    return candidates[0]["id"] if candidates else None


class _KinwallCalendarBase(KinwallEntity, CalendarEntity):
    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, unique_id: str) -> None:
        super().__init__(coordinator, entry, unique_id)
        self._attr_name = None  # has_entity_name: device name is used

    def _events_for(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @property
    def event(self) -> CalendarEvent | None:
        now = datetime.now(timezone.utc)
        upcoming = [e for e in self._events_for() if _parse_end(e) >= now]
        upcoming.sort(key=lambda e: e["start"])
        return _to_calendar_event(upcoming[0]) if upcoming else None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        out = []
        for item in self._events_for():
            all_day = item["allDay"]
            item_start = _parse_dt(item["start"], all_day)
            item_end = _parse_dt(item["end"], all_day)
            s = datetime.combine(item_start, datetime.min.time(), tzinfo=timezone.utc) if all_day else item_start
            e = datetime.combine(item_end, datetime.min.time(), tzinfo=timezone.utc) if all_day else item_end
            if e < start_date or s > end_date:
                continue
            out.append(_to_calendar_event(item))
        return out


def _parse_end(item: dict[str, Any]) -> datetime:
    if item["allDay"]:
        return datetime.combine(date.fromisoformat(item["end"]), datetime.min.time(), tzinfo=timezone.utc)
    return datetime.fromisoformat(item["end"].replace("Z", "+00:00")).astimezone(timezone.utc)


class KinwallFamilyCalendar(_KinwallCalendarBase):
    """Aggregate, read-only view of every member's events."""

    _attr_translation_key = "family_calendar"

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, f"{entry.entry_id}_calendar_family")
        self._attr_device_info = family_device_info(entry, "Family")

    def _events_for(self) -> list[dict[str, Any]]:
        return self.coordinator.data.events


class KinwallMemberCalendar(_KinwallCalendarBase):
    """One calendar per member; supports create/update/delete on a writable calendar."""

    _attr_supported_features = (
        CalendarEntityFeature.CREATE_EVENT | CalendarEntityFeature.UPDATE_EVENT | CalendarEntityFeature.DELETE_EVENT
    )

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, member_id: str, member_name: str) -> None:
        super().__init__(coordinator, entry, f"{entry.entry_id}_calendar_{member_id}")
        self._member_id = member_id
        self._attr_device_info = member_device_info(entry, member_id, member_name)

    def _events_for(self) -> list[dict[str, Any]]:
        return [e for e in self.coordinator.data.events if self._member_id in e.get("memberIds", [])]

    async def async_create_event(self, **kwargs: Any) -> None:
        calendar_id = _writable_calendar_id(self.coordinator.data.calendars, self._member_id)
        if not calendar_id:
            raise ValueError("No writable calendar available for this member")
        payload = _event_to_payload(kwargs)
        payload["calendarId"] = calendar_id
        payload["memberIds"] = [self._member_id]
        await self.coordinator.client.create_event(payload)
        await self.coordinator.async_request_refresh()

    async def async_update_event(self, uid: str, event: dict[str, Any], recurrence_id: str | None = None, recurrence_range: str | None = None) -> None:
        await self.coordinator.client.update_event(uid, _event_to_payload(event))
        await self.coordinator.async_request_refresh()

    async def async_delete_event(self, uid: str, recurrence_id: str | None = None, recurrence_range: str | None = None) -> None:
        await self.coordinator.client.delete_event(uid)
        await self.coordinator.async_request_refresh()
