import logging
from typing import Any, Dict, Optional
import uuid
import voluptuous as vol
from urllib.parse import urlencode

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import IternioDB, IternioBadAuth, IternioCommunicationError

_LOGGER = logging.getLogger(__name__)

DOMAIN = "iternio"
CONF_API_KEY = "api_key"
CONF_AUTH_CODE = "auth_code"

class IternioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.state: Optional[str] = None
        self.client: Optional[IternioDB] = None
    
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}
        
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY, "").strip()
            
            if not api_key:
                errors["base"] = "invalid_api_key"
            else:
                try:
                    session = async_get_clientsession(self.hass)
                    self.client = IternioDB(session, api_key)
                    
                    self.api_key = api_key
                    
                    return await self.async_step_oauth()
                except Exception as err:
                    _LOGGER.error("Error validating API key: %s", err)
                    errors["base"] = "invalid_api_key"
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
            description_placeholders={
                "learn_more": "https://www.iternio.com/api"
            }
        )
    
    async def async_step_oauth(self, user_input: Optional[Dict[str, Any]] = None):
        if user_input is None:
            self.state = str(uuid.uuid4())
            
            redirect_uri = (
                f"{self.hass.config.internal_url}/auth/external/callback"
            )
            
            oauth_url = await self.client.get_oauth_url(
                client_id="homeassistant",
                redirect_uri=redirect_uri,
                state=self.state
            )
            
            return self.async_external_step(
                step_id="oauth",
                url=oauth_url
            )
        
        auth_code = user_input.get(CONF_AUTH_CODE)
        
        if not auth_code:
            return self.async_abort(reason="auth_failed")
        
        try:
            redirect_uri = (
                f"{self.hass.config.internal_url}/auth/external/callback"
            )
            
            access_token = await self.client.exchange_code_for_token(
                code=auth_code,
                client_id="homeassistant",
                redirect_uri=redirect_uri
            )
            
            self.access_token = access_token
            
            return self.async_create_entry(
                title="Iternio",
                data={
                    CONF_API_KEY: self.api_key,
                    "access_token": self.access_token,
                }
            )
        except IternioBadAuth:
            return self.async_abort(reason="auth_failed")
        except IternioCommunicationError as err:
            _LOGGER.error("Communication error: %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception as err:
            _LOGGER.error("Unexpected error: %s", err)
            return self.async_abort(reason="unknown")
    
    async def async_step_external_step_done(
        self, user_input: Optional[Dict[str, Any]] = None
    ):
        return await self.async_step_oauth(user_input=user_input)
