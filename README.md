# A Better Route Planner Home Assistant Integration

This is a custom Home Assistant integration for the Iternio API that allows you to 
retrieve and display telemetry data from your vehicle 
from the A Better Route Planner app.

## Features

- Telemetry data retrieval (SOC, power, and more to come)
- Automatic entity creation based on available telemetry data
- Scheduled updates every 5 minutes
- HACS-compatible installation

## Installation

### Via HACS (Recommended)

1. Add this repository URL: `https://github.com/jannis3005/hass-abrp` as a Custom Repository to HACS
2. Install the Integration
3. Restart Home Assistant
4. Add the Integration

## Configuration

### Step 1: Get your Iternio API Key

1. Go to [https://www.iternio.com/api](https://www.iternio.com/api)
2. Follow the steps described there to get a free API Key

### Step 2: Create a User Token

1. Open the ABRP app or go to [https://abetterrouteplanner.com](https://abetterrouteplanner.com)
2. Log in if you haven't already
2. Navigate to your car settings
3. Click **"Edit Car Connection Details"**
4. Under **"Generic"** as the car connection type, click **"Link"**
6. This will create and display your User Token
7. Copy the User Token for use in Home Assistant

### Step 3: Add the Integration in Home Assistant

1. Go to Settings -> Devices & Services
2. Click "Add Integration"
3. Search for "A Better Route Planner"
4. Enter your **API Key** and **User Token** when prompted
5. Click Submit