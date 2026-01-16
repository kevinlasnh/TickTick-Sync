# TickTick Real-time Sync / 滴答清单实时同步 🔄

A powerful tool to synchronize **TickTick notes** with local **Markdown files** in real-time. Edit your notes in VS Code, Obsidian, or any local editor, and see them instantly updated in TickTick (and vice versa).

一个可以将 **滴答清单笔记** 与本地 **Markdown 文件** 实时双向同步的强大工具。在 VS Code、Obsidian 或任何本地编辑器中编辑笔记，即可即时在滴答清单中看到更新（反之亦然）。

---

## ✨ Features / 功能

- **🔄 Bidirectional Real-time Sync / 双向实时同步**:
  - **Local to Cloud**: Edits in local `.md` files are pushed to TickTick instantly via direct API (no app restart needed!).
  - **Cloud to Local**: Updates on mobile/web are pulled to local files automatically (every 10s).
  - **本地到云端**: 本地 `.md` 文件的修改通过 API 直接推送到滴答清单（无需重启应用！）。
  - **云端到本地**: 手机/网页端的更新会自动拉取到本地文件（每 10 秒）。

- **🖥️ System Tray App / 系统托盘应用**:
  - Runs silently in the background.
  - Quick access to Start/Stop sync and open local folder.
  - 静默后台运行。
  - 快速开启/停止同步，打开本地文件夹。

- **📂 Smart Organization / 智能整理**:
  - Automatically organizes notes into folders based on `func_level` tags.
  - 自动根据 `func_level` 标签将笔记整理到不同文件夹中。

- **⚡ No External API Key Required / 无需外部 API Key**:
  - Auto-extracts authentication token from your local TickTick Desktop client.
  - 自动从本地滴答清单客户端提取认证令牌。

---

## 🚀 Getting Started / 快速开始

### Prerequisites / 前置条件
- Windows OS
- [TickTick Desktop for Windows](https://ticktick.com/about/download) installed & logged in
- Python 3.8+

### Installation / 安装
1. Clone this repository
   克隆此仓库
2. Install dependencies:
   安装依赖:
   ```powershell
   pip install -r requirements.txt
   ```
   *(requirements: watchdog, requests, pystray, Pillow, pywin32)*

### Usage / 使用
Run the system tray application:
运行系统托盘程序:

```powershell
python tray_app.py
```

- A **Cloud Icon** will appear in your system tray.
- Right-click for menu options.
- 系统托盘会出现一个**云朵图标**。
- 右键点击查看菜单选项。

---

## 🛠️ Architecture / 架构

Moved from legacy local SQLite sync to **Direct Cloud API Sync**:

1. **Push (Local → Cloud)**:
   - `watchdog` monitors file changes.
   - `daemon.py` pushes content directly to `api.dida365.com` (China) using extracted token.
   - **Result**: Instant update on all devices.

2. **Pull (Cloud → Local)**:
   - Daemon polls TickTick API every 10 seconds.
   - Compares timestamps (handles UTC/Local time conversion) and content.
   - Updates local file if cloud version is newer.

---

## 📂 Directory Structure / 目录结构

- `tray_app.py`: Main entry point (GUI). / 主程序入口 (GUI)。
- `daemon.py`: Core sync logic (API calls, file watching). / 核心同步逻辑。
- `dev_scripts/`: Debugging and analysis tools. / 调试与分析工具。
- `legacy/`: Old SQLite-based sync scripts. / 旧版 SQLite 同步脚本。
