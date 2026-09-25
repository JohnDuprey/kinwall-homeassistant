"""Kinwall sensors: points today/this week and chores remaining today, per member."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KinwallCoordinator
from .entity import KinwallEntity, member_device_info


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KinwallCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []
    for member in coordinator.data.members:
        entities.append(KinwallPointsSensor(coordinator, entry, member["id"], member["name"], "pointsToday", "points_today"))
        entities.append(KinwallPointsSensor(coordinator, entry, member["id"], member["name"], "pointsWeek", "points_week"))
        entities.append(KinwallChoresRemainingSensor(coordinator, entry, member["id"], member["name"]))
    async_add_entities(entities)


class _MemberSensor(KinwallEntity, SensorEntity):
    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, member_id: str, member_name: str, unique_suffix: str) -> None:
        super().__init__(coordinator, entry, f"{entry.entry_id}_sensor_{member_id}_{unique_suffix}")
        self._member_id = member_id
        self._attr_device_info = member_device_info(entry, member_id, member_name)

    def _member(self) -> dict[str, Any] | None:
        return next((m for m in self.coordinator.data.members if m["id"] == self._member_id), None)


class KinwallPointsSensor(_MemberSensor):
    """Points earned today or this week; resets, so state_class TOTAL (not increasing)."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:star-four-points"

    def __init__(
        self, coordinator: KinwallCoordinator, entry: ConfigEntry, member_id: str, member_name: str, api_field: str, translation_key: str
    ) -> None:
        super().__init__(coordinator, entry, member_id, member_name, translation_key)
        self._api_field = api_field
        self._attr_translation_key = translation_key

    @property
    def native_value(self) -> int | None:
        member = self._member()
        return member.get(self._api_field) if member else None


class KinwallChoresRemainingSensor(_MemberSensor):
    """Count of today's chores not yet completed for this member."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:checkbox-marked-circle-outline"
    _attr_translation_key = "chores_remaining_today"

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, member_id: str, member_name: str) -> None:
        super().__init__(coordinator, entry, member_id, member_name, "chores_remaining_today")

    @property
    def native_value(self) -> int:
        return sum(
            1
            for c in self.coordinator.data.chores_today
            if c.get("memberId") == self._member_id and not c.get("completed")
        )
