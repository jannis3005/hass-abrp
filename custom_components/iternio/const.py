"""Constants for the A Better Route Planner integration."""

DOMAIN = "iternio"

# API endpoints
BASE_URL = "https://api.iternio.com/1"
API_ME_URL = f"{BASE_URL}/oauth/me"
API_TELEMETRY_URL = f"{BASE_URL}/tlm/get_telemetry"
API_SEND_TELEMETRY_URL = f"{BASE_URL}/tlm/send"

# Config keys
CONF_API_KEY = "api_key"
CONF_USER_TOKEN = "user_token"
