"""Data update coordinator for A Better Route Planner."""

from __future__ import annotations

from datetime import timedelta
import logging

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import API_TELEMETRY_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)
SCAN_INTERVAL_FAST = timedelta(seconds=15)


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
