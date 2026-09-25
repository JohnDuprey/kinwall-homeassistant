"""DataUpdateCoordinator for Kinwall: cheap /api/rev poll, full refresh on change."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KinwallAuthError, KinwallClient
from .const import DOMAIN, EVENTS_WINDOW_FUTURE_DAYS, EVENTS_WINDOW_PAST_DAYS

_LOGGER = logging.getLogger(__name__)


@dataclass
class KinwallData:
    """Snapshot of Kinwall state the entities read from."""

    rev: int = 0
    members: list[dict] = field(default_factory=list)
    calendars: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    chores_today: list[dict] = field(default_factory=list)
    lists: list[dict] = field(default_factory=list)
    # list id -> its items, fetched via one GET /api/lists/{id} per list per refresh.
    list_items: dict[str, list[dict]] = field(default_factory=dict)


class KinwallCoordinator(DataUpdateCoordinator[KinwallData]):
    """Polls /api/rev; only re-fetches the rest when it changes."""

    def __init__(self, hass: HomeAssistant, client: KinwallClient, poll_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self.client = client
        self._last_rev: int | None = None
        self.family_device_id: str | None = None  # set by async_setup_entry; member devices hang off it
        self.data = KinwallData()

    async def _async_update_data(self) -> KinwallData:
        try:
            rev = await self.client.get_rev()
        except KinwallAuthError as err:
            raise ConfigEntryAuthFailed("Kinwall API key rejected") from err
        except Exception as err:  # noqa: BLE001 - surfaced via UpdateFailed
            raise UpdateFailed(f"error polling rev: {err}") from err

        if self._last_rev is not None and rev == self._last_rev:
            self.data.rev = rev
            return self.data

        self._last_rev = rev
        return await self._full_refresh(rev)

    async def async_request_full_refresh(self) -> None:
        """Called by the webhook handler after a push notification."""
        rev = await self.client.get_rev()
        self._last_rev = rev
        self.async_set_updated_data(await self._full_refresh(rev))

    async def _full_refresh(self, rev: int) -> KinwallData:
        try:
            members = await self.client.get_members()
            calendars = await self.client.get_calendars()
            now = datetime.now(timezone.utc)
            start = (now - timedelta(days=EVENTS_WINDOW_PAST_DAYS)).strftime("%Y-%m-%dT00:00:00.000Z")
            end = (now + timedelta(days=EVENTS_WINDOW_FUTURE_DAYS)).strftime("%Y-%m-%dT00:00:00.000Z")
            events = await self.client.get_events(start, end)
            today = now.strftime("%Y-%m-%d")
            chores_today = await self.client.get_chores_day(today)
            lists = await self.client.get_lists()
            list_items: dict[str, list[dict]] = {}
            for lst in lists:
                detail = await self.client.get_list_detail(lst["id"])
                list_items[lst["id"]] = detail["items"]
        except KinwallAuthError as err:
            raise ConfigEntryAuthFailed("Kinwall API key rejected") from err
        except Exception as err:  # noqa: BLE001
            raise UpdateFailed(f"error refreshing kinwall data: {err}") from err

        return KinwallData(
            rev=rev,
            members=members,
            calendars=calendars,
            events=events,
            chores_today=chores_today,
            lists=lists,
            list_items=list_items,
        )
