# CONTRIBUTING.md - Developer Guidelines / 开发指南

## 📝 Documentation & Knowledge Management / 文档与知识管理
> **Crucial Rule**: Any new development idea, architectural change, or significant feature implementation MUST be recorded in `CHANGELOG.md` immediately. All documentation MUST be bilingual (Chinese/English).
> 
> **重要规则**：任何新的开发思路、架构变更或重大功能实现必须立即记录在 `CHANGELOG.md` 中。所有文档必须采用中英双语撰写。

- **Log Context**: Explain the *why* and *how* of changes, not just the *what*.
- **Sync**: Keep `CHANGELOG.md` updated as the "source of truth" for the project's evolution.
- **记录背景**：解释变更的"原因"和"方式"，而不仅是"内容"。
- **同步**：保持 `CHANGELOG.md` 更新，作为项目演进的"单一事实来源"。

## 🛠 Project Overview / 项目概览
- **Type**: Python automation for TickTick notes synchronization.
- **Data Source**: TickTick Cloud API (International/China).
- **Local Cache**: Local SQLite (`%APPDATA%/Tick_Tick/TickTick.db`) used for **auth token extraction only**.
- **Sync Logic**: Bidirectional sync between Cloud API and local Markdown files.
- **类型**：TickTick 笔记同步的 Python 自动化工具。
- **数据源**：滴答清单云端 API（国际/中国区）。
- **本地缓存**：本地 SQLite (`%APPDATA%/Tick_Tick/TickTick.db`) 仅用于**提取认证令牌**。
- **同步逻辑**：云端 API 与本地 Markdown 文件之间的双向同步。

## 💻 Tech Stack / 技术栈
- **Languages**: Python 3.10+
- **Key Libraries**: `requests` (API), `watchdog` (File Monitor), `pystray` (System Tray), `sqlite3` (Auth Extraction).
- **OS**: Windows (relies on `APPDATA`).
- **语言**：Python 3.10+
- **核心库**：`requests` (API), `watchdog` (文件监控), `pystray` (系统托盘), `sqlite3` (认证提取).
- **操作系统**：Windows (依赖 `APPDATA`).

## ⚙️ Core Scripts / 核心脚本
- `daemon.py`: The heart of the system. Handles real-time API sync.
  - 系统核心。处理实时 API 同步。
- `tray_app.py`: GUI wrapper. Runs `daemon.py` in background thread.
  - GUI 包装器。在后台线程运行 `daemon.py`。
- `legacy/pull.py` & `legacy/push.py`: Deprecated DB-based sync scripts.
  - 已废弃的基于数据库的同步脚本。

## ⚠️ Critical Constraints / 关键限制
- **API Rate Limits**: Polling interval set to 10s to avoid banning.
  - **API 速率限制**：轮询间隔设为 10 秒以避免封禁。
- **Timezone**: Cloud uses UTC, Local uses user's timezone. Conversion is handled in `daemon.py`.
  - **时区**：云端使用 UTC，本地使用用户时区。转换逻辑在 `daemon.py` 中处理。
- **Encoding**: Ensure `utf-8` for all file I/O to handle Chinese characters correctly.
  - **编码**：确保所有文件 I/O 使用 `utf-8`，以正确处理中文字符。
