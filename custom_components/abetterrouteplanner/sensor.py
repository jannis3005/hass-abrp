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
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTemperature, UnitOfPower, UnitOfLength, UnitOfSpeed
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
SCAN_INTERVAL_FAST = timedelta(seconds=15)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    api_key = entry.data[CONF_API_KEY]
    user_token = entry.data[CONF_USER_TOKEN]
    session = async_get_clientsession(hass)

    coordinator = AbrpDataUpdateCoordinator(hass, session, api_key, user_token)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        [
            AbrpPowerSensor(coordinator, entry),
            AbrpSocSensor(coordinator, entry),
            AbrpSohSensor(coordinator, entry),
            AbrpLongitudeSensor(coordinator, entry),
            AbrpLatitudeSensor(coordinator, entry),
            AbrpHeadingSensor(coordinator, entry),
            AbrpExtTempSensor(coordinator, entry),
            AbrpBattTempSensor(coordinator, entry),
            AbrpTimestampSensor(coordinator, entry),
            AbrpTelemetryTypeSensor(coordinator, entry),
            AbrpOdometerSensor(coordinator, entry),
            AbrpEstBatteryRangeSensor(coordinator, entry),
            AbrpSpeedSensor(coordinator, entry),
            AbrpElevationSensor(coordinator, entry),
            AbrpCalibratedReferenceConsumptionSensor(coordinator, entry)
        ]
    )


class AbrpDataUpdateCoordinator(DataUpdateCoordinator):
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

                if timestamp := result.get("timestamp"):
                    telemetry["timestamp"] = timestamp
                    try:
                        ts = dt_util.parse_datetime(timestamp)
                        if ts:
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=dt_util.UTC)

                            if dt_util.utcnow() - ts < SCAN_INTERVAL:
                                self.update_interval = SCAN_INTERVAL_FAST
                            else:
                                self.update_interval = SCAN_INTERVAL
                    except (ValueError, TypeError):
                        pass
                if telemetry_type := result.get("telemetry_type"):
                    telemetry["telemetry_type"] = telemetry_type

                return telemetry
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class AbrpSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Abrp sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpPowerSensor(AbrpSensorBase):
    """Representation of Power sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:lightning-bolt"
    _attr_translation_key = "power"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpSocSensor(AbrpSensorBase):
    """Representation of State of Charge sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "soc"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpSohSensor(AbrpSensorBase):
    """Representation of State of Health sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:heart-pulse"
    _attr_translation_key = "soh"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpLongitudeSensor(AbrpSensorBase):
    """Representation of Longitude sensor."""

    _attr_icon = "mdi:map-marker"
    _attr_translation_key = "longitude"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpLatitudeSensor(AbrpSensorBase):
    """Representation of Latitude sensor."""

    _attr_icon = "mdi:map-marker"
    _attr_translation_key = "latitude"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpHeadingSensor(AbrpSensorBase):
    """Representation of Heading sensor."""

    _attr_icon = "mdi:compass"
    _attr_native_unit_of_measurement = "°"
    _attr_translation_key = "heading"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpExtTempSensor(AbrpSensorBase):
    """Representation of External Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "ext_temp"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpBattTempSensor(AbrpSensorBase):
    """Representation of Battery Temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_translation_key = "batt_temp"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpTimestampSensor(AbrpSensorBase):
    """Representation of Timestamp sensor."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-outline"
    _attr_translation_key = "timestamp"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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


class AbrpTelemetryTypeSensor(AbrpSensorBase):
    """Representation of Telemetry Type sensor."""

    _attr_icon = "mdi:information-outline"
    _attr_translation_key = "telemetry_type"

    def __init__(
        self,
        coordinator: AbrpDataUpdateCoordinator,
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

class AbrpOdometerSensor(AbrpSensorBase):
    """Representation of Odometer sensor."""

    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:measuring_tape"
    _attr_translation_key = "odometer"

    def __init__(
            self,
            coordinator: AbrpDataUpdateCoordinator,
            entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_odometer"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if odometer := self.coordinator.data.get("odometer"):
            return odometer
        return None

class AbrpEstBatteryRangeSensor(AbrpSensorBase):
    """Representation of Estimated Battery Range sensor."""

    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:arrow_range"
    _attr_translation_key = "est_battery_range"

    def __init__(
            self,
            coordinator: AbrpDataUpdateCoordinator,
            entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_est_battery_range"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if est_battery_range := self.coordinator.data.get("est_battery_range"):
            return est_battery_range
        return None

class AbrpSpeedSensor(AbrpSensorBase):
    """Representation of Speed sensor."""

    _attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_device_class = SensorDeviceClass.SPEED
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:speed"
    _attr_translation_key = "speed"

    def __init__(
            self,
            coordinator: AbrpDataUpdateCoordinator,
            entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_speed"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if speed := self.coordinator.data.get("speed"):
            return speed
        return None

class AbrpElevationSensor(AbrpSensorBase):
    """Representation of Elevation sensor."""

    _attr_native_unit_of_measurement = UnitOfLength.METERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:altitude"
    _attr_translation_key = "elevation"

    def __init__(
            self,
            coordinator: AbrpDataUpdateCoordinator,
            entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_elevation"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if elevation := self.coordinator.data.get("elevation"):
            return elevation
        return None

class AbrpCalibratedReferenceConsumptionSensor(AbrpSensorBase):
    """Representation of Calibrated Reference Consumption sensor."""

    _attr_native_unit_of_measurement = f"{UnitOfEnergy.WATT_HOUR}/{UnitOfLength.KILOMETERS}"
    _attr_device_class = SensorDeviceClass.ENERGY_DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:area_chart"
    _attr_translation_key = "calib_ref_cons"

    def __init__(
            self,
            coordinator: AbrpDataUpdateCoordinator,
            entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_calib_ref_cons"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if calib_ref_cons := self.coordinator.data.get("calib_ref_cons"):
            return calib_ref_cons
        return None