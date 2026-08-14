"""Zeeho tapi.zeehoev.com 客户端。Token + VIN，并按 App 规则签 Cfmoto-X-Sign。"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import time
from typing import Any
from urllib.parse import parse_qsl, quote, urlparse

import aiohttp

from .const import (
    API_HOST,
    API_OK_CODE,
    APP_ID,
    APP_SECRET,
    APP_USER_AGENT,
    INTERFACE_VERSION,
    PATH_BATTERY,
    PATH_FIND_CAR,
    PATH_HOMEPAGE,
    PATH_LOUD_FIND,
    PATH_VEHICLE_LIST,
    PATH_WIDGETS,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)
_NONCE_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


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


def _normalize_query(path: str) -> str:
    query = urlparse(path).query
    if not query:
        return ""
    items = sorted(parse_qsl(query, keep_blank_values=True), key=lambda kv: kv[0])
    return "&".join(f"{k}={quote(v, safe='')}" for k, v in items)


def _sign_headers(path: str, body: str) -> dict[str, str]:
    """Cfmoto-X-Sign = md5(sha1(query + body + appId&nonce&timestamp + appSecret))."""
    timestamp = str(int(time.time() * 1000))
    nonce = timestamp + "".join(secrets.choice(_NONCE_ALPHABET) for _ in range(16))
    param = f"appId={APP_ID}&nonce={nonce}&timestamp={timestamp}"
    source = f"{_normalize_query(path)}{body}{param}{APP_SECRET}"
    signature = hashlib.md5(hashlib.sha1(source.encode("utf-8")).hexdigest().encode("utf-8")).hexdigest()
    return {
        "appId": APP_ID,
        "Cfmoto-X-Param": param,
        "timestamp": timestamp,
        "nonce": nonce,
        "Cfmoto-X-Sign": signature,
        "signature": signature,
        "Cfmoto-X-Sign-Type": "0",
        "interfaceversion": INTERFACE_VERSION,
        "Accept-Language": "zh-CN",
        "User-Agent": APP_USER_AGENT,
        "X-App-Info": APP_USER_AGENT,
    }


class ZeehoApi:
    """极核云端 API。"""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        self._session = session
        self.token = normalize_token(token)

    def _headers(self, path: str, body: str) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }
        headers.update(_sign_headers(path, body))
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        empty_body: bool = False,
    ) -> Any:
        url = f"{API_HOST}{path}"
        body = ""
        data: bytes | None = None
        if empty_body:
            data = b""
        elif json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False, separators=(",", ":"))
            data = body.encode("utf-8")

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        try:
            async with self._session.request(
                method,
                url,
                headers=self._headers(path, body),
                data=data,
                timeout=timeout,
            ) as resp:
                if resp.status in (401, 403):
                    raise ZeehoAuthError(
                        f"认证失败：token 可能已失效（HTTP {resp.status}）"
                    )
                try:
                    payload = await resp.json(content_type=None)
                except (ValueError, TypeError) as err:
                    if resp.status != 200:
                        raise ZeehoApiError(
                            f"API 请求失败：HTTP {resp.status}", status=resp.status
                        ) from err
                    raise ZeehoApiError(f"API 响应解析失败：{err}") from err
                if resp.status != 200:
                    code = payload.get("code") if isinstance(payload, dict) else None
                    message = payload.get("message") if isinstance(payload, dict) else None
                    raise ZeehoApiError(
                        f"API 请求失败：HTTP {resp.status} code={code} message={message}",
                        status=resp.status,
                        code=str(code) if code is not None else None,
                    )
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
