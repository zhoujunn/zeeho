
"""Constants for autoamap."""
DOMAIN = "zeeho"

REQUIRED_FILES = [
    "const.py",
    "manifest.json",
    "device_tracker.py",
    "config_flow.py",
    "translations/zh-Hans.json",
]
VERSION = "2023.8.31"
ISSUE_URL = "https://github.com/zhoujunn/zeeho/issues"

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
"""

from homeassistant.const import (
    ATTR_DEVICE_CLASS,
)

ATTR_ICON = "icon"
ATTR_LABEL = "label"
MANUFACTURER = "https://www.zeehoev.com"
NAME = "极核"


#CONF_USER_ID = "user_id"
CONF_Authorization = "Authorization"
CONF_Cfmoto_X_Sign = "Cfmoto_X_Sign"
CONF_Cfmoto_X_Param = "Cfmoto_X_Param"
CONF_Appid = "Appid"
CONF_Nonce = "Nonce"
CONF_Signature ="Signature"
#CONF_PARAMDATA = "paramdata"
CONF_XUHAO = "xuhao"
CONF_GPS_CONVER = "gps_conver"
CONF_ATTR_SHOW = "attr_show"
CONF_UPDATE_INTERVAL = "update_interval_seconds"
CONF_SENSORS = "sensors"
CONF_MAP_GCJ_LAT = "map_gcj_lat"
CONF_MAP_GCJ_LNG = "map_gcj_lng"
CONF_MAP_BD_LAT = "map_bd_lat"
CONF_MAP_BD_LNG = "map_bd_lng"
CONF_ADDRESSAPI = "addressapi"
CONF_ADDRESSAPI_KEY = "api_key"
CONF_PRIVATE_KEY = "private_key"

COORDINATOR = "coordinator"
UNDO_UPDATE_LISTENER = "undo_update_listener"

KEY_ADDRESS = "address"
KEY_QUERYTIME = "querytime"
KEY_PARKING_TIME = "parkingtime"
KEY_LASTSTOPTIME = "laststoptime"
KEY_BMSSOC = "bmssoc"
KEY_LOCATIONTIME="locationTime"
KEY_CHARGESTATE="chargeState"
KEY_HEADLOCKSTATE="headLockState"




ATTR_DEVICE_MODEL="device_model"
ATTR_VEHICLENAME="vehicleName"
ATTR_VEHICLEPICURL = "vehiclePicUrl"
ATTR_BMSSOC = "bmssoc"
ATTR_BLUETOOTHADDRESS = "bluetoothAddress"
ATTR_FULLCHARGETIME = "fullChargeTime"
ATTR_OTAVERSION = "otaVersion"
ATTR_SUPPORTNETWORKUNLOCK = "supportNetworkUnlock"
ATTR_TOTALRIDEMILE = "totalRideMile"
ATTR_SUPPORTUNLOCK = "supportUnlock"
ATTR_WHETHERCHARGESTATE = "whetherChargeState"
ATTR_LOCATIONTIME="locationTime"
ATTR_RIDESTATE="rideState"
ATTR_COURSE = "course"
ATTR_HEADLOCKSTATE="headLockState"
ATTR_CHARGESTATE="chargeState"


ATTR_LASTSTOPTIME = "laststoptime"
ATTR_LAST_UPDATE = "update_time"
ATTR_QUERYTIME = "querytime"
ATTR_PARKING_TIME = "parkingtime"
ATTR_ADDRESS = "address"

