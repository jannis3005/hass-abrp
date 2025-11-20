"""Config flow for A Better Route Planner."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_ME_URL, CONF_API_KEY, CONF_USER_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class IternioConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for A Better Route Planner."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            api_key = user_input[CONF_API_KEY]
            user_token = user_input[CONF_USER_TOKEN]

            # Validate the credentials
            try:
                session = async_get_clientsession(self.hass)
                vehicle_name = await self._test_credentials(session, user_token)

                # Check if already configured
                await self.async_set_unique_id(user_token)
                self._abort_if_unique_id_configured()

                # Create the entry
                return self.async_create_entry(
                    title=vehicle_name,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_USER_TOKEN: user_token,
                    },
                )
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_API_KEY): str,
                    vol.Required(CONF_USER_TOKEN): str,
                }
            ),
            errors=errors,
        )

    async def _test_credentials(
        self, session: aiohttp.ClientSession, user_token: str
    ) -> str:
        """Validate credentials and return vehicle name."""
        try:
            async with session.get(
                f"{API_ME_URL}?access_token={user_token}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status != 200:
                    raise InvalidAuth

                data = await response.json()

                if data.get("status") != "ok":
                    raise InvalidAuth

                vehicle_name = data.get("vehicle_name")
                if not vehicle_name:
                    raise InvalidAuth

                return vehicle_name
        except aiohttp.ClientError as err:
            raise CannotConnect from err


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
