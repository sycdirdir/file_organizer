# File Organizer Pro v1.3 — 更新记录

## 版本信息
- **Version:** v1.3
- **Date:** 2026-04-19
- **主要变更:** 完善路径架构，支持 PyInstaller --onefile 打包

## 路径架构变更 (v1.2 → v1.3)

| 类别 | v1.2 路径 | v1.3 路径 |
|------|----------|----------|
| **可执行文件所在目录** | `WORK_DIR = __file__` | `APP_DIR = sys.executable` (打包后) / `__file__` (开发时) |
| **磁盘扫描数据库** | `DB/disk_C_HOSTNAME.db` | `DB/disk_C_HOSTNAME.db` |
| **系统数据库** | `DB/scan_history_HOSTNAME.db` | `APP_DIR/scan_history_HOSTNAME.db` |
| **日志文件** | 仅 UI log_txt | UI log_txt + `log/file_organizer_YYYYMMDD.log` |

## 关键代码逻辑

### APP_DIR 智能判断
```python
def _get_app_dir():
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe → sys.executable 指向 .exe
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        # Running as .py script (开发模式)
        return os.path.dirname(os.path.abspath(__file__))
```

### 路径常量
```python
APP_DIR = _get_app_dir()           # 可执行文件所在目录
DB_DIR = os.path.join(APP_DIR, "DB")      # 磁盘扫描数据库目录
LOG_DIR = os.path.join(APP_DIR, "log")    # 日志目录
```

### 磁盘数据库 (per-disk)
- 位置: `APP_DIR/DB/disk_{DRIVE}_HOSTNAME.db`
- 用途: 存储各磁盘扫描的文件清单

### 系统数据库 (meta)
- 位置: `APP_DIR/scan_history_HOSTNAME.db` (直接放 exe 同目录)
- 用途: 记录扫描历史、元数据

### 日志文件
- 目录: `APP_DIR/log/`
- 命名: `file_organizer_YYYYMMDD.log`
- 格式: 每日一个日志文件，按日期滚动

## PyInstaller 打包 (--onefile)
```bash
python -m PyInstaller --onefile --windowed --name FileOrganizerPro file_organizer.py
```
输出: `dist/FileOrganizerPro.exe` (~38.8 MB)
