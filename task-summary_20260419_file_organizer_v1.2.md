# FileOrganizer Pro v1.2 更新摘要

## 重复文件分析表头修复 (2026-04-19 06:15 GMT+8)

### 问题
1. 重复文件分析表头文字没有跟随多语言切换
2. 表头不支持排序

### 修复内容

**1. 添加 i18n 键**（中文/英文/法文）
```python
"t2_col_name": "文件名" / "Filename" / "Nom du fichier"
"t2_col_size": "单个大小(GB)" / "Each(GB)" / "Taille(GB)"
"t2_col_copies": "副本数" / "Copies" / "Copies"
"t2_col_wasted": "浪费空间(GB)" / "Wasted(GB)" / "Espace perdu(GB)"
"t2_col_path": "首个路径" / "First Path" / "Premier chemin"
```

**2. 修改 `_tab_dup` 方法**
- 表头使用 `T()` 函数获取翻译
- 添加可排序列的配置（大小、副本数、浪费空间）

**3. 添加 `_sort_dup_tree` 方法**
- 支持点击表头排序
- 默认降序排列，点击后切换为升序
- 表头显示排序方向箭头（▲ 升序 / ▼ 降序）
- 数值列优先使用数值排序

### 趋势分析功能说明

**功能原理**：从数据库的 `dir_entries` 表中查询文件的修改时间（`mtime`），按月统计文件入库趋势。

**可能为空的原因**：
1. 数据库中没有文件记录 - 需要重新扫描磁盘
2. 文件修改时间获取失败 - 某些文件可能无法读取修改时间
3. 查询条件过滤 - `mtime>'_'` 过滤掉了空值

**建议**：如果趋势分析为空，请重新扫描磁盘确保文件记录包含修改时间。

## 文件位置

```
file_organizer/
├── dist/FileOrganizerPro.exe              # 可执行文件
├── FileOrganizerPro_使用说明书_v1.2.docx  # 使用说明书
└── file_organizer.py                      # 源代码
```
