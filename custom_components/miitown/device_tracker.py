"""Support for Miitown device tracking."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from homeassistant.components.device_tracker import SOURCE_TYPE_GPS
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_BATTERY_CHARGING
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_IMEI,
    ATTR_IS_CONNECTED,
    ATTR_DRIVING,
    ATTR_LAST_SEEN,
    ATTR_IS_LOW_POWER,
    ATTR_SPEED,
    ATTR_HEIGHT,
    ATTRIBUTION,
    CONF_DRIVING_SPEED,
    DOMAIN,
    LOGGER, ATTR_SATELLITES,
)
from .coordinator import MiitownDataUpdateCoordinator, MiitownDevice

_LOC_ATTRS = (
    "last_seen",
    "is_connected",
    "is_driving",
    "latitude",
    "longitude",
    "height",
    "satellites",
    "speed",
)


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the device tracker platform."""
    coordinator = hass.data[DOMAIN].coordinators[entry.entry_id]
    devices = hass.data[DOMAIN].devices

    @callback
    def process_data(new_members_only: bool = True) -> None:
        """Process new Miitown data."""
        new_entities = []
        for device_id, device in coordinator.data.devices.items():
            device_by_entry = devices.get(device_id)
            if new_member := not device_by_entry:
                devices[device_id] = entry.entry_id
                LOGGER.debug("Member: %s (%s)", device.name, entry.unique_id)
            if (
                    new_member
                    or device_by_entry == entry.entry_id
                    and not new_members_only
            ):
                new_entities.append(MiitownDeviceTracker(coordinator, device_id))
        if new_entities:
            async_add_entities(new_entities)

    process_data(new_members_only=False)
    entry.async_on_unload(coordinator.async_add_listener(process_data))


class MiitownDeviceTracker(
    CoordinatorEntity[MiitownDataUpdateCoordinator], TrackerEntity
):
    """Miitown Device Tracker."""

    _attr_attribution = ATTRIBUTION
    _attr_unique_id: str

    def __init__(
            self, coordinator: MiitownDataUpdateCoordinator, device_id: str
    ) -> None:
        """Initialize Miitown Entity."""
        super().__init__(coordinator)
        self._attr_unique_id = device_id

        self._data: MiitownDevice | None = coordinator.data.devices[device_id]
        self._prev_data = self._data
        self._attr_name = self._data.name

    @property
    def _options(self) -> Mapping[str, Any]:
        """Shortcut to config entry options."""
        return cast(Mapping[str, Any], self.coordinator.config_entry.options)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.available:
            self._data = self.coordinator.data.devices.get(self._attr_unique_id)
        else:
            self._data = None

        if self._data:
            last_seen = self._data.last_seen
            prev_seen = self._prev_data.last_seen
            bad_last_seen = last_seen < prev_seen
            if bad_last_seen:
                if bad_last_seen:
                    LOGGER.warning(
                        "%s: Ignoring location update because "
                        "last_seen (%s) < previous last_seen (%s)",
                        self.entity_id,
                        last_seen,
                        prev_seen,
                    )
                for attr in _LOC_ATTRS:
                    setattr(self._data, attr, getattr(self._prev_data, attr))

            self._prev_data = self._data

        super()._handle_coordinator_update()

    @property
    def force_update(self) -> bool:
        """Return True if state updates should be forced."""
        return False

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the device.

        Percentage from 0-100.
        """
        if not self._data:
            return None
        return self._data.battery_level

    @property
    def source_type(self) -> str:
        """Return the source type, eg gps or router, of the device."""
        return SOURCE_TYPE_GPS

    @property
    def driving(self) -> bool:
        """Return if driving."""
        if not self._data:
            return False
        if (driving_speed := self._options.get(CONF_DRIVING_SPEED)) is not None:
            if self._data.speed >= driving_speed:
                return True
        return self._data.is_driving

    @property
    def location_name(self) -> str | None:
        """Return a location name for the current location of the device."""
        if self.driving:
            return "Driving"
        return None

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if not self._data:
            return None
        return self._data.latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if not self._data:
            return None
        return self._data.longitude

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        """Return entity specific state attributes."""
        if not self._data:
            return {
                ATTR_IMEI: None,
                ATTR_LAST_SEEN: None,
                ATTR_IS_CONNECTED: None,
                ATTR_IS_LOW_POWER: None,
                ATTR_DRIVING: None,
                ATTR_HEIGHT: None,
                ATTR_SATELLITES: None,
                ATTR_SPEED: None,
            }
        return {
            ATTR_IMEI: self._data.imei,
            ATTR_LAST_SEEN: self._data.last_seen,
            ATTR_IS_CONNECTED: self._data.is_connected,
            ATTR_IS_LOW_POWER: self._data.is_low_power,
            ATTR_DRIVING: self.driving,
            ATTR_HEIGHT: self._data.height,
            ATTR_SATELLITES: self._data.satellites,
            ATTR_SPEED: self._data.speed,
        }
