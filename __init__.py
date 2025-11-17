import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

_LOGGER: logging.Logger = logging.getLogger(__name__)

DOMAIN: Final = "iternio"
PLATFORMS: Final = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    
    # Store the entry
    hass.data[DOMAIN][entry.entry_id] = entry.data
    
    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unloaded
