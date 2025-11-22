"""Sensor platform for A Better Route Planner."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging

import aiohttp

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import API_TELEMETRY_URL, CONF_API_KEY, CONF_USER_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    api_key = entry.data[CONF_API_KEY]
    user_token = entry.data[CONF_USER_TOKEN]
    session = async_get_clientsession(hass)

    coordinator = IternioDataUpdateCoordinator(hass, session, api_key, user_token)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            IternioPowerSensor(coordinator, entry),
            IternioSocSensor(coordinator, entry),
            IternioSohSensor(coordinator, entry),
            IternioLongitudeSensor(coordinator, entry),
            IternioLatitudeSensor(coordinator, entry),
            IternioHeadingSensor(coordinator, entry),
            IternioExtTempSensor(coordinator, entry),
            IternioBattTempSensor(coordinator, entry),
            IternioTimestampSensor(coordinator, entry),
            IternioTelemetryTypeSensor(coordinator, entry),
        ]
    )


class IternioDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        user_token: str,
    ) -> None:
        """Initialize."""
        self.session = session
        self.api_key = api_key
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
            headers = {"Authorization": f"APIKEY {self.api_key}"}
            async with self.session.get(
                f"{API_TELEMETRY_URL}?token={self.user_token}",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise UpdateFailed(f"Error communicating with API: {response.status}")

                data = await response.json()
                result = data.get("result", {})
                telemetry = result.get("telemetry", {})

                # Add timestamp and telemetry_type from result level to telemetry data
                if timestamp := result.get("timestamp"):
                    telemetry["timestamp"] = timestamp
                if telemetry_type := result.get("telemetry_type"):
                    telemetry["telemetry_type"] = telemetry_type

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

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:lightning-bolt"
    _attr_translation_key = "power"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_power"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        power = self.coordinator.data.get("power")
        if power is not None:
            return power
        return None


class IternioSocSensor(IternioSensorBase):
    """Representation of State of Charge sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "soc"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_soc"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if soc := self.coordinator.data.get("soc"):
            return soc
        return None


class IternioSohSensor(IternioSensorBase):
    """Representation of State of Health sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:heart-pulse"
    _attr_translation_key = "soh"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_soh"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if soh := self.coordinator.data.get("soh"):
            return soh
        return None


class IternioLongitudeSensor(IternioSensorBase):
    """Representation of Longitude sensor."""

    _attr_icon = "mdi:map-marker"
    _attr_translation_key = "longitude"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_longitude"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if lon := self.coordinator.data.get("lon"):
            return lon
        return None


class IternioLatitudeSensor(IternioSensorBase):
    """Representation of Latitude sensor."""

    _attr_icon = "mdi:map-marker"
    _attr_translation_key = "latitude"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_latitude"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if lat := self.coordinator.data.get("lat"):
            return lat
        return None


class IternioHeadingSensor(IternioSensorBase):
    """Representation of Heading sensor."""

    _attr_icon = "mdi:compass"
    _attr_native_unit_of_measurement = "°"
    _attr_translation_key = "heading"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_heading"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if heading := self.coordinator.data.get("heading"):
            return heading
        return None


class IternioExtTempSensor(IternioSensorBase):
    """Representation of External Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "ext_temp"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ext_temp"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        ext_temp = self.coordinator.data.get("ext_temp")
        if ext_temp is not None:
            return ext_temp
        return None


class IternioBattTempSensor(IternioSensorBase):
    """Representation of Battery Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "batt_temp"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_batt_temp"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        batt_temp = self.coordinator.data.get("batt_temp")
        if batt_temp is not None:
            return batt_temp
        return None


class IternioTimestampSensor(IternioSensorBase):
    """Representation of Timestamp sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"
    _attr_translation_key = "timestamp"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_timestamp"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if timestamp_str := self.coordinator.data.get("timestamp"):
            try:
                # Parse the timestamp string to datetime
                return dt_util.parse_datetime(timestamp_str)
            except (ValueError, TypeError):
                _LOGGER.warning("Failed to parse timestamp: %s", timestamp_str)
                return None
        return None


class IternioTelemetryTypeSensor(IternioSensorBase):
    """Representation of Telemetry Type sensor."""

    _attr_icon = "mdi:information-outline"
    _attr_translation_key = "telemetry_type"

    def __init__(
        self,
        coordinator: IternioDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_telemetry_type"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if telemetry_type := self.coordinator.data.get("telemetry_type"):
            return telemetry_type
        return None
