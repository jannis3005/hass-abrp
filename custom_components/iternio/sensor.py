"""Sensor platform for A Better Route Planner."""

from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import API_TELEMETRY_URL, CONF_USER_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    user_token = entry.data[CONF_USER_TOKEN]
    session = async_get_clientsession(hass)

    coordinator = IternioDataUpdateCoordinator(hass, session, user_token)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            IternioPowerSensor(coordinator, entry),
            IternioSocSensor(coordinator, entry),
            IternioSohSensor(coordinator, entry),
        ]
    )


class IternioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        user_token: str,
    ) -> None:
        """Initialize."""
        self.session = session
        self.user_token = user_token

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            async with self.session.get(
                f"{API_TELEMETRY_URL}?token={self.user_token}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error communicating with API: {response.status}")

                data = await response.json()
                result = data.get("result", {})
                telemetry = result.get("telemetry", {})

                return telemetry
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class IternioSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Iternio sensors."""

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Iternio",
            model="A Better Route Planner",
        )


class IternioPowerSensor(IternioSensorBase):
    """Representation of Power sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_power"
        self._attr_name = "Power"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("power")


class IternioSocSensor(IternioSensorBase):
    """Representation of State of Charge sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_soc"
        self._attr_name = "State of Charge"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("soc")


class IternioSohSensor(IternioSensorBase):
    """Representation of State of Health sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_soh"
        self._attr_name = "State of Health"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get("soh")
