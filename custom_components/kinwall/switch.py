"""Night screen switches: one for every wall screen (on the Family device) and one per paired display.

On while Kinwall's remote Night screen is on for it and hasn't run out. Turning one on or off calls
POST /api/displays/night-screen. Displays paired after setup appear after a reload of the integration.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KinwallCoordinator
from .entity import KinwallEntity, family_device_info, member_device_info
from .services import set_night_screen


def night_unique_id(entry: ConfigEntry, display_id: str | None) -> str:
    return f"{entry.entry_id}_night_screen_{display_id or 'all'}"


def _live(state: dict[str, Any] | None) -> bool:
    """On, and not past its `until` (Kinwall lets a forgotten "on" run out on its own)."""
    if not state or not state.get("on") or not state.get("until"):
        return False
    return datetime.fromisoformat(state["until"].replace("Z", "+00:00")) > datetime.now(timezone.utc)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KinwallCoordinator = hass.data[DOMAIN][entry.entry_id]
    night = coordinator.data.night_screen
    if night is None:
        return
    async_add_entities(
        [KinwallNightScreenSwitch(coordinator, entry, None, "Family")]
        + [KinwallNightScreenSwitch(coordinator, entry, d["id"], d["name"]) for d in night.get("displays", [])]
    )


class KinwallNightScreenSwitch(KinwallEntity, SwitchEntity):
    """The Night screen on every wall screen (display_id None) or on one paired display."""

    _attr_icon = "mdi:weather-night"
    _attr_name = "Night screen"

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, display_id: str | None, name: str) -> None:
        super().__init__(coordinator, entry, night_unique_id(entry, display_id))
        self._display_id = display_id
        self._attr_device_info = (
            member_device_info(entry, f"display_{display_id}", name, coordinator.family_device_id) if display_id else family_device_info(entry, name)
        )

    def _state(self) -> dict[str, Any] | None:
        night = self.coordinator.data.night_screen or {}
        if self._display_id is None:
            return night.get("all")
        return next((d for d in night.get("displays", []) if d["id"] == self._display_id), None)

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.night_screen is not None and (self._display_id is None or self._state() is not None)

    @property
    def is_on(self) -> bool:
        return _live(self._state())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self._state() or {}
        return {"display_id": self._display_id, "until": state.get("until") if self.is_on else None}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await set_night_screen(self.coordinator, True, [self._display_id] if self._display_id else None)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await set_night_screen(self.coordinator, False, [self._display_id] if self._display_id else None)
