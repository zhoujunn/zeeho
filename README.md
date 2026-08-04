# Zeeho（极核）Home Assistant 集成

将极核（ZEEHO）电动车接入 Home Assistant，实时获取车辆电量、续航、车锁状态、地址与定位。

## 功能

- **4 个传感器（sensor）**：
  - 车辆电量（%）
  - 续航里程（km）
  - 车锁状态（已锁 / 未锁）
  - 车辆地址（部分情况下 API 返回空，属正常现象）
- **1 个设备追踪器（device_tracker）**：车辆实时定位（API 返回 GCJ-02 坐标系，集成已自动转换为 WGS-84）
- 数据每分钟自动刷新

## 安装

### 方法一：HACS（推荐）

1. HACS → 右上角菜单 → **自定义存储库**
2. 仓库地址填 `https://github.com/zhoujunn/zeeho`，类别选择 **Integration**
3. 添加后搜索 **Zeeho** 并下载
4. 重启 Home Assistant

### 方法二：手动安装

1. 下载 `zeeho-2026.8.4.zip` 并解压
2. 将 `zeeho` 文件夹复制到 Home Assistant 的 `custom_components/` 目录下
3. 重启 Home Assistant

## 配置

设置 → 设备与服务 → 添加集成 → 搜索 **Zeeho**。

| 配置项 | 说明 |
|---|---|
| 访问 Token | 极核 App 接口请求头 `Authorization` 的值（**不要**带 `Bearer` 前缀，集成会自动加上） |
| 车辆 VIN | 车架号，例如 `358122400020000` |
| 车辆名称 | 自定义名称（可选，留空则使用 API 返回的车辆名） |

> **Token 获取方式**：抓取极核 App 的 API 请求，取请求头 `Authorization` 中 `Bearer` 后面的值。
> 旧版抓包所需的 `Cfmoto-X-Sign` / `Cfmoto-X-Param` / `Appid` / `Nonce` / `Signature` 等签名头，在新版 API 中**不再需要**，只需 Token + VIN 即可。

API 域名：`https://tapi.zeehoev.com`

## v2026.8.4 更新说明

- 错误处理优化：token 失效（HTTP 401/403）时日志会明确提示「token 可能失效，请重新配置」；网络/DNS 异常也会明确提示
- 配置流程优化：连通性测试可区分「认证失败」与「无法连接」；同一 VIN 不允许重复添加；Token / VIN 自动去除首尾空格
- 电量、续航改为数值类型（API 原返回字符串），便于自动化与图表使用；补充设备类别与图标
- 修复资源释放：卸载集成时正确关闭 HTTP 会话
- 新增 README 与 CHANGELOG

## 注意事项

- Token 即极核账号的访问凭证，请勿公开分享（Token 保存在 HA 配置存储 `.storage` 中，不会写入日志）
- 若实体显示不可用，先查看日志：
  - `认证失败：token 可能已失效` → 重新抓取 Token，删除集成后重新添加
  - `网络错误：无法连接 Zeeho API` → 检查服务器网络 / DNS 是否能解析 `tapi.zeehoev.com`
- 车辆地址字段（address）部分情况下 API 返回空，此时地址传感器显示「未知」
- 轮询间隔固定为 1 分钟，避免对官方 API 造成压力

## 更新日志

见 [CHANGELOG.md](CHANGELOG.md)

## 参考项目

- [dscao/autoamap](https://github.com/dscao/autoamap)（高德车机集成，坐标转换参考）
