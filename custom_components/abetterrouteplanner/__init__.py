"""The A Better Route Planner integration."""

from __future__ import annotations

import json
import time

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_SEND_TELEMETRY_URL, CONF_USER_TOKEN, DOMAIN

PLATFORMS: list[Platform] = [Platform.SENSOR]

SERVICE_SEND_TELEMETRY = "send_telemetry"

TELEMETRY_SCHEMA = vol.Schema(
    {
        vol.Optional("utc"): cv.positive_int,
        vol.Optional("soc"): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
        vol.Optional("soh"): vol.All(vol.Coerce(float), vol.Range(min=0, max=100)),
        vol.Optional("power"): vol.Coerce(float),
        vol.Optional("lat"): vol.Coerce(float),
        vol.Optional("lon"): vol.Coerce(float),
        vol.Optional("heading"): vol.All(vol.Coerce(float), vol.Range(min=0, max=360)),
        vol.Optional("ext_temp"): vol.Coerce(float),
        vol.Optional("batt_temp"): vol.Coerce(float),
        vol.Optional("is_charging"): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up A Better Route Planner from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_send_telemetry(call: ServiceCall) -> None:
        """Handle the send_telemetry service call."""
        user_token = entry.data[CONF_USER_TOKEN]
        session = async_get_clientsession(hass)

        # Build telemetry dict from service call data, excluding None values
        tlm = {k: v for k, v in call.data.items() if v is not None}

        # Add current timestamp if not provided
        if "utc" not in tlm:
            tlm["utc"] = int(time.time())

        # Convert to JSON string
        tlm_json = json.dumps(tlm)

        # Make API call
        url = f"{API_SEND_TELEMETRY_URL}?tlm={tlm_json}"
        headers = {"Authorization": f"APIKEY {user_token}"}

        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    raise Exception(f"API returned status {response.status}")
                result = await response.json()
                if result.get("status") != "ok":
                    raise Exception(f"API returned error: {result}")
        except Exception as err:
            raise Exception(f"Failed to send telemetry: {err}") from err

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_TELEMETRY,
        handle_send_telemetry,
        schema=TELEMETRY_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.services.async_remove(DOMAIN, SERVICE_SEND_TELEMETRY)

    return unload_ok