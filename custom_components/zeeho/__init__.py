"""Zeeho（极核）电动车 Home Assistant 集成。"""
import logging
from datetime import timedelta

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_OK_CODE, API_URL, CONF_TOKEN, CONF_VIN, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup(hass: HomeAssistant, config: dict):
    """初始化 zeeho 组件。"""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """根据配置条目设置 zeeho。"""
    session = aiohttp.ClientSession()
    token = entry.data[CONF_TOKEN]
    vin = entry.data[CONF_VIN]
    url = f"{API_URL}{vin}"

    async def async_update_data():
        """从极核 API 拉取车辆数据。"""
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Cfmoto-X-Sign-Type": "0",
            "Accept": "*/*",
        }
        try:
            async with session.get(
                url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status in (401, 403):
                    raise UpdateFailed(
                        "认证失败：token 可能已失效，请删除该集成后重新配置（检查 Token 与 VIN）"
                    )
                if resp.status != 200:
                    raise UpdateFailed(f"API 请求失败：HTTP {resp.status}")
                data = await resp.json()
        except aiohttp.ClientError as err:
            # 网络 / DNS / 连接超时等
            raise UpdateFailed(
                f"网络错误：无法连接 Zeeho API（{type(err).__name__}），请检查服务器网络与 DNS"
            ) from err
        except (ValueError, TypeError) as err:
            raise UpdateFailed(f"API 响应解析失败：{err}") from err

        if data.get("code") != API_OK_CODE:
            raise UpdateFailed(
                f"API 返回错误：code={data.get('code')}，message={data.get('message', '未知')}"
                "（token 可能失效，请重新配置）"
            )
        return data.get("data", {})

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="zeeho coordinator",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await session.close()
        raise

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator, "session": session}

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "device_tracker"])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """卸载配置条目。"""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ["sensor", "device_tracker"]
    )
    if unload_ok:
        session = hass.data[DOMAIN][entry.entry_id].get("session")
        if session is not None and not session.closed:
            await session.close()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
