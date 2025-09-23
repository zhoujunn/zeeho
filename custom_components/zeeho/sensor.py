import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, UnitOfLength
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

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

    @property
    def native_value(self):
        return self.coordinator.data.get("bmssoc", 0)

class ZeehoRangeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_range"
        self._attr_name = f"Zeeho {vehicle_name} 续航"
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    @property
    def native_value(self):
        return self.coordinator.data.get("hmiRidableMile", 0)

class ZeehoLockSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_lock"
        self._attr_name = f"Zeeho {vehicle_name} 车锁"

    @property
    def native_value(self):
        state = self.coordinator.data.get("headLockState")
        if state == "1":
            return "已锁"
        elif state == "0":
            return "未锁"
        return "未知"

class ZeehoAddressSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, vin, vehicle_name):
        super().__init__(coordinator)
        self._vin = vin
        self._vehicle_name = vehicle_name
        self._attr_unique_id = f"zeeho_{vehicle_name}_address"
        self._attr_name = f"Zeeho {vehicle_name} 地址"

    @property
    def native_value(self):
        return self.coordinator.data.get("address", "未知")
