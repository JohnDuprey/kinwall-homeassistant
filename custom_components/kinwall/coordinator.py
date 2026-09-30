"""DataUpdateCoordinator for Kinwall: cheap /api/rev poll, refetch only what changed."""
from __future__ import annotations

import dataclasses
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KinwallApiError, KinwallAuthError, KinwallClient
from .const import DOMAIN, EVENTS_WINDOW_FUTURE_DAYS, EVENTS_WINDOW_PAST_DAYS

_LOGGER = logging.getLogger(__name__)

# GET /api/rev `revs`: lists (lists and items), chores (chores, completions, rewards: points) and
# events (everything else: events, calendars, members, settings). Older servers send no `revs`.
AREAS = ("events", "lists", "chores")


@dataclass
class KinwallData:
    """Snapshot of Kinwall state the entities read from."""

    rev: int = 0
    members: list[dict] = field(default_factory=list)
    calendars: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    chores: list[dict] = field(default_factory=list)  # every chore, due today or not (binary sensors)
    chores_today: list[dict] = field(default_factory=list)
    lists: list[dict] = field(default_factory=list)
    # list id -> its items, from GET /api/lists/{id}; refetched only when the list's itemsRev changes.
    list_items: dict[str, list[dict]] = field(default_factory=dict)
    # GET /api/displays/night-screen: {all, displays}. None when the server has no such endpoint
    # (older than 1.1.0) or the key can't read it (a display key): no Night screen switches then.
    night_screen: dict | None = None


class KinwallCoordinator(DataUpdateCoordinator[KinwallData]):
    """Polls /api/rev; when it changes, re-fetches only the areas whose rev changed."""

    def __init__(self, hass: HomeAssistant, client: KinwallClient, poll_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client
        self._last_rev: int | None = None
        self._revs: dict | None = None  # the area revs last fetched; None = refetch everything
        self._day: str | None = None  # chores_today and the events window move with the day
        self.family_device_id: str | None = None  # set by async_setup_entry; member devices hang off it
        self.data = KinwallData()

    async def _async_update_data(self) -> KinwallData:
        try:
            info = await self.client.get_rev_info()
        except KinwallAuthError as err:
            raise ConfigEntryAuthFailed("Kinwall API key rejected") from err
        except Exception as err:  # noqa: BLE001 - surfaced via UpdateFailed
            raise UpdateFailed(f"error polling rev: {err}") from err

        rev = info["rev"]
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if rev == self._last_rev and today == self._day:
            return self.data
        data = await self._refresh(rev, info.get("revs"), today)
        self._last_rev, self._day = rev, today
        return data

    async def _refresh(self, rev: int, revs: dict | None, today: str) -> KinwallData:
        full = revs is None or self._revs is None or today != self._day
        changed = set(AREAS) if full else {a for a in AREAS if revs.get(a) != self._revs.get(a)}
        other = "events" in changed  # the catch-all area: refetch everything but unchanged lists
        data = dataclasses.replace(self.data, rev=rev)
        try:
            if other or "chores" in changed:
                data.members = await self.client.get_members()  # points
                data.chores = await self.client.get_chores()
                data.chores_today = await self.client.get_chores_day(today)
            if other:
                now = datetime.now(timezone.utc)
                start = (now - timedelta(days=EVENTS_WINDOW_PAST_DAYS)).strftime("%Y-%m-%dT00:00:00.000Z")
                end = (now + timedelta(days=EVENTS_WINDOW_FUTURE_DAYS)).strftime("%Y-%m-%dT00:00:00.000Z")
                data.calendars = await self.client.get_calendars()
                data.events = await self.client.get_events(start, end)
                try:
                    data.night_screen = await self.client.get_night_screen()
                except KinwallApiError:
                    data.night_screen = None
            if other or "lists" in changed:
                data.lists = await self.client.get_lists()
                data.list_items = await self._list_items(data.lists, full)
        except KinwallAuthError as err:
            raise ConfigEntryAuthFailed("Kinwall API key rejected") from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"error refreshing kinwall data: {err}") from err
        self._revs = revs
        return data

    async def _list_items(self, lists: list[dict], full: bool) -> dict[str, list[dict]]:
        """Each list's items: refetched when its itemsRev moved (always on a server without it)."""
        seen = {lst["id"]: lst.get("itemsRev") for lst in self.data.lists}
        items: dict[str, list[dict]] = {}
        for lst in lists:
            list_id = lst["id"]
            unchanged = lst.get("itemsRev") is not None and seen.get(list_id) == lst["itemsRev"] and list_id in self.data.list_items
            if unchanged and not full:
                items[list_id] = self.data.list_items[list_id]
            else:
                items[list_id] = (await self.client.get_list_detail(list_id))["items"]
        return items
