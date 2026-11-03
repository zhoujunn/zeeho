"""Zeeho（极核）集成配置流程。"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ZeehoApi, ZeehoApiError, ZeehoAuthError, normalize_token
from .const import CONF_VEHICLE_NAME, CONF_VIN, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _vehicle_label(item: dict[str, Any]) -> str:
    name = (item.get("vehicleName") or "").strip() or "ZEEHO"
    vin = item.get("vinNo") or ""
    tail = vin[-6:] if len(vin) >= 6 else vin
    return f"{name} · {tail}" if tail else name


async def async_test_vehicle(api: ZeehoApi, vin: str) -> str:
    """返回 auth / cannot_connect / 车辆名。"""
    try:
        data = await api.async_get_homepage(vin)
        return data.get("vehicleName") or ""
    except ZeehoAuthError:
        return "auth"
    except ZeehoApiError as err:
        _LOGGER.debug("homepage 连通性失败，回退 widgets：%s", err)
    try:
        data = await api.async_get_widgets(vin)
        return data.get("vehicleName") or ""
    except ZeehoAuthError:
        return "auth"
    except ZeehoApiError as err:
        _LOGGER.error("Zeeho 连通性测试失败：%s", err)
        return "cannot_connect"


class ZeehoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Zeeho 配置流程。"""

    VERSION = 1

    def __init__(self) -> None:
        self._token: str = ""
        self._vehicles: list[dict[str, Any]] = []
        self._reauth_entry: config_entries.ConfigEntry | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return ZeehoOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = normalize_token(user_input[CONF_TOKEN])
            if not token:
                errors["base"] = "auth"
            else:
                api = ZeehoApi(async_get_clientsession(self.hass), token)
                try:
                    vehicles = await api.async_list_vehicles()
                except ZeehoAuthError:
                    errors["base"] = "auth"
                except ZeehoApiError as err:
                    _LOGGER.warning("拉取车辆列表失败，改为手填 VIN：%s", err)
                    self._token = token
                    return await self.async_step_manual()
                else:
                    real = [
                        item
                        for item in vehicles
                        if isinstance(item, dict) and item.get("vinNo")
                    ]
                    self._token = token
                    if not real:
                        return await self.async_step_manual()
                    self._vehicles = real
                    if len(real) == 1:
                        return await self._async_create_from_vehicle(real[0])
                    return await self.async_step_pick_vehicle()

        schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_pick_vehicle(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        choices = {
            item["vinNo"]: _vehicle_label(item) for item in self._vehicles
        }
        if user_input is not None:
            vin = user_input[CONF_VIN]
            match = next((item for item in self._vehicles if item.get("vinNo") == vin), None)
            if match is None:
                errors["base"] = "auth"
            else:
                return await self._async_create_from_vehicle(match)

        schema = vol.Schema({vol.Required(CONF_VIN): vol.In(choices)})
        return self.async_show_form(
            step_id="pick_vehicle", data_schema=schema, errors=errors
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            vin = user_input[CONF_VIN].strip()
            name = (user_input.get(CONF_VEHICLE_NAME) or "").strip()
            if not vin:
                errors["base"] = "auth"
            else:
                api = ZeehoApi(async_get_clientsession(self.hass), self._token)
                result = await async_test_vehicle(api, vin)
                if result == "auth":
                    errors["base"] = "auth"
                elif result == "cannot_connect":
                    errors["base"] = "cannot_connect"
                else:
                    return await self._async_finish(vin, name or result or vin)

        schema = vol.Schema(
            {
                vol.Required(CONF_VIN): str,
                vol.Optional(CONF_VEHICLE_NAME): str,
            }
        )
        return self.async_show_form(step_id="manual", data_schema=schema, errors=errors)

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> FlowResult:
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        entry = self._reauth_entry
        if entry is None:
            return self.async_abort(reason="unknown")
        if user_input is not None:
            token = normalize_token(user_input[CONF_TOKEN])
            api = ZeehoApi(async_get_clientsession(self.hass), token)
            result = await async_test_vehicle(api, entry.data[CONF_VIN])
            if result == "auth":
                errors["base"] = "auth"
            elif result == "cannot_connect":
                errors["base"] = "cannot_connect"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data={**entry.data, CONF_TOKEN: token},
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=schema, errors=errors
        )

    async def _async_create_from_vehicle(self, item: dict[str, Any]) -> FlowResult:
        vin = item["vinNo"].strip()
        name = (item.get("vehicleName") or "").strip() or vin
        return await self._async_finish(vin, name)

    async def _async_finish(self, vin: str, vehicle_name: str) -> FlowResult:
        await self.async_set_unique_id(vin)
        if self._reauth_entry is None:
            self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Zeeho {vehicle_name}",
            data={
                CONF_TOKEN: self._token,
                CONF_VIN: vin,
                CONF_VEHICLE_NAME: vehicle_name,
            },
        )


class ZeehoOptionsFlow(config_entries.OptionsFlow):
    """更新 Token，不删条目。"""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            token = normalize_token(user_input[CONF_TOKEN])
            api = ZeehoApi(async_get_clientsession(self.hass), token)
            result = await async_test_vehicle(
                api, self.config_entry.data[CONF_VIN]
            )
            if result in ("auth", "cannot_connect"):
                errors["base"] = result
            else:
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, CONF_TOKEN: token},
                )
                return self.async_create_entry(title="", data={})

        schema = vol.Schema({vol.Required(CONF_TOKEN): str})
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
