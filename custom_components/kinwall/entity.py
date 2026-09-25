"""Shared device/entity helpers."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import KinwallCoordinator

FAMILY_DEVICE_KEY = "family"


def member_device_info(entry: ConfigEntry, member_id: str, member_name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_{member_id}")},
        name=member_name,
        manufacturer="Kinwall",
        via_device=(DOMAIN, f"{entry.entry_id}_{FAMILY_DEVICE_KEY}"),
    )


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
