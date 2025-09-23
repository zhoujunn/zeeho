import logging
from datetime import timedelta
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    session = aiohttp.ClientSession()

    async def async_update_data():
        try:
            url = f"https://tapi.zeehoev.com/v1.0/app/cfmotoserverapp/vehicle/widgets/{entry.data['vin']}"
            headers = {
                "Authorization": f"Bearer {entry.data['token']}",
                "Content-Type": "application/json",
                "Cfmoto-X-Sign-Type": "0",
                "Accept": "*/*",
            }
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()
                return data.get("data", {})
        except Exception as err:
            raise UpdateFailed(err)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="zeeho coordinator",
        update_method=async_update_data,
        update_interval=timedelta(minutes=1),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "session": session}

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "device_tracker"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "device_tracker"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
