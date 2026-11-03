# Zeeho（极核）Home Assistant 集成

[zhoujunn/zeeho](https://github.com/zhoujunn/zeeho) 的 fork。在原有电量 / 续航 / 地址 / 定位之外，按极核 App（tapi.zeehoev.com）核实过的接口补了首页遥测、云端寻车、云端车锁、胎压、开坐垫和每日签到。

仍只需 **Token + VIN**。请求签名和云端开关锁的 AES 都由集成按 App 规则现算。

## 功能

### 原有（unique_id 保持不变，可直接升级）

- 电量（%）
- 续航（km）
- 地址（来自 `widgets`；没有则显示「未知」）
- 设备追踪器（GCJ-02 → WGS-84）

原「车锁」实体仍在，显示 **已锁 / 未锁**（`headLockState`：`1` 已锁，`0` 未锁）。不要把它理解成「上下电」，也不要把它和后台那条「整车锁定」混成一把锁。

### 新增

- **传感器**：座垫锁、总里程、本月里程、本月骑行时长、本月均速、蜂窝信号、联网服务到期、充电功率 / 电压 / 电流、前/后胎压（bar）、前/后胎温、签到天数。整车锁定（`VehicleLock_S` 原始值）默认关闭，需要时再手动打开
- **二进制传感器**：充电中、在线、今日已签到
- **按钮**：短按寻车、高声寻车、开坐垫、每日签到
- **锁**：云端车锁（开锁 / 关锁，会真的操作车辆）

数据每分钟刷新一次：首页 `vehicleHomePage` + `widgets`（只为地址）+ `batteryInfo`（充电电参，失败忽略）+ `app/vehicle/tire/monitoring`（胎压，失败忽略）+ `signin/count`（签到，失败忽略）。

## 安装

### 方法一：HACS（推荐）

1. HACS → 右上角菜单 → **自定义存储库**
2. 仓库地址填 `https://github.com/FlyRenxing/zeeho`，类别选择 **Integration**
3. 若之前添加过 `zhoujunn/zeeho`，改成上述地址后重新下载
4. 搜索 **Zeeho** 并下载，重启 Home Assistant

### 方法二：手动安装

1. 下载本仓库，将 `custom_components/zeeho` 复制到 Home Assistant 的 `custom_components/` 目录
2. 重启 Home Assistant

## 配置

设置 → 设备与服务 → 添加集成 → 搜索 **Zeeho**，粘贴 Token。集成会调用车辆列表，多车时再选一辆。

已经添加过的车辆：**配置 → 选项** 里只更新 Token，不必删除集成。Token 失效时也会弹出重新认证。

| 配置项 | 说明 |
|---|---|
| 访问 Token | 极核 App 请求头 `Authorization` 的值（**不要**带 `Bearer` 前缀；带着也会自动去掉） |
| 车辆 VIN | 通常由车辆列表自动填入 |

> **Token 获取**：抓极核 App 的 API 请求，取 `Authorization` 里 `Bearer` 后面的值。

API 域名：`https://tapi.zeehoev.com`

首页、电池信息等接口除 Token 外还要 App 签名头（`appId` / `nonce` / `timestamp` / `Cfmoto-X-Sign`）。集成会按极核 App 的 type-0 算法现算，无需再从抓包里抄签名。

## 云端操作

都只要 Token + VIN。寻车、开坐垫、签到是明文；只有云端车锁要算 AES `secret`。

### 寻车

- **短按寻车**：`PUT /v1.0/app/cfmotoserverapp/vehicleInfo/control/{vin}`，空 body
- **高声寻车**：`POST /v1.0/app/cfmotoserverapp/vehicleInfo/controlV2`，`{"param":"4","vin":"..."}`

### 云端车锁

- 实体：`lock.zeeho_*_yun_duan_che_suo`（显示名「云端车锁」）
- 开锁 `lock.unlock` / 关锁 `lock.lock`，对应 App `POST /vehicleSet/network/unlock`
- 明文 `{"lockFlag":1|0,"vinNo":...}` 用 AES-256-ECB 加密后放进 `secret`；签名签明文，不是签密文
- `lockFlag`：`1` 开锁，`0` 关锁。状态跟首页 `headLockState`（`1` 已锁，`0` 未锁）
- **会真的操作车辆**，和官方 App 同一条云端指令

不要把「整车锁定」当成可以下发的锁，也不要用它判断 App 有没有解开。云端开关锁后这个值可以一直是 `0`。需要看状态时以「车锁」传感器或「云端车锁」为准。

### 开坐垫

- 实体：`button.zeeho_*_kai_zuo_dian`（显示名「开坐垫」）
- `PUT /vehicleSet/propertyTwo/one`，body `{commond:"28", commondParam:"1", vcu:VIN, version:"v2"}`
- 首页 `openCushionFlag=false` 时按钮不可用
- **会真的弹起坐垫**，和官方 App 同一条 4G 指令

### 每日签到

- 按钮 `每日签到`：`POST /mine/cfmotoservermine/signin`，空 body
- 传感器 `签到天数`、二进制传感器 `今日已签到`：来自 `GET /signin/count`（`signStatus` 1=已签）
- 今天已经签过时按钮不可用

## 明确还没有

这些不是疏忽，是现有抓包不够或只在蓝牙里：

- **开储物箱 / VCU 锁**：部分车型首页 `openStorageBoxFlag=false`，蓝牙 `serviceCode` 里才有 `OPEN_STORAGE_BOX` / `LOCK_VCU`。没有对应的 4G `commond`，猜一个会误操作别的属性

## 注意事项

- Token 是账号凭证，不要公开。保存在 HA `.storage`，不会写入日志或本仓库
- 实体不可用时：
  - 日志出现「token 可能已失效」→ 用选项/重新认证更新 Token
  - 「无法连接 Zeeho API」→ 检查 HA 主机能否访问 `tapi.zeehoev.com`
- 首页没有 `address` 字段，地址仍走 `widgets`；widgets 失败时地址显示「未知」，其它传感器照常
- `encryptInfo`、车机 Wi-Fi 密码、蓝牙 MAC 不会出现在实体属性里
- 轮询间隔固定 1 分钟

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)

## 参考

- 上游：[zhoujunn/zeeho](https://github.com/zhoujunn/zeeho)
- 坐标转换参考：[dscao/autoamap](https://github.com/dscao/autoamap)
