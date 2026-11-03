"""Zeeho 传感器。"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPower,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_VEHICLE_NAME, CONF_VIN, DOMAIN
from .helpers import device_info, tire_extra, to_number, vehicle_lock_attrs, vehicle_lock_value


def _map_lock(value: Any) -> str:
    state = None if value is None else str(value)
    if state == "1":
        return "已锁"
    if state == "0":
        return "未锁"
    return "未知"


@dataclass(kw_only=True)
class ZeehoSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    extra_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None
    legacy_unique_suffix: str | None = None


SENSORS: tuple[ZeehoSensorDescription, ...] = (
    ZeehoSensorDescription(
        key="battery",
        name="电量",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: to_number(data.get("bmssoc")),
        legacy_unique_suffix="battery",
    ),
    ZeehoSensorDescription(
        key="range",
        name="续航",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: to_number(data.get("hmiRidableMile")),
        legacy_unique_suffix="range",
    ),
    ZeehoSensorDescription(
        key="lock",
        name="车锁",
        icon="mdi:lock",
        value_fn=lambda data: _map_lock(data.get("headLockState")),
        extra_fn=lambda data: {
            "raw": data.get("headLockState"),
            "iot_name": "车辆电源模式",
        },
        legacy_unique_suffix="lock",
    ),
    ZeehoSensorDescription(
        key="address",
        name="地址",
        icon="mdi:map-marker",
        value_fn=lambda data: data.get("address") or "未知",
        legacy_unique_suffix="address",
    ),
    ZeehoSensorDescription(
        key="vehicle_lock",
        name="整车锁定",
        icon="mdi:shield-lock-outline",
        entity_registry_enabled_default=False,
        value_fn=vehicle_lock_value,
        extra_fn=vehicle_lock_attrs,
    ),
    ZeehoSensorDescription(
        key="seat_lock",
        name="座垫锁",
        icon="mdi:seat",
        value_fn=lambda data: _map_lock(data.get("seatLockState")),
        extra_fn=lambda data: {"raw": data.get("seatLockState")},
    ),
    ZeehoSensorDescription(
        key="total_mileage",
        name="总里程",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=1,
        icon="mdi:counter",
        value_fn=lambda data: to_number(data.get("totalRideMile")),
    ),
    ZeehoSensorDescription(
        key="month_mileage",
        name="本月里程",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:map-marker-distance",
        value_fn=lambda data: to_number(data.get("rideMileageMonth")),
    ),
    ZeehoSensorDescription(
        key="month_ride_time",
        name="本月骑行时长",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:timer-outline",
        value_fn=lambda data: to_number(data.get("ridingTimeMonthUnitMinute")),
    ),
    ZeehoSensorDescription(
        key="month_avg_speed",
        name="本月均速",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:speedometer",
        value_fn=lambda data: to_number(data.get("avgVelocityMonth")),
    ),
    ZeehoSensorDescription(
        key="gsm",
        name="蜂窝信号",
        icon="mdi:signal",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: to_number(data.get("gsmRxLev")),
        extra_fn=lambda data: {
            key: data[key]
            for key in ("gsmRxLevValue", "gsmRxLevel")
            if key in data and data[key] is not None
        },
    ),
    ZeehoSensorDescription(
        key="service_end",
        name="联网服务到期",
        icon="mdi:calendar-end",
        value_fn=lambda data: data.get("rechargeEndDate"),
    ),
    ZeehoSensorDescription(
        key="charge_power",
        name="充电功率",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: to_number(data.get("power")),
    ),
    ZeehoSensorDescription(
        key="charge_voltage",
        name="充电电压",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: to_number(data.get("voltage")),
    ),
    ZeehoSensorDescription(
        key="charge_current",
        name="充电电流",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: to_number(data.get("current")),
    ),
    ZeehoSensorDescription(
        key="front_tire_pressure",
        name="前胎压",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: to_number(data.get("frontTirePressure")),
        extra_fn=lambda data: tire_extra(data, "front"),
    ),
    ZeehoSensorDescription(
        key="rear_tire_pressure",
        name="后胎压",
        native_unit_of_measurement=UnitOfPressure.BAR,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        icon="mdi:car-tire-alert",
        value_fn=lambda data: to_number(data.get("rearTirePressure")),
        extra_fn=lambda data: tire_extra(data, "rear"),
    ),
    ZeehoSensorDescription(
        key="front_tire_temp",
        name="前胎温",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: to_number(data.get("frontTireTemp")),
        extra_fn=lambda data: tire_extra(data, "front"),
    ),
    ZeehoSensorDescription(
        key="rear_tire_temp",
        name="后胎温",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: to_number(data.get("rearTireTemp")),
        extra_fn=lambda data: tire_extra(data, "rear"),
    ),
    ZeehoSensorDescription(
        key="signin_count",
        name="签到天数",
        icon="mdi:calendar-star",
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=0,
        value_fn=lambda data: to_number(data.get("signCount")),
        extra_fn=lambda data: {
            key: data[key]
            for key in ("signStatus", "signCount")
            if key in data and data[key] is not None
        },
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    vin = entry.data[CONF_VIN]
    vehicle_name = entry.data.get(CONF_VEHICLE_NAME, vin)
    async_add_entities(
        [
            ZeehoSensor(coordinator, vin, vehicle_name, description)
            for description in SENSORS
        ]
    )


class ZeehoSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = False

    def __init__(self, coordinator, vin: str, vehicle_name: str, description: ZeehoSensorDescription):
        super().__init__(coordinator)
        self.entity_description = description
        self._vin = vin
        self._vehicle_name = vehicle_name
        if description.legacy_unique_suffix:
            self._attr_unique_id = f"zeeho_{vehicle_name}_{description.legacy_unique_suffix}"
        else:
            self._attr_unique_id = f"zeeho_{vin}_{description.key}"
        self._attr_name = f"Zeeho {vehicle_name} {description.name}"

    @property
    def device_info(self):
        return device_info(self.coordinator, self._vin, self._vehicle_name)

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        return self.entity_description.value_fn(data)

    @property
    def extra_state_attributes(self):
        if not self.entity_description.extra_fn:
            return None
        return self.entity_description.extra_fn(self.coordinator.data or {})
