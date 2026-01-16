# Development Log / 开发日志

## 2026-01-16: Cloud API Discovery & Major Rewrite / 云端 API 发现与重大重写

### 🎉 Breakthrough: Direct Cloud API Sync / 突破：直接云端 API 同步

After discovering that modifying the local SQLite database doesn't trigger TickTick's cloud sync (the app uses memory cache), we found a way to **bypass the local client entirely**.
在发现修改本地 SQLite 数据库无法触发滴答清单的云同步（应用使用内存缓存）后，我们找到了**完全绕过本地客户端**的方法。

**Key Discovery / 关键发现**:
- TickTick stores auth token in `UserModel.token`
- China region uses `api.dida365.com` (international: `api.ticktick.com`)
- Batch update endpoint: `POST /api/v2/batch/task`
- 滴答清单在 `UserModel.token` 中存储认证令牌
- 中国区使用 `api.dida365.com`（国际版: `api.ticktick.com`）
- 批量更新端点: `POST /api/v2/batch/task`

### Architecture Change / 架构变更

```
BEFORE (Local DB):  Edit → SQLite → (blocked) → No sync
AFTER (Cloud API):  Edit → HTTP POST → Cloud → All devices sync instantly!

之前（本地数据库）：编辑 → SQLite → (阻断) → 无法同步
之后（云端 API）：编辑 → HTTP POST → 云端 → 所有设备即时同步！
```

### Files Rewritten / 重写的文件
- `daemon.py`: Now uses `CloudSyncDaemon` with API calls instead of SQLite writes
- `tray_app.py`: Updated to use new cloud-based daemon
- `daemon.py`: 现在使用 `CloudSyncDaemon`，通过 API 调用而非 SQLite 写入
- `tray_app.py`: 更新为使用新的云端守护进程

---

## 2026-01-16: Project Initialization & Core Sync Logic / 项目初始化与核心同步逻辑

### 1. Goal Definition / 目标定义
Enable local editing of TickTick notes in VS Code with real-time cloud sync.
实现在 VS Code 中本地编辑滴答清单笔记，并实时同步到云端。

### 2. Initial Approach (Deprecated) / 初始方案（已废弃）
- **pull.py**: Extract from local DB → `.md` files
- **push.py**: Write `.md` changes → local DB
- **Problem**: Local DB changes don't trigger cloud sync
- **pull.py**: 从本地数据库提取 → `.md` 文件
- **push.py**: 写入 `.md` 变更 → 本地数据库
- **问题**: 本地数据库变更不会触发云同步

### 3. Investigation / 调查
- Confirmed TickTick uses **WAL mode** SQLite (allows concurrent access)
- Discovered database writes succeed but **GUI doesn't refresh** (memory cache)
- Found **SyncStatusModel** table but inserting entries doesn't trigger sync
- 确认滴答清单使用 **WAL 模式** SQLite（允许并发访问）
- 发现数据库写入成功但 **GUI 不刷新**（内存缓存）
- 找到 **SyncStatusModel** 表但插入条目不会触发同步

### 4. Solution / 解决方案
Extracted auth token from `UserModel` and called TickTick's internal API directly.
从 `UserModel` 提取认证令牌，直接调用滴答清单的内部 API。

---

## Dependencies / 依赖
- `watchdog`: File system monitoring / 文件系统监控
- `requests`: HTTP client for API calls / API 调用的 HTTP 客户端
- `pystray`, `Pillow`: System tray icon / 系统托盘图标
