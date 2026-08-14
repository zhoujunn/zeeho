"""Zeeho tapi.zeehoev.com 客户端。只使用 Token + VIN，不签名。"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

from .const import (
    API_HOST,
    API_OK_CODE,
    PATH_BATTERY,
    PATH_FIND_CAR,
    PATH_HOMEPAGE,
    PATH_LOUD_FIND,
    PATH_VEHICLE_LIST,
    PATH_WIDGETS,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class ZeehoAuthError(Exception):
    """Token 失效或无权限。"""


class ZeehoApiError(Exception):
    """业务或网络错误。"""

    def __init__(self, message: str, *, status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.status = status
        self.code = code


def normalize_token(token: str) -> str:
    """去掉用户可能一并粘贴的 Bearer 前缀。"""
    value = (token or "").strip()
    if value.lower().startswith("bearer "):
        return value[7:].strip()
    return value


class ZeehoApi:
    """极核云端 API。"""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self.token = normalize_token(token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Cfmoto-X-Sign-Type": "0",
            "Accept": "*/*",
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        empty_body: bool = False,
    ) -> Any:
        url = f"{API_HOST}{path}"
        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        kwargs: dict[str, Any] = {
            "headers": self._headers(),
            "timeout": timeout,
        }
        if empty_body:
            kwargs["data"] = b""
        elif json_body is not None:
            kwargs["json"] = json_body

        try:
            async with self._session.request(method, url, **kwargs) as resp:
                if resp.status in (401, 403):
                    raise ZeehoAuthError(
                        f"认证失败：token 可能已失效（HTTP {resp.status}）"
                    )
                if resp.status != 200:
                    raise ZeehoApiError(
                        f"API 请求失败：HTTP {resp.status}", status=resp.status
                    )
                try:
                    payload = await resp.json(content_type=None)
                except (ValueError, TypeError) as err:
                    raise ZeehoApiError(f"API 响应解析失败：{err}") from err
        except aiohttp.ClientError as err:
            raise ZeehoApiError(
                f"网络错误：无法连接 Zeeho API（{type(err).__name__}）"
            ) from err

        if not isinstance(payload, dict):
            raise ZeehoApiError("API 响应不是对象")

        code = payload.get("code")
        if code != API_OK_CODE:
            raise ZeehoApiError(
                f"API 返回错误：code={code}，message={payload.get('message', '未知')}",
                code=str(code) if code is not None else None,
            )
        return payload.get("data")

    async def async_list_vehicles(self) -> list[dict[str, Any]]:
        data = await self._request("GET", PATH_VEHICLE_LIST)
        if data is None:
            return []
        if isinstance(data, list):
            return data
        raise ZeehoApiError("车辆列表响应格式异常")

    async def async_get_homepage(self, vin: str) -> dict[str, Any]:
        data = await self._request("GET", PATH_HOMEPAGE.format(vin=vin))
        return data if isinstance(data, dict) else {}

    async def async_get_widgets(self, vin: str) -> dict[str, Any]:
        data = await self._request("GET", PATH_WIDGETS.format(vin=vin))
        return data if isinstance(data, dict) else {}

    async def async_get_battery(self, vin: str) -> dict[str, Any]:
        data = await self._request("GET", PATH_BATTERY.format(vin=vin))
        return data if isinstance(data, dict) else {}

    async def async_find_car(self, vin: str) -> Any:
        return await self._request(
            "PUT", PATH_FIND_CAR.format(vin=vin), empty_body=True
        )

    async def async_loud_find_car(self, vin: str) -> Any:
        return await self._request(
            "POST",
            PATH_LOUD_FIND,
            json_body={"param": "4", "vin": vin},
        )
