"""Constants for Miitown integration."""

from datetime import timedelta
import logging

DOMAIN = "miitown"
LOGGER = logging.getLogger(__package__)

ATTRIBUTION = "Data provided by miitown.com"
SPEED_DIGITS = 1
UPDATE_INTERVAL = timedelta(seconds=10)

ATTR_IMEI = "imei"
ATTR_IS_CONNECTED = "is_connected"
ATTR_DRIVING = "driving"
ATTR_LAST_SEEN = "last_seen"
ATTR_IS_LOW_POWER = "is_low_power"
ATTR_SPEED = "speed"
ATTR_HEIGHT = "height"
ATTR_SATELLITES = "satellites"

CONF_AUTHORIZATION = "authorization"
CONF_DRIVING_SPEED = "driving_speed"

DEFAULT_OPTIONS = {
    CONF_DRIVING_SPEED: None,
}

OPTIONS = list(DEFAULT_OPTIONS.keys())

# REST API
BASE_URL = "https://miitown.com"
LOGIN_PATH = "/api-user/user/login"
DEVICES_PATH = "/api-device/device-gps/all"
STATUS_PATH = "/api-gps/last/all/status"
