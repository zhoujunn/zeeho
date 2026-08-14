"""Zeeho 二进制传感器：充电中、在线。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VEHICLE_NAME, CONF_VIN, DOMAIN
from .helpers import device_info


def _is_charging(data: dict[str, Any]) -> bool | None:
    flag = data.get("whetherChargeState")
    if flag is True:
        return True
    if flag is False:
        return False
    state = data.get("chargeState")
    if state is None:
        return None
    return str(state) == "1"


def _is_online(data: dict[str, Any]) -> bool | None:
    status = data.get("onlineStatus")
    if status is None:
        return None
    return str(status).upper() == "ONLINE"


@dataclass(kw_only=True)
class ZeehoBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], bool | None]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


BINARY_SENSORS: tuple[ZeehoBinaryDescription, ...] = (
    ZeehoBinaryDescription(
        key="charging",
        name="充电中",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=_is_charging,
        extra_fn=lambda data: {
            key: data[key]
            for key in ("chargeState", "chargeStateStr", "whetherChargeState")
            if key in data
        },
    ),
    ZeehoBinaryDescription(
        key="online",
        name="在线",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=_is_online,
        extra_fn=lambda data: {
            key: data[key]
            for key in ("onlineStatus", "rideState")
            if key in data
        },
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    vin = entry.data[CONF_VIN]
    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, vin)
    async_add_entities(
        [
            ZeehoBinarySensor(coordinator, vin, vehicle_name, description)
            for description in BINARY_SENSORS
        ]
    )


class ZeehoBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator,
        vin: str,
        vehicle_name: str,
        description: ZeehoBinaryDescription,
    ):
        super().__init__(coordinator)
        self.entity_description = description
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vin}_{description.key}"
        self._attr_name = f"Zeeho {vehicle_name} {description.name}"

    @property
    def device_info(self):
        return device_info(self.coordinator, self._vin, self._vehicle_name)

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator.data or {})

    @property
    def extra_state_attributes(self):
        if not self.entity_description.extra_fn:
            return None
        return self.entity_description.extra_fn(self.coordinator.data or {})
