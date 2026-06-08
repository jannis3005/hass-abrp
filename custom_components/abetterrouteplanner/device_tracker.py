"""Device tracker platform for A Better Route Planner."""

from __future__ import annotations

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AbrpDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device tracker platform."""
    coordinator: AbrpDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]

    async_add_entities([AbrpDeviceTracker(coordinator, entry)])


class AbrpDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Representation of the vehicle location as a device tracker."""

    _attr_has_entity_name = True
    _attr_translation_key = "location"
    _attr_icon = "mdi:car"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_location"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Iternio",
            model="A Better Route Planner",
        )

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device tracker."""
        return SourceType.GPS

    @property
    def latitude(self) -> float | None:
        """Return the latitude of the vehicle."""
        return self.coordinator.data.get("lat")

    @property
    def longitude(self) -> float | None:
        """Return the longitude of the vehicle."""
        return self.coordinator.data.get("lon")
