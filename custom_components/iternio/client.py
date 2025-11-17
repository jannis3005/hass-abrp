import aiohttp
import logging
from typing import Any, Optional
import json

_LOGGER = logging.getLogger(__name__)

class IternioBadRequest(Exception):
    pass

class IternioBadAuth(Exception):
    pass

class IternioCommunicationError(Exception):
    pass

class IternioDB:
    BASE_URL = "https://api.iternio.com/1"
    AUTH_URL = "https://abetterrouteplanner.com/oauth/auth"
    TOKEN_URL = "https://api.iternio.com/1/oauth/token"
    
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.session = session
        self.api_key = api_key
        self.access_token: Optional[str] = None
    
    async def get_oauth_url(self, client_id: str, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": client_id,
            "scope": "set_telemetry,get_telemetry",
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "state": state
        }
        
        # Build URL manually to ensure proper formatting
        url = f"{self.AUTH_URL}?"
        url += "&".join([f"{k}={v}" for k, v in params.items()])
        return url
    
    async def exchange_code_for_token(
        self, code: str, client_id: str, redirect_uri: str
    ) -> str:
        try:
            data = {
                "client_id": client_id,
                "client_secret": self.api_key,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
            
            async with self.session.post(self.TOKEN_URL, data=data) as resp:
                if resp.status == 401:
                    raise IternioBadAuth("Invalid credentials")
                if resp.status != 200:
                    raise IternioCommunicationError(f"HTTP {resp.status}")
                
                response_data = await resp.json()
                self.access_token = response_data.get("access_token")
                return self.access_token
        except aiohttp.ClientError as err:
            raise IternioCommunicationError(f"Communication error: {err}")
    
    async def get_telemetry(self) -> dict[str, Any]:
        """Get telemetry data."""
        if not self.access_token:
            raise IternioBadAuth("Not authenticated. Call exchange_code_for_token first.")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.get(
                f"{self.BASE_URL}/telemetry/get",
                headers=headers
            ) as resp:
                if resp.status == 401:
                    raise IternioBadAuth("Token expired or invalid")
                if resp.status == 400:
                    raise IternioBadRequest("Bad request to API")
                if resp.status != 200:
                    raise IternioCommunicationError(f"HTTP {resp.status}")
                
                data = await resp.json()
                return data
        except aiohttp.ClientError as err:
            raise IternioCommunicationError(f"Communication error: {err}")
    
    async def set_telemetry(self, telemetry_data: dict[str, Any]) -> dict[str, Any]:
        """Set telemetry data."""
        if not self.access_token:
            raise IternioBadAuth("Not authenticated. Call exchange_code_for_token first.")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(
                f"{self.BASE_URL}/telemetry/set",
                headers=headers,
                json=telemetry_data
            ) as resp:
                if resp.status == 401:
                    raise IternioBadAuth("Token expired or invalid")
                if resp.status == 400:
                    raise IternioBadRequest("Bad request to API")
                if resp.status != 200:
                    raise IternioCommunicationError(f"HTTP {resp.status}")
                
                data = await resp.json()
                return data
        except aiohttp.ClientError as err:
            raise IternioCommunicationError(f"Communication error: {err}")
