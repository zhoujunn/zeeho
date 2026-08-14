"""Zeeho 集成常量。"""

from datetime import timedelta

DOMAIN = "zeeho"
API_HOST = "https://tapi.zeehoev.com"
API_OK_CODE = "10000"

CONF_VIN = "vin"
CONF_TOKEN = "token"
CONF_VEHICLE_NAME = "vehicle_name"

PLATFORMS = ["sensor", "device_tracker", "binary_sensor", "button", "lock"]

SCAN_INTERVAL = timedelta(minutes=1)
REQUEST_TIMEOUT = 30

PATH_WIDGETS = "/v1.0/app/cfmotoserverapp/vehicle/widgets/{vin}"
PATH_HOMEPAGE = "/v1.0/app/cfmotoserverapp/vehicleHomePage/{vin}"
PATH_BATTERY = "/v1.0/app/cfmotoserverapp/batteryInfo/{vin}"
PATH_VEHICLE_LIST = "/v1.0/app/cfmotoserverapp/vehicle/list"
PATH_FIND_CAR = "/v1.0/app/cfmotoserverapp/vehicleInfo/control/{vin}"
PATH_LOUD_FIND = "/v1.0/app/cfmotoserverapp/vehicleInfo/controlV2"
PATH_UNLOCK = "/v1.0/app/cfmotoserverapp/vehicleSet/network/unlock"
PATH_TIRE = "/v1.0/app/cfmotoserverapp/app/vehicle/tire/monitoring"
PATH_PROPERTY_TWO = "/v1.0/app/cfmotoserverapp/vehicleSet/propertyTwo/one"
PATH_SIGNIN = "/v1.0/mine/cfmotoservermine/signin"
PATH_SIGNIN_COUNT = "/v1.0/mine/cfmotoservermine/signin/count"

# App 开坐垫：PUT propertyTwo，官方字段名就是 commond。
COMMOND_OPEN_CUSHION = "28"

# App 3.0.0 云端开关锁：AES-256-ECB / PKCS7，明文 {"lockFlag":int,"vinNo":vin}
# lockFlag 1=开锁，0=关锁。HTTP body 是 {"secret": Base64}，签名签明文。
UNLOCK_AES_KEY = b"9dbc2cbf2ec327699301b495010316ec"

TIRE_POS_FRONT = 1
TIRE_POS_REAR = 2

# App 客户端签名（Cfmoto-X-Sign-Type=0）。secret 写在官方 App / 公开脚本里。
APP_ID = "S7qPWPU1"
APP_SECRET = "c5e0da7f4da28df805694ec3dd1fc6792e9df99d"
APP_USER_AGENT = (
    "MOBILE|iOS|27.0|ZEEHO_APP|2.6.26|iPhone|iPhone 16 Pro|"
    "1206*2622|homeassistant|WiFi|iOS"
)
INTERFACE_VERSION = "2"

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
