"""Zeeho 数据协调器。"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ZeehoApi, ZeehoApiError, ZeehoAuthError
from .const import DOMAIN, SCAN_INTERVAL, TIRE_POS_FRONT, TIRE_POS_REAR

_LOGGER = logging.getLogger(__name__)

_BATTERY_FALLBACK_KEYS = (
    "power",
    "voltage",
    "current",
    "chargeStateStr",
    "whetherChargeState",
    "chargeState",
    "fullChargeTime",
    "fullChargeTimeSecond",
)


def _flatten_tire(tire: dict[str, Any]) -> dict[str, Any]:
    extra: dict[str, Any] = {"tire": tire, "tireUpdateTime": tire.get("updateTime")}
    for item in tire.get("realTimeData") or []:
        if not isinstance(item, dict):
            continue
        position = item.get("sensorPosition")
        if position == TIRE_POS_FRONT:
            prefix = "front"
        elif position == TIRE_POS_REAR:
            prefix = "rear"
        else:
            continue
        extra[f"{prefix}TirePressure"] = item.get("tirePressure")
        extra[f"{prefix}TireTemp"] = item.get("tireTemp")
        extra[f"{prefix}TireWarning"] = item.get("warningType")
        extra[f"{prefix}TireReportTime"] = item.get("reportTime")
        extra[f"{prefix}TireSensorId"] = item.get("sensorId")
    return extra


def _merge_vehicle_data(
    homepage: dict[str, Any] | None,
    widgets: dict[str, Any] | None,
    battery: dict[str, Any] | None,
    tire: dict[str, Any] | None = None,
    signin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = dict(homepage or {})
    if widgets:
        for key, value in widgets.items():
            if key == "address":
                if value:
                    data["address"] = value
                continue
            if key not in data or data[key] in (None, ""):
                data[key] = value
    if battery:
        data["batteryInfo"] = battery
        for key in _BATTERY_FALLBACK_KEYS:
            if key in battery and (key not in data or data[key] in (None, "")):
                data[key] = battery[key]
    if tire:
        data.update(_flatten_tire(tire))
    if signin:
        if "signStatus" in signin:
            data["signStatus"] = signin.get("signStatus")
        count = signin.get("count")
        if count in (None, ""):
            data["signCount"] = 0 if "signStatus" in signin else None
        else:
            data["signCount"] = count
    return data


class ZeehoDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """合并 homepage / widgets / batteryInfo / 胎压 / 签到。"""

    def __init__(self, hass: HomeAssistant, api: ZeehoApi, vin: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} coordinator",
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self.vin = vin

    async def _async_update_data(self) -> dict[str, Any]:
        homepage: dict[str, Any] | None = None
        widgets: dict[str, Any] | None = None
        battery: dict[str, Any] | None = None
        tire: dict[str, Any] | None = None
        signin: dict[str, Any] | None = None
        homepage_error: Exception | None = None
        widgets_error: Exception | None = None

        try:
            homepage = await self.api.async_get_homepage(self.vin)
        except ZeehoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ZeehoApiError as err:
            homepage_error = err
            _LOGGER.warning("拉取车辆首页失败：%s", err)

        try:
            widgets = await self.api.async_get_widgets(self.vin)
        except ZeehoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ZeehoApiError as err:
            widgets_error = err
            _LOGGER.debug("拉取 widgets 失败（地址可能不可用）：%s", err)

        try:
            battery = await self.api.async_get_battery(self.vin)
        except ZeehoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ZeehoApiError as err:
            _LOGGER.debug("拉取电池信息失败：%s", err)

        try:
            tire = await self.api.async_get_tire(self.vin)
        except ZeehoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ZeehoApiError as err:
            _LOGGER.debug("拉取胎压失败：%s", err)

        try:
            signin = await self.api.async_get_signin()
        except ZeehoAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ZeehoApiError as err:
            _LOGGER.debug("拉取签到状态失败：%s", err)

        if homepage is None and widgets is None:
            raise UpdateFailed(
                str(homepage_error or widgets_error or "无法获取车辆数据")
            )

        return _merge_vehicle_data(homepage, widgets, battery, tire, signin)
