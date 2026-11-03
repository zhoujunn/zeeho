"""Zeeho 云端车锁。"""

from __future__ import annotations

import logging

from homeassistant.components.lock import LockEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ZeehoApiError, ZeehoAuthError
from .const import CONF_VEHICLE_NAME, CONF_VIN, DOMAIN
from .helpers import device_info

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]
    vin = entry.data[CONF_VIN]
    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, vin)
    async_add_entities([ZeehoNetworkLock(coordinator, vin, vehicle_name)])


class ZeehoNetworkLock(CoordinatorEntity, LockEntity):
    """POST /vehicleSet/network/unlock，状态跟 headLockState。"""

    _attr_has_entity_name = False

    def __init__(self, coordinator, vin: str, vehicle_name: str) -> None:
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vin}_network_lock"
        self._attr_name = f"Zeeho {vehicle_name} 云端车锁"
        self._attr_icon = "mdi:lock"

    @property
    def device_info(self):
        return device_info(self.coordinator, self._vin, self._vehicle_name)

    @property
    def is_locked(self) -> bool | None:
        state = (self.coordinator.data or {}).get("headLockState")
        if state is None or state == "":
            return None
        return str(state) == "1"

    async def _async_set_lock(self, lock_flag: int, label: str) -> None:
        try:
            await self.coordinator.api.async_network_lock(self._vin, lock_flag)
        except ZeehoAuthError as err:
            raise HomeAssistantError(str(err)) from err
        except ZeehoApiError as err:
            _LOGGER.warning("%s失败：%s", label, err)
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()

    async def async_lock(self, **kwargs) -> None:
        await self._async_set_lock(0, "关锁")

    async def async_unlock(self, **kwargs) -> None:
        await self._async_set_lock(1, "开锁")
