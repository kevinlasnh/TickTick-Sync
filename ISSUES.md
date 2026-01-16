# Known Issues / 已知问题

This document tracks known bugs, limitations, and planned improvements.
本文档追踪已知 Bug、限制和计划中的改进。

## 🐛 Bugs

### [UI-001] System Tray Menu Status Incorrect / 系统托盘菜单状态不正确
- **Severity**: Low / 低
- **Status**: ✅ Fixed / 已修复
- **Description**: 
  When the application starts, the right-click menu may display "Status: Paused" even though synchronization is actually running in the background.
  程序启动后，右键菜单可能显示 "Status: Paused"（状态：已暂停），尽管后台实际上正在进行同步。
- **Steps to Reproduce**:
  1. Run `tray_app.py`.
  2. Wait for "Cloud sync loop started" log.
  3. Right-click the tray icon immediately.
- **Root Cause**: Potential variable scope issue or race condition in menu rendering callback.
- **Fix**: Refactored menu to use pystray's dynamic `MenuItem` callbacks. Status text now uses a callable that reads the `running` variable each time the menu is opened, and toggle buttons use `visible` callbacks for real-time state.

### [UI-002] Missing Colors/Emojis in Tray Menu / 托盘菜单缺少颜色/Emoji
- **Severity**: Low / 低
- **Status**: ✅ Fixed / 已修复
- **Description**:
  The status indicators (🔴/🟢) are not visible on some Windows systems.
  在某些 Windows 系统上，状态指示器（🔴/🟢）无法显示。
- **Environment**: Windows 10/11 (System font dependent).
- **Fix**: Replaced emoji indicators with ASCII text: `[ON]` for running, `[OFF]` for paused.

### [UI-003] Pause Action Has Delay / 暂停操作有延迟
- **Severity**: Low / 低
- **Status**: ✅ Fixed / 已修复
- **Description**:
  When clicking "Pause Sync", the CLI log "🛑 Cloud sync loop stopped" appears with several seconds delay.
  点击"暂停同步"时，CLI 日志 "🛑 Cloud sync loop stopped" 会延迟数秒才出现。
- **Root Cause**: `time.sleep(POLL_INTERVAL)` blocks for 10 seconds. The loop can only detect `running=False` after sleep completes.
  `time.sleep(POLL_INTERVAL)` 阻塞 10 秒。循环只能在 sleep 结束后才能检测到 `running=False`。
- **Fix**: Replaced single 10s sleep with 100 × 0.1s sleep loop, checking `running` flag each iteration. Now responds within 0.1s.
  将单次 10 秒 sleep 改为 100 次 × 0.1 秒循环，每次迭代检查 `running` 标志。现在 0.1 秒内响应。

---

## 🔧 Limitations / 限制

### [SYNC-001] UTC Timezone Delay / UTC 时区延迟
- **Description**: Cloud timestamps are in UTC. Local comparison requires accurate conversion.
- **Workaround**: Implemented automatic conversion in `daemon.py`.

---

## 💡 Feature Requests / 功能建议

- ~~**Auto-Start**: Add "Start with Windows" registry key integration.~~ ✅ Implemented
- **Log Viewer**: Add "View Logs" menu item to open log file.
