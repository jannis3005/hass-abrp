# Iternio Home Assistant Integration

This is a custom Home Assistant integration for the Iternio API that allows you to retrieve and display telemetry data from your vehicle.

## Features

- OAuth2-based authentication with Iternio
- Automatic token exchange with API key
- Real-time telemetry data retrieval (SOC, range, efficiency, consumption, power, speed, elevation)
- Automatic entity creation based on available telemetry data
- Scheduled updates every 5 minutes
- HACS-compatible installation

## Installation

### Prerequisites

- An Iternio API key (get it from [https://www.iternio.com/api](https://www.iternio.com/api))

### Via HACS (Recommended)

1. Install HACS if you haven't already
2. Go to HACS → Integrations → Custom repositories
3. Add this repository: `https://gitlab.jannis-goeing.de/Jannis3005/hass-abrp/-/tree/master`
4. Search for "Iternio" and click Install
5. Restart Home Assistant
