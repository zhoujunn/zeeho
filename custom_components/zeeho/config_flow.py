"""Zeeho（极核）集成配置流程。"""
import logging

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN

from .const import API_OK_CODE, API_URL, CONF_VIN, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ZeehoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Zeeho 配置流程。"""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN].strip()
            vin = user_input[CONF_VIN].strip()
            vehicle_name = (user_input.get("vehicle_name") or "").strip()

            if not token or not vin:
                errors["base"] = "auth"
            else:
                # 同一 VIN 只允许配置一次
                await self.async_set_unique_id(vin)
                self._abort_if_unique_id_configured()
                for existing in self._async_current_entries():
                    if existing.data.get(CONF_VIN) == vin:
                        return self.async_abort(reason="already_configured")

                result = await self._test_connection(token, vin)
                if result == "auth":
                    errors["base"] = "auth"
                elif result == "cannot_connect":
                    errors["base"] = "cannot_connect"
                else:
                    return self.async_create_entry(
                        title=f"Zeeho {vehicle_name or vin}",
                        data={
                            CONF_TOKEN: token,
                            CONF_VIN: vin,
                            "vehicle_name": vehicle_name or result or vin,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_VIN): str,
                vol.Optional("vehicle_name"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def _test_connection(self, token, vin):
        """测试与极核 API 的连通性。

        返回 "auth"（认证失败）、"cannot_connect"（网络失败）或 API 返回的车辆名。
        """
        def _request():
            return requests.get(
                API_URL + vin,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                    "Cfmoto-X-Sign-Type": "0",
                    "Accept": "*/*",
                },
                timeout=15,
            )

        try:
            resp = await self.hass.async_add_executor_job(_request)
        except requests.RequestException as err:
            _LOGGER.error("Zeeho 连通性测试失败：%s", err)
            return "cannot_connect"

        if resp.status_code in (401, 403):
            _LOGGER.error("Zeeho 连通性测试返回 HTTP %s（token 可能失效）", resp.status_code)
            return "auth"
        if resp.status_code != 200:
            _LOGGER.error("Zeeho 连通性测试返回 HTTP %s", resp.status_code)
            return "cannot_connect"

        try:
            body = resp.json()
        except ValueError:
            _LOGGER.error("Zeeho 连通性测试返回非 JSON 内容")
            return "cannot_connect"

        if body.get("code") != API_OK_CODE:
            _LOGGER.error(
                "Zeeho 连通性测试失败：code=%s，message=%s",
                body.get("code"),
                body.get("message"),
            )
            return "auth"

        return body.get("data", {}).get("vehicleName") or ""
