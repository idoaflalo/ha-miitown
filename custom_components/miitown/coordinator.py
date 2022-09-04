"""DataUpdateCoordinator for the Miitown integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    CONF_AUTHORIZATION,
    DOMAIN,
    LOGGER,
    SPEED_DIGITS,
    UPDATE_INTERVAL,
)
from .miitown_api import MiitownApi
from .utils import AuthError


@dataclass
class MiitownDevice:
    """Miitown Device data."""

    imei: str
    name: str
    last_seen: datetime
    is_connected: bool
    battery_level: int
    is_low_power: bool
    is_driving: bool
    latitude: float
    longitude: float
    height: float
    satellites: int
    speed: float


@dataclass
class MiitownData:
    """Miitown data."""

    devices: dict[str, MiitownDevice] = field(init=False, default_factory=dict)


class MiitownDataUpdateCoordinator(DataUpdateCoordinator[MiitownData]):
    """Miitown data update coordinator."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize data update coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN} ({entry.unique_id})",
            update_interval=UPDATE_INTERVAL,
        )
        self._hass = hass
        self._api = MiitownApi(
            session=async_get_clientsession(hass),
            authorization=entry.data[CONF_AUTHORIZATION],
        )
        self._devices: list[dict] | None = None

    async def _retrieve_data(self, func: str, *args: Any) -> list[dict[str, Any]]:
        """Get data from Miitown."""
        try:
            return await getattr(self._api, func)(*args)
        except AuthError as exc:
            LOGGER.debug("Login error: %s", exc)
            raise ConfigEntryAuthFailed from exc
        except Exception as exc:
            LOGGER.debug("%s: %s", exc.__class__.__name__, exc)
            raise UpdateFailed from exc

    async def _async_update_data(self) -> MiitownData:
        """Get & process data from Miitown."""

        data = MiitownData()

        if not self._devices:
            self._devices = await self._retrieve_data("fetch_devices")

        device_metas = await self._retrieve_data("fetch_devices_data", self._devices)

        for device_meta in device_metas:
            data.devices[device_meta["serialNumber"]] = MiitownDevice(
                device_meta["imei"],
                device_meta["displayName"],
                dt_util.utc_from_timestamp(device_meta["lastSeen"]),
                device_meta["isConnected"],
                int(device_meta["battery"]),
                device_meta["isLowPower"],
                device_meta["isDriving"],
                float(device_meta["latitude"]),
                float(device_meta["longitude"]),
                float(device_meta["height"]),
                int(device_meta["satellites"]),
                round(device_meta["speed"], SPEED_DIGITS),
            )

        return data
