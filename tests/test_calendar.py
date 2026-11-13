"""Calendar entities: all-day events by the local date, and repeating events never changed by accident."""
from datetime import date, datetime

import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from custom_components.kinwall.api import KinwallClient
from custom_components.kinwall.calendar import KinwallMemberCalendar, _to_calendar_event
from custom_components.kinwall.coordinator import KinwallCoordinator, KinwallData

BASE_URL = "http://kinwall.local:8080"

# A weekly swim practice: GET /api/events expands it into one entry per date, all with the series' id.
SWIM_SERIES = {"id": "e1", "title": "Swim", "start": "2026-03-02T23:00:00Z", "end": "2026-03-03T00:00:00Z", "allDay": False, "rrule": "FREQ=WEEKLY", "memberIds": ["m1"]}


def _swim(occurrence_start: str, occurrence_end: str) -> dict:
    return {**SWIM_SERIES, "start": occurrence_start, "end": occurrence_end, "occurrenceStart": occurrence_start}


@pytest.fixture
def expected_lingering_timers() -> bool:
    """These entities run on bare coordinators (no config entry), whose refresh debouncer outlives the test."""
    return True


class _FakeEntry:
    entry_id = "entry1"


def _make_calendar(hass, aioclient_mock, events=None, calendars=None) -> KinwallMemberCalendar:
    client = KinwallClient(async_get_clientsession(hass), BASE_URL, "fc_key")
    coordinator = KinwallCoordinator(hass, client, poll_interval=30)
    coordinator.data = KinwallData(rev=1, members=[{"id": "m1", "name": "Alice"}], events=events or [], calendars=calendars or [])
    coordinator._last_rev = 1
    coordinator._day = coordinator.today()
    entity = KinwallMemberCalendar(coordinator, _FakeEntry(), "m1", "Alice")
    entity.hass = hass
    aioclient_mock.get(f"{BASE_URL}/api/rev", json={"rev": 1})
    return entity


def _calls(aioclient_mock, method: str) -> list:
    return [c for c in aioclient_mock.mock_calls if c[0] == method]


# -- all-day events follow the local date, not UTC midnight ------------------------------------


async def test_todays_all_day_event_stays_current_all_evening(hass, aioclient_mock, freezer):
    # 8 PM on March 9 in Home Assistant's timezone (US/Pacific in tests), already March 10 in UTC.
    freezer.move_to("2026-03-10T03:00:00Z")
    today = {"id": "a1", "title": "Field trip", "start": "2026-03-09", "end": "2026-03-10", "allDay": True, "memberIds": ["m1"]}
    entity = _make_calendar(hass, aioclient_mock, events=[today])
    assert entity.event is not None and entity.event.summary == "Field trip"


async def test_range_query_leaves_out_tomorrows_all_day_events(hass, aioclient_mock, freezer):
    freezer.move_to("2026-03-10T03:00:00Z")
    tomorrow = {"id": "a2", "title": "Picture day", "start": "2026-03-10", "end": "2026-03-11", "allDay": True, "memberIds": ["m1"]}
    entity = _make_calendar(hass, aioclient_mock, events=[tomorrow])
    start = dt_util.start_of_local_day(date(2026, 3, 9))
    end = datetime(2026, 3, 9, 23, 59, 59, tzinfo=dt_util.get_default_time_zone())
    assert await entity.async_get_events(hass, start, end) == []
    next_day = await entity.async_get_events(hass, end, end.replace(day=10))
    assert [e.summary for e in next_day] == ["Picture day"]


# -- repeating events ---------------------------------------------------------------------------


def test_each_date_of_a_repeating_event_has_its_own_recurrence_id():
    first = _to_calendar_event(_swim("2026-03-02T23:00:00.000Z", "2026-03-03T00:00:00.000Z"))
    second = _to_calendar_event(_swim("2026-03-09T23:00:00.000Z", "2026-03-10T00:00:00.000Z"))
    assert first.uid == second.uid == "e1"
    assert first.recurrence_id == "2026-03-02T23:00:00.000Z"
    assert second.recurrence_id == "2026-03-09T23:00:00.000Z"
    assert _to_calendar_event({**SWIM_SERIES, "rrule": None}).recurrence_id is None


async def test_deleting_one_date_of_a_repeating_event_is_refused(hass, aioclient_mock):
    entity = _make_calendar(hass, aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/api/events/e1", json=SWIM_SERIES)
    for recurrence_range in (None, "", "THISANDFUTURE"):
        with pytest.raises(HomeAssistantError, match="repeating"):
            await entity.async_delete_event("e1", recurrence_id="2026-03-09T23:00:00.000Z", recurrence_range=recurrence_range)
    assert _calls(aioclient_mock, "DELETE") == []


async def test_deleting_all_dates_from_the_first_one_deletes_the_series(hass, aioclient_mock):
    entity = _make_calendar(hass, aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/api/events/e1", json=SWIM_SERIES)
    aioclient_mock.delete(f"{BASE_URL}/api/events/e1", json={"ok": True})
    await entity.async_delete_event("e1", recurrence_id="2026-03-02T23:00:00.000Z", recurrence_range="THISANDFUTURE")
    assert len(_calls(aioclient_mock, "DELETE")) == 1


async def test_deleting_a_one_off_event_deletes_it(hass, aioclient_mock):
    entity = _make_calendar(hass, aioclient_mock)
    aioclient_mock.delete(f"{BASE_URL}/api/events/e2", json={"ok": True})
    await entity.async_delete_event("e2", recurrence_id="", recurrence_range="")
    assert len(_calls(aioclient_mock, "DELETE")) == 1


async def test_editing_one_date_of_a_repeating_event_is_refused(hass, aioclient_mock):
    """It would otherwise PATCH the series' start to this date, dropping every earlier one."""
    entity = _make_calendar(hass, aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/api/events/e1", json=SWIM_SERIES)
    moved = {"summary": "Swim", "dtstart": dt_util.parse_datetime("2026-03-09T23:30:00Z"), "dtend": dt_util.parse_datetime("2026-03-10T00:30:00Z"), "rrule": "FREQ=WEEKLY"}
    with pytest.raises(HomeAssistantError, match="repeating"):
        await entity.async_update_event("e1", moved, recurrence_id="2026-03-09T23:00:00.000Z", recurrence_range="")
    assert _calls(aioclient_mock, "PATCH") == []


async def test_editing_all_dates_from_the_first_one_updates_the_series(hass, aioclient_mock):
    entity = _make_calendar(hass, aioclient_mock)
    aioclient_mock.get(f"{BASE_URL}/api/events/e1", json=SWIM_SERIES)
    aioclient_mock.patch(f"{BASE_URL}/api/events/e1", json=SWIM_SERIES)
    event = {"summary": "Swim team", "dtstart": dt_util.parse_datetime("2026-03-02T23:00:00Z"), "dtend": dt_util.parse_datetime("2026-03-03T00:00:00Z"), "rrule": "FREQ=WEEKLY"}
    await entity.async_update_event("e1", event, recurrence_id="2026-03-02T23:00:00.000Z", recurrence_range="THISANDFUTURE")
    patches = _calls(aioclient_mock, "PATCH")
    assert len(patches) == 1
    assert patches[0][2]["title"] == "Swim team" and patches[0][2]["start"] == "2026-03-02T23:00:00Z"


# -- write errors read as Home Assistant errors ---------------------------------------------------


async def test_write_failures_are_home_assistant_errors(hass, aioclient_mock):
    entity = _make_calendar(hass, aioclient_mock)
    event = {"summary": "Dentist", "dtstart": date(2026, 3, 9), "dtend": date(2026, 3, 10)}
    with pytest.raises(HomeAssistantError, match="writable calendar"):
        await entity.async_create_event(**event)

    entity.coordinator.data.calendars = [{"id": "c1", "kind": "local", "writable": True}]
    aioclient_mock.post(f"{BASE_URL}/api/events", status=400, text='{"error":"end is before start"}')
    with pytest.raises(HomeAssistantError, match="end is before start"):
        await entity.async_create_event(**event)

    aioclient_mock.delete(f"{BASE_URL}/api/events/e2", status=404, text='{"error":"not found"}')
    with pytest.raises(HomeAssistantError, match="not found"):
        await entity.async_delete_event("e2")
