# Development Log / 开发日志

## 2026-01-16: Auto-Start Feature & UI Fixes / 开机自启动功能与 UI 修复

### ✨ New Feature: Start with Windows / 新功能：Windows 开机自启动

Added a toggle in the tray menu to enable/disable auto-start with Windows.
在托盘菜单中添加了启用/禁用 Windows 开机自启动的开关。

**Implementation / 实现方式**:
- Uses Windows Registry: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- Runs with `pythonw.exe` for silent execution (no console window)
- Dynamic menu item shows current state: `[ON]` / `[OFF]`
- 使用 Windows 注册表: `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`
- 使用 `pythonw.exe` 静默运行（无控制台窗口）
- 动态菜单项显示当前状态: `[ON]` / `[OFF]`

### 📦 Packaging / 打包

Added support for building standalone executable using PyInstaller.
添加了使用 PyInstaller 打包为独立可执行文件的支持。

**Features / 特性**:
- Single-file `.exe` (~20MB) with no Python installation required
- `--noconsole` mode for silent background execution
- Fixed `sys.stdout` handling for noconsole compatibility
- 单文件 `.exe`（约 20MB），无需安装 Python
- `--noconsole` 模式实现静默后台运行
- 修复了 noconsole 兼容性的 `sys.stdout` 处理

**Build Command / 打包命令**:
```powershell
pyinstaller --onefile --noconsole --name "TickTickSync" tray_app.py
```

### 🐛 Bug Fixes / Bug 修复
- **UI-001**: Fixed menu status not updating in real-time (use dynamic callbacks)
- **UI-002**: Replaced emoji with ASCII text for compatibility
- **UI-003**: Fixed pause action delay (replaced blocking sleep with polling loop)
- **UI-001**: 修复菜单状态不实时更新（使用动态回调）
- **UI-002**: 用 ASCII 文本替代 Emoji 以提高兼容性
- **UI-003**: 修复暂停操作延迟（用轮询循环替代阻塞 sleep）

---

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

### UI/UX Improvements / 体验优化
- **High-Res Icon**: New anti-aliased cloud icon generated programmatically.
- **Dynamic Menu**: Replaced confusing checkboxes with clear "Pause/Resume" actions and Status indicator.
- **高清图标**: 程序生成的抗锯齿云朵图标。
- **动态菜单**: 将令人困惑的复选框替换为清晰的"暂停/恢复"操作和状态指示器。

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
