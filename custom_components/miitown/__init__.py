"""Miitown integration."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

import voluptuous as vol

from homeassistant.components.device_tracker import CONF_SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DRIVING_SPEED,
    CONF_DEVICES,
    DOMAIN,
)
from .coordinator import MiitownDataUpdateCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER]

CONF_ACCOUNTS = "accounts"

ACCOUNT_SCHEMA = {
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
}

MIITOWN_SCHEMA = vol.All(
    vol.Schema(
        {
            vol.Optional(CONF_ACCOUNTS): vol.All(cv.ensure_list, [ACCOUNT_SCHEMA]),
            vol.Optional(CONF_DRIVING_SPEED): vol.Coerce(float),
            vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
        }
    )
)
CONFIG_SCHEMA = vol.Schema(
    vol.All({DOMAIN: MIITOWN_SCHEMA}, cv.removed(DOMAIN, raise_if_present=False)),
    extra=vol.ALLOW_EXTRA,
)


@dataclass
class IntegrationData:
    """Integration data."""

    cfg_options: dict[str, Any] | None = None
    # ConfigEntry.entry_id: MiitownDataUpdateCoordinator
    coordinators: dict[str, MiitownDataUpdateCoordinator] = field(
        init=False, default_factory=dict
    )
    # serial_number: ConfigEntry.entry_id
    devices: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self):
        """Finish initialization of cfg_options."""
        self.cfg_options = self.cfg_options or {}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up integration."""
    hass.data.setdefault(DOMAIN, IntegrationData(config.get(DOMAIN)))
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up config entry."""
    hass.data.setdefault(DOMAIN, IntegrationData())

    coordinator = MiitownDataUpdateCoordinator(hass, entry)

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN].coordinators[entry.entry_id] = coordinator

    # Set up components for our platforms.
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""

    # Unload components for our platforms.
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        del hass.data[DOMAIN].coordinators[entry.entry_id]
        # Remove any devices that were tracked by this entry.
        for device_id, entry_id in hass.data[DOMAIN].devices.copy().items():
            if entry_id == entry.entry_id:
                del hass.data[DOMAIN].devices[device_id]

    return unload_ok
