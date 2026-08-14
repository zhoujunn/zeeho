"""Zeeho 集成常量。"""

from datetime import timedelta

DOMAIN = "zeeho"
API_HOST = "https://tapi.zeehoev.com"
API_OK_CODE = "10000"

CONF_VIN = "vin"
CONF_TOKEN = "token"
CONF_VEHICLE_NAME = "vehicle_name"

PLATFORMS = ["sensor", "device_tracker", "binary_sensor", "button"]

SCAN_INTERVAL = timedelta(minutes=1)
REQUEST_TIMEOUT = 30

PATH_WIDGETS = "/v1.0/app/cfmotoserverapp/vehicle/widgets/{vin}"
PATH_HOMEPAGE = "/v1.0/app/cfmotoserverapp/vehicleHomePage/{vin}"
PATH_BATTERY = "/v1.0/app/cfmotoserverapp/batteryInfo/{vin}"
PATH_VEHICLE_LIST = "/v1.0/app/cfmotoserverapp/vehicle/list"
PATH_FIND_CAR = "/v1.0/app/cfmotoserverapp/vehicleInfo/control/{vin}"
PATH_LOUD_FIND = "/v1.0/app/cfmotoserverapp/vehicleInfo/controlV2"

# 不要写入实体属性的敏感字段
REDACT_KEYS = {
    "encryptInfo",
    "key",
    "iv",
    "encryptValue",
    "wifiAddress",
    "bluetoothAddress",
    "hmiBluetoothAddress",
}

IOT_VEHICLE_LOCK = "VehicleLock_S"
