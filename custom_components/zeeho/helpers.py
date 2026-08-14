"""实体共用辅助函数。"""

from __future__ import annotations

from typing import Any

from .const import DOMAIN, IOT_VEHICLE_LOCK, REDACT_KEYS


def device_info(coordinator, vin: str, vehicle_name: str) -> dict[str, Any]:
    data = coordinator.data or {}
    model = data.get("vehicleTypeName") or data.get("vehicleName") or "Unknown"
    return {
        "identifiers": {(DOMAIN, vin)},
        "name": vehicle_name or data.get("vehicleName") or "ZEEHO",
        "manufacturer": "ZEEHO",
        "model": model,
        "configuration_url": "https://github.com/FlyRenxing/zeeho",
    }


def to_number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def iot_property(data: dict[str, Any] | None, identify: str) -> dict[str, Any] | None:
    if not data:
        return None
    for item in data.get("iotProperties") or []:
        if isinstance(item, dict) and item.get("identify") == identify:
            return item
    return None


def vehicle_lock_value(data: dict[str, Any] | None) -> str | None:
    prop = iot_property(data, IOT_VEHICLE_LOCK)
    if not prop:
        return None
    value = prop.get("value")
    return None if value is None else str(value)


def vehicle_lock_attrs(data: dict[str, Any] | None) -> dict[str, Any]:
    prop = iot_property(data, IOT_VEHICLE_LOCK) or {}
    attrs: dict[str, Any] = {}
    if prop.get("name"):
        attrs["iot_name"] = prop["name"]
    if prop.get("identify"):
        attrs["iot_identify"] = prop["identify"]
    if prop.get("describe"):
        attrs["iot_describe"] = prop["describe"]
    return attrs


def safe_attrs(mapping: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if key not in REDACT_KEYS}
