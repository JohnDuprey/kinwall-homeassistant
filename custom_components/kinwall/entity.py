"""Shared device/entity helpers."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KinwallCoordinator

FAMILY_DEVICE_KEY = "family"

# The Kinwall feature switch behind each entity, by its unique ID after "<entry_id>_": the
# points/chores-remaining sensors, chore binary sensors and chore to-do lists, and the list to-dos.
FEATURE_BY_UNIQUE_ID = {"sensor_": "chores", "chore_": "chores", "todo_": "chores", "list_": "lists"}


def feature_of(entry: ConfigEntry, unique_id: str) -> str | None:
    rest = unique_id.removeprefix(f"{entry.entry_id}_")
    return next((f for prefix, f in FEATURE_BY_UNIQUE_ID.items() if rest.startswith(prefix)), None)


def member_device_info(entry: ConfigEntry, member_id: str, member_name: str, family_device_id: str | None = None) -> DeviceInfo:
    info = DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{member_id}")},
        name=member_name,
        manufacturer="Kinwall",
    )
    # The Family device is created in __init__ before any platform loads. HA 2026.x deprecates
    # via_device (removed in 2027.8) in favour of via_device_id; older cores only know the former.
    if "via_device_id" in DeviceInfo.__annotations__:
        if family_device_id:
            info["via_device_id"] = family_device_id
    else:
        info["via_device"] = (DOMAIN, f"{entry.entry_id}_{FAMILY_DEVICE_KEY}")
    return info


def family_device_info(entry: ConfigEntry, family_name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{FAMILY_DEVICE_KEY}")},
        name=family_name,
        manufacturer="Kinwall",
    )


class KinwallEntity(CoordinatorEntity[KinwallCoordinator]):
    """Base entity: has_entity_name + attaches to a device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, unique_id: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = unique_id
        self._feature = feature_of(entry, unique_id)

    @property
    def available(self) -> bool:
        # Unavailable from the moment the family turns its feature off until the reload removes it.
        return super().available and self.coordinator.feature_on(self._feature)
