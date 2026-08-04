"""Zeeho（极核）传感器：电量、续航、车锁、地址。"""
import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfLength
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _device_info(coordinator, vin):
    # 所有 zeeho 实体归属同一设备
    return {
        "identifiers": {(DOMAIN, vin)},
        "name": "ZEEHO",
        "manufacturer": "ZEEHO",
        "model": coordinator.data.get("vehicleName", "Unknown"),
        "configuration_url": "https://github.com/zhoujunn/zeeho",
    }


def _to_number(value):
    """将 API 返回的字符串数值安全转换为 float，失败返回 None。"""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    vin = entry.data["vin"]
    vehicle_name = entry.data.get("vehicle_name", vin)

    entities = [
        ZeehoBatterySensor(coordinator, vin, vehicle_name),
        ZeehoRangeSensor(coordinator, vin, vehicle_name),
        ZeehoLockSensor(coordinator, vin, vehicle_name),
        ZeehoAddressSensor(coordinator, vin, vehicle_name),
    ]
    async_add_entities(entities, True)


class ZeehoBatterySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_battery"
        self._attr_name = f"Zeeho {vehicle_name} 电量"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._vin)

    @property
    def native_value(self):
        return _to_number(self.coordinator.data.get("bmssoc"))


class ZeehoRangeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_range"
        self._attr_name = f"Zeeho {vehicle_name} 续航"
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        self._attr_device_class = SensorDeviceClass.DISTANCE

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._vin)

    @property
    def native_value(self):
        return _to_number(self.coordinator.data.get("hmiRidableMile"))


class ZeehoLockSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_lock"
        self._attr_name = f"Zeeho {vehicle_name} 车锁"
        self._attr_icon = "mdi:lock"

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._vin)

    @property
    def native_value(self):
        state = self.coordinator.data.get("headLockState")
        if state == "1":
            return "已锁"
        if state == "0":
            return "未锁"
        return "未知"


class ZeehoAddressSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_address"
        self._attr_name = f"Zeeho {vehicle_name} 地址"
        self._attr_icon = "mdi:map-marker"

    @property
    def device_info(self):
        return _device_info(self.coordinator, self._vin)

    @property
    def native_value(self):
        return self.coordinator.data.get("address") or "未知"
