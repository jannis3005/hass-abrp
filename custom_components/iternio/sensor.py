"""Sensor platform for Iternio."""
import logging
from typing import Any
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.exceptions import ConfigEntryAuthFailed

from .client import IternioDB, IternioBadAuth, IternioCommunicationError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "iternio"
SCAN_INTERVAL = timedelta(minutes=5)

# Map Iternio telemetry fields to sensor descriptions
SENSOR_DESCRIPTIONS = {
    "soc": SensorEntityDescription(
        key="soc",
        name="State of Charge",
        unit_of_measurement="%",
        icon="mdi:battery",
    ),
    "range": SensorEntityDescription(
        key="range",
        name="Range",
        unit_of_measurement="km",
        icon="mdi:map-marker-distance",
    ),
    "efficiency": SensorEntityDescription(
        key="efficiency",
        name="Efficiency",
        unit_of_measurement="kWh/100km",
        icon="mdi:flash",
    ),
    "consumption": SensorEntityDescription(
        key="consumption",
        name="Consumption",
        unit_of_measurement="kW",
        icon="mdi:lightning-bolt",
    ),
    "power": SensorEntityDescription(
        key="power",
        name="Power",
        unit_of_measurement="kW",
        icon="mdi:flash",
    ),
    "speed": SensorEntityDescription(
        key="speed",
        name="Speed",
        unit_of_measurement="km/h",
        icon="mdi:speedometer",
    ),
    "elevation": SensorEntityDescription(
        key="elevation",
        name="Elevation",
        unit_of_measurement="m",
        icon="mdi:elevation-rise",
    ),
}


class IternioDat UpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Iternio data."""

    def __init__(self, hass: HomeAssistant, client: IternioDB) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Iternio API."""
        try:
            telemetry = await self.client.get_telemetry()
            return telemetry
        except IternioBadAuth as err:
            raise ConfigEntryAuthFailed from err
        except IternioCommunicationError as err:
            raise err


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Iternio sensor."""
    api_key = entry.data.get("api_key")
    access_token = entry.data.get("access_token")
    
    if not api_key or not access_token:
        _LOGGER.error("Missing API key or access token")
        return
    
    session = async_get_clientsession(hass)
    client = IternioDB(session, api_key)
    client.access_token = access_token
    
    coordinator = IternioDat UpdateCoordinator(hass, client)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Create sensors from telemetry data
    entities = []
    
    if coordinator.data:
        for key, description in SENSOR_DESCRIPTIONS.items():
            if key in coordinator.data:
                entities.append(
                    IternioDatSensor(coordinator, entry, description)
                )
    
    async_add_entities(entities)


class IternioDatSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Iternio sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: IternioDat UpdateCoordinator,
        entry: ConfigEntry,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{entry.entry_id}_{entity_description.key}"
        self._attr_device_name = f"Iternio {entity_description.name}"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        
        value = self.coordinator.data.get(self.entity_description.key)
        return value

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def should_poll(self) -> bool:
        """No polling needed."""
        return False

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()
