import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_TOKEN
import requests
import logging
from .const import DOMAIN, API_URL, CONF_VIN

_LOGGER = logging.getLogger(__name__)

class ZeehoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            token = user_input[CONF_TOKEN]
            vin = user_input[CONF_VIN]
            vehicle_name = user_input.get("vehicle_name")  # 新增字段

            try:
                data = await self.hass.async_add_executor_job(
                    lambda: requests.get(
                        API_URL + vin,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {token}",
                            "Cfmoto-X-Sign-Type": "0",
                            "Accept": "*/*",
                        },
                        timeout=10,
                    )
                )
                resp = data.json()
                if resp.get("code") != "10000":
                    errors["base"] = "auth"
                else:
                    return self.async_create_entry(
                        title=f"Zeeho {vehicle_name or vin}",
                        data={
                            CONF_TOKEN: token,
                            CONF_VIN: vin,
                            "vehicle_name": vehicle_name or resp["data"].get("vehicleName", vin),
                        },
                    )
            except Exception as e:
                _LOGGER.error("API error: %s", e)
                errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_VIN): str,
                vol.Optional("vehicle_name"): str,  # 新增可选字段
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
