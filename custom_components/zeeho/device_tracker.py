"""Zeeho 设备追踪器。API 坐标为 GCJ-02，转换为 WGS-84。"""

from __future__ import annotations

import math

from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VEHICLE_NAME, CONF_VIN, DOMAIN
from .helpers import device_info

PI = math.pi
A = 6378245.0
EE = 0.00669342162296594323


def gcj02_to_wgs84(lng, lat):
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    return lng - dlng, lat - dlat


def _transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320.0 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    return not (72.004 <= lng <= 137.8347 and 0.8293 <= lat <= 55.8271)


def _wgs_coords(data: dict):
    loc = (data or {}).get("location") or {}
    if loc.get("latitude") is None or loc.get("longitude") is None:
        return None
    try:
        lng = float(loc["longitude"])
        lat = float(loc["latitude"])
    except (TypeError, ValueError):
        return None
    return gcj02_to_wgs84(lng, lat)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    vin = entry.data[CONF_VIN]
    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, vin)
    async_add_entities([ZeehoDeviceTracker(coordinator, vin, vehicle_name)])


class ZeehoDeviceTracker(CoordinatorEntity, TrackerEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_tracker"
        self._attr_name = f"Zeeho {vehicle_name}"

    @property
    def latitude(self):
        coords = _wgs_coords(self.coordinator.data)
        return None if coords is None else coords[1]

    @property
    def longitude(self):
        coords = _wgs_coords(self.coordinator.data)
        return None if coords is None else coords[0]

    @property
    def location_accuracy(self):
        return 50

    @property
    def icon(self):
        return "mdi:motorbike"

    @property
    def extra_state_attributes(self):
        loc = (self.coordinator.data or {}).get("location") or {}
        return {
            "altitude": loc.get("altitude"),
            "location_time": loc.get("locationTime"),
            "coordinate_system": loc.get("coordinateSystem"),
        }

    @property
    def device_info(self):
        return device_info(self.coordinator, self._vin, self._vehicle_name)
