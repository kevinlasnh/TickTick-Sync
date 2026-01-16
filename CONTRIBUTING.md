# CONTRIBUTING.md - Developer Guidelines / 开发指南

## 🤖 AI Agent Guidelines / AI Agent 操作规范
> **For AI Agents (Copilot, Claude, etc.)**: You MUST follow these rules when working on this project.
> 
> **面向 AI Agent（Copilot、Claude 等）**：在此项目中工作时必须遵循以下规则。

### Automatic Documentation Requirements / 自动文档记录要求

1. **CHANGELOG.md - Development Log / 开发日志**
   - **When to update**: After implementing any feature, fix, or architectural change.
   - **What to record**: 
     - Date and change title (bilingual)
     - Problem description and root cause analysis
     - Solution approach and implementation details
     - Files modified
   - **何时更新**：实现任何功能、修复或架构变更后。
   - **记录内容**：
     - 日期和变更标题（中英双语）
     - 问题描述和根因分析
     - 解决方案和实现细节
     - 修改的文件

2. **ISSUES.md - Bug & Feature Tracking / Bug 与功能追踪**
   - **When to update**:
     - New bug discovered → Add new issue entry
     - Bug fixed → Update status to "✅ Fixed" and add "Fix" description
     - New limitation found → Document in Limitations section
   - **Issue Format**:
     ```markdown
     ### [CATEGORY-XXX] Issue Title / 问题标题
     - **Severity**: Critical/High/Medium/Low
     - **Status**: Open / ✅ Fixed
     - **Description**: Bilingual description
     - **Fix**: (if fixed) What was done to resolve it
     ```
   - **何时更新**：
     - 发现新 Bug → 添加新问题条目
     - Bug 修复 → 更新状态为 "✅ Fixed" 并添加 "Fix" 描述
     - 发现新限制 → 记录到 Limitations 章节

3. **Workflow Checklist / 工作流检查清单**
   Before completing any task, verify:
   完成任务前，验证：
   - [ ] Code changes are tested/verified / 代码变更已测试验证
   - [ ] CHANGELOG.md updated if feature/architecture changed / 如有功能/架构变更，已更新 CHANGELOG.md
   - [ ] ISSUES.md updated if bug fixed or discovered / 如修复或发现 Bug，已更新 ISSUES.md
   - [ ] All documentation is bilingual (Chinese/English) / 所有文档均为中英双语

---

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
