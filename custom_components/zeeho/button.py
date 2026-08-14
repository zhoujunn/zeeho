"""Zeeho 寻车按钮。"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import ZeehoApiError, ZeehoAuthError
from .const import CONF_VEHICLE_NAME, CONF_VIN, DOMAIN
from .helpers import device_info

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ZeehoButtonDescription(ButtonEntityDescription):
    press_fn: Callable[[Any, str], Coroutine[Any, Any, Any]]


BUTTONS: tuple[ZeehoButtonDescription, ...] = (
    ZeehoButtonDescription(
        key="find_car",
        name="短按寻车",
        icon="mdi:bell-ring-outline",
        press_fn=lambda api, vin: api.async_find_car(vin),
    ),
    ZeehoButtonDescription(
        key="loud_find_car",
        name="高声寻车",
        icon="mdi:bullhorn",
        press_fn=lambda api, vin: api.async_loud_find_car(vin),
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]
    vin = entry.data[CONF_VIN]
    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, vin)
    async_add_entities(
        [
            ZeehoButton(coordinator, vin, vehicle_name, description)
            for description in BUTTONS
        ]
    )


class ZeehoButton(CoordinatorEntity, ButtonEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, vin: str, vehicle_name: str, description: ZeehoButtonDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vin}_{description.key}"
        self._attr_name = f"Zeeho {vehicle_name} {description.name}"

    @property
    def device_info(self):
        return device_info(self.coordinator, self._vin, self._vehicle_name)

    async def async_press(self) -> None:
        try:
            await self.entity_description.press_fn(self.coordinator.api, self._vin)
        except ZeehoAuthError as err:
            raise HomeAssistantError(str(err)) from err
        except ZeehoApiError as err:
            _LOGGER.warning("寻车失败：%s", err)
            raise HomeAssistantError(str(err)) from err
        await self.coordinator.async_request_refresh()
