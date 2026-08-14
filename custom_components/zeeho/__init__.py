"""Zeeho（极核）电动车 Home Assistant 集成。"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ZeehoApi, normalize_token
from .const import CONF_TOKEN, CONF_VIN, DOMAIN, PLATFORMS
from .coordinator import ZeehoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """YAML 占位，实际走 config entry。"""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """根据配置条目设置 zeeho。"""
    session = async_get_clientsession(hass)
    api = ZeehoApi(session, entry.data[CONF_TOKEN])
    coordinator = ZeehoDataUpdateCoordinator(hass, api, entry.data[CONF_VIN])

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
    }

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """卸载配置条目。"""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Token 等配置变更后整条目重载。"""
    stored = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if stored:
        stored["api"].token = normalize_token(entry.data[CONF_TOKEN])
    await hass.config_entries.async_reload(entry.entry_id)
