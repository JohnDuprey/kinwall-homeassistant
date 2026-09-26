"""One binary sensor per Kinwall chore: on when it has been completed today.

`binary_sensor.<member>_<chore>` is what an automation should look at ("is the after-school checklist
done?") instead of digging through the to-do list's items. Chores added after setup appear after a
reload of the integration.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import KinwallCoordinator
from .entity import KinwallEntity, family_device_info, member_device_info


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: KinwallCoordinator = hass.data[DOMAIN][entry.entry_id]
    members = {m["id"]: m["name"] for m in coordinator.data.members}
    async_add_entities(
        KinwallChoreDoneSensor(coordinator, entry, chore, members.get(chore.get("memberId") or ""))
        for chore in coordinator.data.chores
        if chore.get("active", True)
    )


class KinwallChoreDoneSensor(KinwallEntity, BinarySensorEntity):
    """On once the chore is completed for today; off while it's open or simply not due today."""

    _attr_icon = "mdi:checkbox-marked-circle-outline"

    def __init__(self, coordinator: KinwallCoordinator, entry: ConfigEntry, chore: dict[str, Any], member_name: str | None) -> None:
        super().__init__(coordinator, entry, f"{entry.entry_id}_chore_{chore['id']}")
        self._chore_id = chore["id"]
        self._attr_name = chore["title"]
        member_id = chore.get("memberId")
        self._attr_device_info = (
            member_device_info(entry, member_id, member_name, coordinator.family_device_id) if member_id and member_name else family_device_info(entry, "Family")
        )

    def _today(self) -> dict[str, Any] | None:
        return next((c for c in self.coordinator.data.chores_today if c["id"] == self._chore_id), None)

    def _chore(self) -> dict[str, Any] | None:
        return next((c for c in self.coordinator.data.chores if c["id"] == self._chore_id), None)

    @property
    def available(self) -> bool:
        return super().available and self._chore() is not None

    @property
    def is_on(self) -> bool | None:
        today = self._today()
        return bool(today and today.get("completed"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        chore, today = self._chore() or {}, self._today()
        cl = today.get("checklist") if today else None
        return {
            "chore_id": self._chore_id,
            "member_id": chore.get("memberId"),
            "points": chore.get("points"),
            "due_today": today is not None,
            "completed_at": today.get("completedAt") if today else None,
            "checklist": cl["name"] if cl else None,
            "checklist_done": cl["done"] if cl else None,
            "checklist_total": cl["total"] if cl else None,
        }
