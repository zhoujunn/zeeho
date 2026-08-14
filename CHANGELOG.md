# 更新日志

## [2026.8.14.1] - 2026-08-14

### 修复

- **HTTP 430 permit error**：`vehicleHomePage` / `batteryInfo` 等接口会校验 `Cfmoto-X-Sign`。少签名是 `30124`，签名过期/算错是 `30123`。现按 App 规则每次请求现算 `md5(sha1(query+body+appId&nonce&timestamp+appSecret))`。

## [2026.8.14] - 2026-08-14

本版本为 [zhoujunn/zeeho](https://github.com/zhoujunn/zeeho) 的 fork 增强版。旧配置条目可直接替换升级，原 4 个 sensor + 1 个 device_tracker 的 `unique_id` 不变。

### 新增

- **云端寻车按钮**：短按寻车、高声寻车（只需 Token + VIN）
- **首页遥测**：充电中、在线、整车锁定、座垫锁、总里程、本月里程 / 时长 / 均速、蜂窝信号、联网服务到期
- **充电电参**：功率、电压、电流（来自 `batteryInfo`，失败不影响其它实体）
- **配置流**：粘贴 Token 后自动拉车辆列表；多车时选择；支持选项页和重新认证更新 Token
- **数据源**：`vehicleHomePage` 为主，`widgets` 只补地址

### 变更

- 原「车锁」显示名改为「电源模式」，取值 `上电` / `下电`（对应 IoT「车辆电源模式」）
- HTTP 会话改为使用 Home Assistant 共享 `aiohttp` 客户端，卸载时不再自建/自关 session
- 去掉对 `requests` 的依赖

### 不做

- 云端解锁 / 上锁、开坐垫 / 储物箱、每日签到按钮（抓包或算法不足）

## [2026.8.4] - 2026-08-04

### 修复与优化

- **错误处理**：API 返回 401/403 时日志明确提示「token 可能失效，请重新配置」；网络 / DNS 异常时提示检查服务器网络；API 业务错误（code ≠ 10000）也会记录并暴露具体原因
- **配置流程**：连通性测试区分「认证失败（token / VIN 错误）」与「无法连接（网络问题）」；同一 VIN 禁止重复添加；Token / VIN 自动去除首尾空格
- **传感器**：电量、续航改为数值类型（API 返回字符串），便于自动化与图表使用；补充 battery / distance 设备类别与图标；地址为空时显示「未知」而非 unknown
- **资源释放**：卸载集成时正确关闭 HTTP 会话，避免连接泄漏
- **文档**：新增 README.md（安装 / 配置 / 注意事项）与 CHANGELOG.md

### 兼容性

- 配置项不变：Token（不带 Bearer 前缀）+ VIN + 车辆名称
- 4 个 sensor + 1 个 device_tracker 结构保持不变
- 旧版本可直接替换升级，无需重新配置

## [2025.9.23] - 2025-09-23

- 初始版本：4 个传感器（电量 / 续航 / 车锁 / 地址）+ 设备追踪器（GCJ-02 → WGS-84 坐标转换）
