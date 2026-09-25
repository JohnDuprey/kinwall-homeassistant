"""Diagnostics support for Kinwall (API key redacted)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_KINWALL_WEBHOOK_SECRET, DOMAIN
from .coordinator import KinwallCoordinator

TO_REDACT = {"api_key", CONF_KINWALL_WEBHOOK_SECRET}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    coordinator: KinwallCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": dict(entry.options),
        "rev": coordinator.data.rev,
        "member_count": len(coordinator.data.members),
        "calendar_count": len(coordinator.data.calendars),
        "event_count": len(coordinator.data.events),
        "chores_today_count": len(coordinator.data.chores_today),
        "list_count": len(coordinator.data.lists),
    }
