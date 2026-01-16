# TickTick-Sync

在本地 VS Code 中编辑滴答清单笔记的工具。

## 功能

- **pull.py**: 从滴答清单导出笔记到本地 `.md` 文件
- **push.py**: 将本地编辑推回滴答清单（自动云同步）

## 使用方法

### 1. 导出笔记到本地

```powershell
# 先关闭滴答清单
python pull.py
```

笔记将按 `func_level_X` 标签分类导出到 `Note_temp/` 目录。

### 2. 在 VS Code 中编辑

直接打开 `Note_temp/` 目录，编辑任意 `.md` 文件。

> ⚠️ 不要修改文件开头的 `---` 元数据区域（包含 task_id）

### 3. 推送修改回滴答清单

```powershell
# 确保滴答清单已关闭
python push.py
# 输入 y 确认
```

### 4. 重新打开滴答清单

修改会自动同步到云端。

## 目录结构

```
TickTick-Sync/
├── pull.py           # 导出脚本
├── push.py           # 推送脚本
├── Note_temp/        # 本地笔记（按标签分类）
│   ├── func_level_1/
│   ├── func_level_2/
│   └── ...
└── backups/          # 推送前自动备份
```

## 注意事项

- 操作前必须**完全关闭**滴答清单（包括托盘图标）
- 只同步 `kind='NOTE'` 类型的笔记，不包括普通任务
