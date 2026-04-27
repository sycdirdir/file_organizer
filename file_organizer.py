# -*- coding: utf-8 -*-
"""File Organizer Pro v2.5 - i18n: 中文 / EN / FR
Updated: Tab 8 now tracks folder changes (new/deleted folders) in addition to files
"""
import os, sys, sqlite3, threading, time, math, socket, hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei UI', 'SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

VER = "2.5"

def _get_app_dir():
    """Return the directory where the executable or script resides.
    PyInstaller --onefile: sys.executable points to the .exe
    PyInstaller --onedir: sys.executable or __file__ both work
    Dev mode (python script): __file__ is correct
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))

APP_DIR = _get_app_dir()
DB_DIR  = os.path.join(APP_DIR, "DB")
LOG_DIR = os.path.join(APP_DIR, "log")

# ======================================================== Machine name ========================================================
def get_machine_name():
    try:
        return socket.gethostname().split('.')[0].upper()
    except Exception:
        try:
            return os.environ.get('COMPUTERNAME', 'UNKNOWN').upper()
        except Exception:
            return 'UNKNOWN'

MACHINE_NAME = get_machine_name()

# ======================================================== Path helpers ========================================================
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def disk_snapshot_path(drive_letter, timestamp):
    """Return path for a dated snapshot .db file.
    E.g. DB/20260420T063000_C_DESKTOP-CJJJF0S.db
    Format: {timestamp}_{drive}_{machinename}.db
    drive_letter: single letter like 'C'
    timestamp:    format string like '20260101T103000'
    """
    ensure_dir(DB_DIR)
    return os.path.join(
        DB_DIR,
        "{}_{}_{}.db".format(timestamp, drive_letter.upper(), MACHINE_NAME)
    )

def meta_db_path():
    """System meta database (stored alongside the executable)."""
    return os.path.join(APP_DIR, "scan_history_{}.db".format(MACHINE_NAME))

def init_log_dir():
    return ensure_dir(LOG_DIR)

META_DB = meta_db_path()

# ======================================================== Hash helper ========================================================
HASH_SAMPLE_BYTES = 64 * 1024   # 64 KB sample from front+back for large files
HASH_FULL_THRESHOLD = 50 * 1024 * 1024  # 50 MB: fully hash files below this size


def quick_hash(filepath):
    """Compute a fast content hash (MD5) for a file.
    - Files < 50 MB: full file hash
    - Files 鈮?50 MB: head+tail 64 KB sample hash (fast, good for uniqueness)
    Returns hex digest or None on error.
    """
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return "empty"
        if size < HASH_FULL_THRESHOLD:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        else:
            with open(filepath, 'rb') as f:
                front = f.read(HASH_SAMPLE_BYTES)
                f.seek(max(0, size - HASH_SAMPLE_BYTES))
                back = f.read(HASH_SAMPLE_BYTES)
            return hashlib.md5(front + back).hexdigest()
    except Exception:
        return None

# ======================================================== i18n system ========================================================
_LANG = {}
_LANG["zh"] = {
    "app_title": "File Organizer Pro",
    "app_subtitle": "磁盘 / 文件夹整理工具",
    "not_scanned": "尚未扫描",
    "status_ready": "就绪",
    "nav_0": "  [0] 扫描", "nav_1": "  [1] 总览",
    "nav_2": "  [2] 重复文件", "nav_3": "  [3] 趋势",
    "nav_4": "  [4] 分类", "nav_5": "  [5] 搜索",
    "nav_6": "  [6] 清理", "nav_7": "  [7] 历史", "nav_8": "  [8] 对比",
    "lang_label": "语言",
    "history_label": "历史",
    "history_combo_empty": "请扫描磁盘或目录",
    "t0_title": "1. 选择文件夹或磁盘",
    "t0_browse": "浏览...", "t0_load_db": "加载 DB",
    "t0_start": ">> 开始扫描", "t0_stop": "停止",
    "t0_log": "扫描日志", "t0_hash": "计算文件哈希(慢)",
    "t0_err_path": "路径不存在：",
    "t0_done_title": "扫描完成",
    "t0_done_msg": "完成！\n{:,} 个文件\n{:,} 个目录\n{:.1f} GB",
    "t1_title": "磁盘总览",
    "t1_files": "总文件数", "t1_dirs": "总目录数",
    "t1_size": "总大小", "t1_db": "数据库",
    "t1_by_ext": "按扩展名统计", "t1_by_month": "月度趋势",
    "t1_col_ext": "扩展名", "t1_col_files": "文件数", "t1_col_size": "大小(GB)", "t1_col_bar": "占比",
    "t1_col_month": "月份",
    "t2_title": "重复文件分析",
    "t2_min_size": "最小文件(MB)：",
    "t2_find": "查找重复",
    "t2_del_btn": "预览并删除全部重复文件",
    "t2_prev_title": "删除预览",
    "t2_prev_warn": "警告：将删除重复文件（保留一份）",
    "t2_keep": "[保留]", "t2_del": "[删除]",
    "t2_confirm": "确认删除？此操作无法撤销！",
    "t2_confirm_btn": "确认删除", "t2_cancel": "取消",
    "t2_done": "已删除：{:,} 个文件\n失败：{:,}\n回收空间：{:.1f} GB",
    "t2_col_name": "文件名",
    "t2_col_size": "单个大小(GB)",
    "t2_col_copies": "副本数",
    "t2_col_wasted": "耗费空间(GB)",
    "t2_col_path": "首个路径",
    "t3_title": "月度趋势",
    "t4_title": "分类统计",
    "t4_top_dirs": "按大小排列的顶级目录",
    "t4_ext_dist": "文件类型分布",
    "t4_pie_count": "文件数量占比 (Top 10)",
    "t4_pie_size": "存储空间占比 (Top 10)",
    "t5_title": "文件搜索",
    "t5_keyword": "关键字：", "t5_search_btn": "搜索",
    "t5_tip": "提示：按文件名、扩展名、标题搜索",
    "t5_enter_kw": "请输入关键字",
    "t6_title": "清理工具", "t6_small": "小文件清理",
    "t6_small_thresh": "清理小于 (MB)：",
    "t6_small_scan": "扫描小文件",
    "t6_small_del": "删除所列全部小文件",
    "t6_small_empty": "请先扫描小文件",
    "t6_del_confirm": "确认删除 {:,} 个文件？无法撤销！",
    "t6_del_done": "已删除：{:,} 个文件\n失败：{:,}",
    "dlg_tip": "提示", "dlg_err": "错误",
    "dlg_scan_first": "请先扫描文件夹（[0] 扫描）",
    "dlg_find_first": "请先点击「查找重复」",
    "dlg_loaded": "已加载：",
    "t7_title": "扫描历史",
    "t7_disk_sum": "已扫描磁盘",
    "t7_history": "扫描记录",
    "t7_load": "加载", "t7_del": "删除",
    "t7_del_confirm": "确认删除磁盘 {drive} 的数据库？\n{path}\n无法撤销！",
    "t7_del_done": "已删除：{path}",
    "t7_no_disk": "当前未加载任何磁盘数据库",
    # Tab 8 历史对比
    "t8_title": "扫描历史对比",
    "t8_desc": "选择两次扫描记录进行对比，查看文件变化",
    "t8_drive": "磁盘：",
    "t8_scan_a": "扫描 A（较早）",
    "t8_scan_b": "扫描 B（较晚）",
    "t8_compare_btn": "执行对比",
    "t8_result": "对比结果",
    "t8_added": "新增文件",
    "t8_deleted": "删除文件",
    "t8_modified": "修改文件",
    "t8_same": "无变化",
    "t8_added_size": "新增大小",
    "t8_deleted_size": "删除大小",
    "t8_no_change": "两次扫描完全相同",
    "t8_need_two": "请先选择一个磁盘，然后选择两次不同的扫描记录进行对比",
    "t8_load_a": "加载A", "t8_load_b": "加载B",
    "t8_col_file": "文件名", "t8_col_path": "文件路径",
    "t8_col_size": "大小(MB)", "t8_col_change": "变化",
    "t8_changed": "变化",
    "t8_same_size": "相同",
    "t8_new": "新增",
    "t8_removed": "已删除",
    "t8_no_sel": "未选择",
    "t8_ready": "可以对比",
    "t8_pick": "请左右各选一条记录",
    "t8_same_db": "左右选中了相同的数据文件，请重新选择。",
    "t8_new_dir": "新增文件夹",
    "t8_del_dir": "删除文件夹",

    # Tab 3 趋势表头
    "t3_col_month": "月份", "t3_col_files": "文件数", "t3_col_size": "大小(GB)", "t3_col_bar": "趋势图",
    # Tab 4 分类表头
    "t4_col_dir": "目录路径", "t4_col_ext2": "扩展名",
    "t4_col_files": "文件数", "t4_col_size": "大小(GB)",
    # Tab 5 搜索表头
    "t5_col_name": "文件名", "t5_col_path": "完整路径", "t5_col_size": "大小(GB)",
    # Tab 6 清理表头
    "t6_col_name": "文件名", "t6_col_path": "完整路径", "t6_col_size": "大小(MB)",
    # Tab 7 历史表头
    "t7_col_drive": "磁盘", "t7_col_snapshot": "快照路径", "t7_col_last": "最近扫描",
    "t7_col_files": "文件数", "t7_col_dirs": "目录数", "t7_col_size2": "大小(GB)",
    "t7_col_status": "状态", "t7_col_no": "#", "t7_col_root": "根路径", "t7_col_time": "扫描时间",
}
_LANG["en"] = {
    "app_title": "File Organizer Pro",
    "app_subtitle": "Disk / Folder Organizer",
    "not_scanned": "Not scanned",
    "status_ready": "Ready",
    "nav_0": "  [0] Scan", "nav_1": "  [1] Overview",
    "nav_2": "  [2] Duplicates", "nav_3": "  [3] Trends",
    "nav_4": "  [4] Categories", "nav_5": "  [5] Search",
    "nav_6": "  [6] Cleanup", "nav_7": "  [7] History", "nav_8": "  [8] Compare",
    "lang_label": "Lang",
    "history_label": "History",
    "history_combo_empty": "Please scan a disk or folder",
    "t0_title": "1. Select Folder or Drive",
    "t0_browse": "Browse...", "t0_load_db": "Load DB",
    "t0_start": ">> START SCAN", "t0_stop": "STOP",
    "t0_log": "Scan Log", "t0_hash": "Compute file hash (slow)",
    "t0_err_path": "Path not found: ",
    "t0_done_title": "Scan Complete",
    "t0_done_msg": "Done!\n{:,} files\n{:,} dirs\n{:.1f} GB",
    "t1_title": "Disk Overview",
    "t1_files": "Total Files", "t1_dirs": "Total Dirs",
    "t1_size": "Total Size", "t1_db": "Database",
    "t1_by_ext": "File Types by Size", "t1_by_month": "Monthly Trend",
    "t1_col_ext": "Extension", "t1_col_files": "Files", "t1_col_size": "Size(GB)", "t1_col_bar": "Bar",
    "t1_col_month": "Month",
    "t2_title": "Duplicate File Analysis",
    "t2_min_size": "Min size (MB):",
    "t2_find": "Find Duplicates",
    "t2_del_btn": "Preview and Delete All Duplicates",
    "t2_prev_title": "Delete Preview",
    "t2_prev_warn": "WARNING: Will delete duplicates (keeping first copy)",
    "t2_keep": "[KEEP]", "t2_del": "[DEL] ",
    "t2_confirm": "Confirm deletion? This cannot be undone!",
    "t2_confirm_btn": "CONFIRM DELETE", "t2_cancel": "Cancel",
    "t2_done": "Deleted: {:,} files\nFailed: {:,}\nRecovered: {:.1f} GB",
    "t2_col_name": "Filename",
    "t2_col_size": "Each(GB)",
    "t2_col_copies": "Copies",
    "t2_col_wasted": "Wasted(GB)",
    "t2_col_path": "First Path",
    "t3_title": "Monthly Trend",
    "t4_title": "Category Statistics",
    "t4_top_dirs": "Top Directories by Size",
    "t4_ext_dist": "File Type Distribution",
    "t4_pie_count": "File Count Distribution (Top 10)",
    "t4_pie_size": "Storage Space Distribution (Top 10)",
    "t5_title": "File Search",
    "t5_keyword": "Keyword: ", "t5_search_btn": "Search",
    "t5_tip": "Tip: Search by actor name, video code, or title",
    "t5_enter_kw": "Enter a keyword",
    "t6_title": "Cleanup Tools", "t6_small": "Small File Cleanup",
    "t6_small_thresh": "Clean files smaller than (MB):",
    "t6_small_scan": "Scan Small Files",
    "t6_small_del": "Delete All Listed Small Files",
    "t6_small_empty": "Scan small files first",
    "t6_del_confirm": "Delete {:,} files? Cannot undo!",
    "t6_del_done": "Deleted: {:,} files\nFailed: {:,}",
    "dlg_tip": "Tip", "dlg_err": "Error",
    "dlg_scan_first": "Scan a folder first (tab [0] Scan)",
    "dlg_find_first": "Click 'Find Duplicates' first",
    "dlg_loaded": "Loaded: ",
    "t7_title": "Scan History",
    "t7_disk_sum": "Scanned Disks",
    "t7_history": "Scan Records",
    "t7_load": "Load", "t7_del": "Delete",
    "t7_del_confirm": "Delete disk {drive} database?\n{path}\nCannot undo!",
    "t7_del_done": "Deleted: {path}",
    "t7_no_disk": "No disk database loaded",
    # Tab 8 History Compare
    "t8_title": "Scan History Compare",
    "t8_desc": "Compare two scan records to see file changes",
    "t8_drive": "Drive: ",
    "t8_scan_a": "Scan A (earlier)",
    "t8_scan_b": "Scan B (later)",
    "t8_compare_btn": "Compare",
    "t8_result": "Comparison Result",
    "t8_added": "Added Files",
    "t8_deleted": "Deleted Files",
    "t8_modified": "Modified Files",
    "t8_same": "Unchanged",
    "t8_added_size": "Added Size",
    "t8_deleted_size": "Deleted Size",
    "t8_no_change": "The two scans are identical",
    "t8_need_two": "Select a drive, then choose two different scan records to compare",
    "t8_load_a": "Load A", "t8_load_b": "Load B",
    "t8_col_file": "Filename", "t8_col_path": "File Path",
    "t8_col_size": "Size(MB)", "t8_col_change": "Change",
    "t8_changed": "Changed",
    "t8_same_size": "Same",
    "t8_new": "New",
    "t8_removed": "Removed",
    "t8_no_sel": "Not selected",
    "t8_ready": "Ready to compare",
    "t8_pick": "Pick one on each side",
    "t8_same_db": "Same data file selected on both sides. Please pick different snapshots.",
    "t8_new_dir": "New Folder",
    "t8_del_dir": "Deleted Folder",

    # Tab 3 Trends columns
    "t3_col_month": "Month", "t3_col_files": "Files", "t3_col_size": "Size(GB)", "t3_col_bar": "Bar Chart",
    # Tab 4 Categories columns
    "t4_col_dir": "Directory Path", "t4_col_ext2": "Extension",
    "t4_col_files": "Files", "t4_col_size": "Size(GB)",
    # Tab 5 Search columns
    "t5_col_name": "Filename", "t5_col_path": "Full Path", "t5_col_size": "Size(GB)",
    # Tab 6 Cleanup columns
    "t6_col_name": "Filename", "t6_col_path": "Full Path", "t6_col_size": "Size(MB)",
    # Tab 7 History columns
    "t7_col_drive": "Drive", "t7_col_snapshot": "Snapshot Path", "t7_col_last": "Last Scan",
    "t7_col_files": "Files", "t7_col_dirs": "Dirs", "t7_col_size2": "Size(GB)",
    "t7_col_status": "Status", "t7_col_no": "#", "t7_col_root": "Root Path", "t7_col_time": "Scan Time",
}
_LANG["fr"] = {
    "app_title": "File Organizer Pro",
    "app_subtitle": "Organisateur de Disque / Fichiers",
    "not_scanned": "Non analyse",
    "status_ready": "Pret",
    "nav_0": "  [0] Analyser", "nav_1": "  [1] Apercu",
    "nav_2": "  [2] Doublons", "nav_3": "  [3] Tendances",
    "nav_4": "  [4] Categories", "nav_5": "  [5] Recherche",
    "nav_6": "  [6] Nettoyage", "nav_7": "  [7] Historique", "nav_8": "  [8] Comparer",
    "lang_label": "Langue",
    "history_label": "Historique",
    "history_combo_empty": "Veuillez scanner un disque",
    "t0_title": "1. Selectionner un dossier ou lecteur",
    "t0_browse": "Parcourir...", "t0_load_db": "Charger DB",
    "t0_start": ">> ANALYSER", "t0_stop": "ARRET",
    "t0_log": "Journal d'analyse", "t0_hash": "Calculer hachage (lent)",
    "t0_err_path": "Chemin introuvable : ",
    "t0_done_title": "Analyse terminee",
    "t0_done_msg": "Termine !\n{:,} fichiers\n{:,} dossiers\n{:.1f} Go",
    "t1_title": "Apercu du disque",
    "t1_files": "Fichiers totaux", "t1_dirs": "Dossiers totaux",
    "t1_size": "Taille totale", "t1_db": "Base de donnees",
    "t1_by_ext": "Types de fichiers par taille",
    "t1_by_month": "Tendance mensuelle",
    "t1_col_ext": "Extension", "t1_col_files": "Fichiers", "t1_col_size": "Taille(Go)", "t1_col_bar": "Barre",
    "t1_col_month": "Mois",
    "t2_title": "Analyse des fichiers en double",
    "t2_min_size": "Taille min (Mo) :",
    "t2_find": "Trouver les doublons",
    "t2_del_btn": "Apercu et supprimer tous les doublons",
    "t2_prev_title": "Apercu de la suppression",
    "t2_prev_warn": "ATTENTION : Suppression des doublons (premiere copie conservee)",
    "t2_keep": "[GARDER]", "t2_del": "[SUPPR] ",
    "t2_confirm": "Confirmer la suppression ? Irreversible !",
    "t2_confirm_btn": "CONFIRMER", "t2_cancel": "Annuler",
    "t2_done": "Supprimes : {:,}\nEchecs : {:,}\nEspace recu : {:.1f} Go",
    "t3_title": "Tendance mensuelle",
    "t4_title": "Statistiques par categorie",
    "t4_top_dirs": "Principaux dossiers par taille",
    "t4_ext_dist": "Repartition par type de fichier",
    "t4_pie_count": "Repartition par nombre (Top 10)",
    "t4_pie_size": "Repartition par espace (Top 10)",
    "t5_title": "Recherche de fichiers",
    "t5_keyword": "Mot-cle : ", "t5_search_btn": "Rechercher",
    "t5_tip": "Astuce : rechercher par nom d'acteur, code video, titre",
    "t5_enter_kw": "Entrez un mot-cle",
    "t6_title": "Outils de nettoyage",
    "t6_small": "Nettoyage des petits fichiers",
    "t6_small_thresh": "Nettoyer les fichiers de moins de (Mo) :",
    "t6_small_scan": "Scanner les petits fichiers",
    "t6_small_del": "Supprimer tous les fichiers listes",
    "t6_small_empty": "Effectuez d'abord un scan",
    "t6_del_confirm": "Supprimer {:,} fichiers ? Irreversible !",
    "t6_del_done": "Supprimes : {:,}\nEchecs : {:,}",
    "dlg_tip": "Astuce", "dlg_err": "Erreur",
    "dlg_scan_first": "Analyser un dossier d'abord (onglet [0])",
    "dlg_find_first": "Cliquez d'abord sur 'Trouver les doublons'",
    "dlg_loaded": "Charge : ",
    "t7_title": "Historique des analyses",
    "t7_disk_sum": "Disques analyses",
    "t7_history": "Enregistrements",
    "t7_load": "Charger", "t7_del": "Suppr",
    "t7_del_confirm": "Supprimer la base du disque {drive} ?\n{path}\nIrreversible !",
    "t7_del_done": "Supprime : {path}",
    "t7_no_disk": "Aucune base de disque chargee",
    # Tab 8 Comparer historique
    "t8_title": "Comparer les analyses",
    "t8_desc": "Comparer deux analyses pour voir les changements",
    "t8_drive": "Disque : ",
    "t8_scan_a": "Analyse A (plus ancienne)",
    "t8_scan_b": "Analyse B (plus recente)",
    "t8_compare_btn": "Comparer",
    "t8_result": "Resultat de la comparaison",
    "t8_added": "Fichiers ajoutes",
    "t8_deleted": "Fichiers supprimes",
    "t8_modified": "Fichiers modifies",
    "t8_same": "Inchanges",
    "t8_added_size": "Taille ajoutee",
    "t8_deleted_size": "Taille supprimee",
    "t8_no_change": "Les deux analyses sont identiques",
    "t8_need_two": "Selectionnez un disque, puis deux analyses differentes a comparer",
    "t8_load_a": "Charger A", "t8_load_b": "Charger B",
    "t8_col_file": "Nom fichier", "t8_col_path": "Chemin",
    "t8_col_size": "Taille(Mo)", "t8_col_change": "Changement",
    "t8_changed": "Modifie",
    "t8_same_size": "Identique",
    "t8_new": "Nouveau",
    "t8_removed": "Supprime",
    "t8_no_sel": "Non selectionne",
    "t8_ready": "Pret a comparer",
    "t8_pick": "Choisissez un de chaque cote",
    "t8_same_db": "Même fichier de données sélectionné des deux côtés. Veuillez choisir des instantanés différents.",
    "t8_new_dir": "Nouveau dossier",
    "t8_del_dir": "Dossier supprimé",

    # Tab 3 Tendances colonnes
    "t3_col_month": "Mois", "t3_col_files": "Fichiers", "t3_col_size": "Taille(Go)", "t3_col_bar": "Graphique",
    # Tab 4 Categories colonnes
    "t4_col_dir": "Chemin dossier", "t4_col_ext2": "Extension",
    "t4_col_files": "Fichiers", "t4_col_size": "Taille(Go)",
    # Tab 5 Recherche colonnes
    "t5_col_name": "Nom fichier", "t5_col_path": "Chemin complet", "t5_col_size": "Taille(Go)",
    # Tab 6 Nettoyage colonnes
    "t6_col_name": "Nom fichier", "t6_col_path": "Chemin complet", "t6_col_size": "Taille(Mo)",
    # Tab 7 Historique colonnes
    "t7_col_drive": "Disque", "t7_col_snapshot": "Chemin instantane", "t7_col_last": "Dernier scan",
    "t7_col_files": "Fichiers", "t7_col_dirs": "Dossiers", "t7_col_size2": "Taille(Go)",
    "t7_col_status": "Statut", "t7_col_no": "#", "t7_col_root": "Chemin racine", "t7_col_time": "Heure scan",
}

_CURRENT_LANG = "zh"

def T(key):
    return _LANG[_CURRENT_LANG].get(key, _LANG["zh"].get(key, key))

def set_lang(code):
    global _CURRENT_LANG
    _CURRENT_LANG = code


# ======================================================== DB class ========================================================
class DB:
    def __init__(self, path):
        self.path = path
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.text_factory = str
        cu = self.conn.cursor()
        cu.execute(
            "CREATE TABLE IF NOT EXISTS dir_entries ("
            "id INTEGER PRIMARY KEY, name TEXT NOT NULL, path TEXT NOT NULL, "
            "size_bytes INTEGER DEFAULT 0, file_ext TEXT, mtime TEXT, "
            "content_hash TEXT, "
            "is_dir INTEGER DEFAULT 0, UNIQUE(path,name))"
        )
        cu.execute("CREATE TABLE IF NOT EXISTS scan_meta (key TEXT PRIMARY KEY, val TEXT)")
        cu.execute("CREATE INDEX IF NOT EXISTS ix_name ON dir_entries(name)")
        cu.execute("CREATE INDEX IF NOT EXISTS ix_size ON dir_entries(size_bytes)")
        cu.execute("CREATE INDEX IF NOT EXISTS ix_hash ON dir_entries(content_hash)")
        # Schema migration: add content_hash column if missing (old DBs)
        try:
            cu.execute("ALTER TABLE dir_entries ADD COLUMN content_hash TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists
        self.conn.commit()

    def clear(self):
        self.conn.execute("DELETE FROM dir_entries")
        self.conn.execute("DELETE FROM scan_meta")
        self.conn.commit()

    def batch_insert(self, rows):
        self.conn.executemany(
            "INSERT OR IGNORE INTO dir_entries"
            "(name,path,size_bytes,file_ext,mtime,content_hash,is_dir) VALUES(?,?,?,?,?,?,?)",
            rows
        )
        self.conn.commit()

    def set_meta(self, k, v):
        self.conn.execute(
            "INSERT OR REPLACE INTO scan_meta(key,val) VALUES(?,?)", (k, v)
        )
        self.conn.commit()

    def stats(self):
        cu = self.conn.cursor()
        tf = cu.execute(
            "SELECT COUNT(*) FROM dir_entries WHERE is_dir=0"
        ).fetchone()[0]
        td = cu.execute(
            "SELECT COUNT(*) FROM dir_entries WHERE is_dir=1"
        ).fetchone()[0]
        tb = cu.execute(
            "SELECT COALESCE(SUM(size_bytes),0) FROM dir_entries WHERE is_dir=0"
        ).fetchone()[0]
        return tf, td, tb

    def duplicates(self, min_mb=1):
        cu = self.conn.cursor()
        cu.execute(
            "SELECT name, size_bytes, COUNT(*) copies, "
            "GROUP_CONCAT(path||char(92)||name, char(10)) paths "
            "FROM dir_entries WHERE is_dir=0 AND size_bytes>? "
            "GROUP BY name,size_bytes HAVING COUNT(*)>1 "
            "ORDER BY (COUNT(*)-1)*size_bytes DESC",
            (min_mb * 1024 * 1024,)
        )
        return cu.fetchall()

    def trend(self):
        cu = self.conn.cursor()
        cu.execute(
            "SELECT SUBSTR(mtime,1,7), COUNT(*), COALESCE(SUM(size_bytes),0) "
            "FROM dir_entries WHERE is_dir=0 AND mtime>'_' "
            "GROUP BY 1 ORDER BY 1 DESC LIMIT 24"
        )
        return cu.fetchall()

    def top_dirs(self, n=20):
        cu = self.conn.cursor()
        cu.execute(
            "SELECT path, COUNT(*), COALESCE(SUM(size_bytes),0) "
            "FROM dir_entries WHERE is_dir=1 "
            "GROUP BY path ORDER BY 3 DESC LIMIT ?", (n,)
        )
        return cu.fetchall()

    def ext_stats(self):
        cu = self.conn.cursor()
        cu.execute(
            "SELECT file_ext, COUNT(*), COALESCE(SUM(size_bytes),0) "
            "FROM dir_entries WHERE is_dir=0 "
            "GROUP BY file_ext ORDER BY 3 DESC LIMIT 30"
        )
        return cu.fetchall()

    def search(self, q, n=200):
        cu = self.conn.cursor()
        cu.execute(
            "SELECT name, path||char(92)||name, size_bytes "
            "FROM dir_entries WHERE is_dir=0 AND name LIKE ? "
            "ORDER BY size_bytes DESC LIMIT ?",
            ("%" + q + "%", n)
        )
        return cu.fetchall()

    def small_files(self, max_mb=1):
        cu = self.conn.cursor()
        cu.execute(
            "SELECT name, path||char(92)||name, size_bytes "
            "FROM dir_entries WHERE is_dir=0 AND size_bytes<=? "
            "ORDER BY size_bytes DESC LIMIT 500",
            (max_mb * 1024 * 1024,)
        )
        return cu.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()


# ======================================================== Scanner class ========================================================
class Scanner(threading.Thread):
    def __init__(self, root_path, snapshot_path, on_prog, on_done, enable_hash=False):
        super().__init__(daemon=True)
        self.root_path = root_path
        self.snapshot_path = snapshot_path
        self.on_prog = on_prog
        self.on_done = on_done
        self.enable_hash = enable_hash
        self._stop = threading.Event()
        self.fc = self.dc = 0
        self.bc = 0

    def stop(self):
        self._stop.set()

    def run(self):
        self.db = DB(self.snapshot_path)
        self.db.connect()
        self.db.clear()
        try:
            self.db.set_meta("root", self.root_path)
            self.db.set_meta("time", time.strftime("%Y-%m-%d %H:%M:%S"))
            batch, last = [], time.time()
            for dp, dns, fns in os.walk(self.root_path):
                if self._stop.is_set():
                    break
                for d in dns:
                    if self._stop.is_set():
                        break
                    rp = os.path.relpath(os.path.join(dp, d), self.root_path)
                    batch.append((d, rp, 0, "", "", None, 1))
                    self.dc += 1
                for f in fns:
                    if self._stop.is_set():
                        break
                    fp = os.path.join(dp, f)
                    rp = os.path.relpath(dp, self.root_path)
                    _, ext = os.path.splitext(f)
                    try:
                        sz = os.path.getsize(fp)
                        mt = time.strftime(
                            "%Y-%m-%d %H:%M:%S",
                            time.localtime(os.path.getmtime(fp))
                        )
                    except Exception:
                        sz, mt = 0, ""
                    h = quick_hash(fp) if self.enable_hash else None
                    batch.append((f, rp, sz, ext.lower(), mt, h, 0))
                    self.fc += 1
                    self.bc += sz
                if time.time() - last > 0.5 or len(batch) >= 500:
                    if batch:
                        self.db.batch_insert(batch)
                        batch = []
                        last = time.time()
                    self.on_prog("scan", self.fc, self.dc, self.bc)
            if batch:
                self.db.batch_insert(batch)
            self.on_prog("done", self.fc, self.fc, self.bc)
            self.on_done(self.fc, self.dc, self.bc)
        except Exception as e:
            self.on_done(0, 0, 0, error=str(e))
        finally:
            if self.db and self.db.conn:
                self.db.conn.close()

# ======================================================== App class ========================================================
class App:
    BG = "#1e1e2e"
    BG2 = "#2a2a3e"
    FG = "#cdd6f4"
    AC = "#89b4fa"
    GR = "#a6e3a1"
    RD = "#f38ba8"
    YL = "#f9e2af"
    PU = "#cba6f7"
    GY = "#6c7086"
    BL = "#313244"
    LANGS = [("中文", "zh"), ("EN", "en"), ("FR", "fr")]

    def __init__(self, root):
        self.root = root
        self.root.title("File Organizer Pro v" + VER)
        self.root.geometry("1120x740")
        self.root.minsize(900, 600)
        self.root.configure(bg=self.BG)
        self.db = None
        self.current_drive = None
        self.meta_conn = None
        self.scanner = None
        self.dup_data = []
        self._current_tab = 0
        self._lang_btns = []
# Generic sort tree helper
        self._dup_sort_col = None; self._dup_sort_asc = False
        self._ext_sort_col = None; self._ext_sort_asc = False
        self._month_sort_col = None; self._month_sort_asc = False
        self._trend_sort_col = None; self._trend_sort_asc = False
        self._cat_dir_sort_col = None; self._cat_dir_sort_asc = False
        self._cat_ext_sort_col = None; self._cat_ext_sort_asc = False
        self._sr_sort_col = None; self._sr_sort_asc = False
        self._sm_sort_col = None; self._sm_sort_asc = False
        self._hist_disk_sort_col = None; self._hist_disk_sort_asc = False
        self._hist_scan_sort_col = None; self._hist_scan_sort_asc = False
        self.history_var = tk.StringVar()
        self._history_map = {}
        self._init_meta_db()
        self._build()
        self._try_load_last_disk()

    def _init_meta_db(self):
        self.meta_conn = sqlite3.connect(META_DB)
        self.meta_conn.execute("PRAGMA journal_mode=WAL")
        cu = self.meta_conn.cursor()
        cu.execute(
            "CREATE TABLE IF NOT EXISTS drives ("
            "drive_letter TEXT PRIMARY KEY, "
            "root_path TEXT NOT NULL, last_scan_time TEXT, "
            "file_count INTEGER DEFAULT 0, dir_count INTEGER DEFAULT 0, "
            "total_bytes INTEGER DEFAULT 0)"
        )
        cu.execute(
            "CREATE TABLE IF NOT EXISTS scans ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "drive_letter TEXT NOT NULL, "
            "snapshot_path TEXT NOT NULL, "
            "root_path NOT NULL, scan_time TEXT NOT NULL, "
            "file_count INTEGER DEFAULT 0, dir_count INTEGER DEFAULT 0, "
            "total_bytes INTEGER DEFAULT 0)"
        )
        self.meta_conn.commit()
# ======================================================== Schema migration: add missing columns to existing tables ========================================================
        for col_sql in [
            ("drives", "last_snapshot_path", "TEXT"),
            ("scans",  "snapshot_path",      "TEXT"),
        ]:
            tbl, col, ctype = col_sql
            try:
                cu.execute("ALTER TABLE {} ADD COLUMN {} {}".format(tbl, col, ctype))
                self.meta_conn.commit()
            except sqlite3.OperationalError:
                pass  # column already exists
        # Backfill: copy legacy db_path → new snapshot_path / last_snapshot_path
        try:
            cu.execute("UPDATE scans SET snapshot_path=db_path WHERE snapshot_path IS NULL AND db_path IS NOT NULL")
            cu.execute("UPDATE drives SET last_snapshot_path=db_path WHERE last_snapshot_path IS NULL AND db_path IS NOT NULL")
            self.meta_conn.commit()
        except sqlite3.OperationalError:
            pass  # columns don't exist yet

    def _try_load_last_disk(self):
        cu = self.meta_conn.cursor()
        # Try new column first, fall back to legacy db_path
        row = cu.execute(
            "SELECT drive_letter, last_snapshot_path FROM drives "
            "ORDER BY last_scan_time DESC LIMIT 1"
        ).fetchone()
        if not row or not row[1] or not os.path.exists(row[1]):
            try:
                row = cu.execute(
                    "SELECT drive_letter, db_path FROM drives "
                    "ORDER BY last_scan_time DESC LIMIT 1"
                ).fetchone()
            except sqlite3.OperationalError:
                row = None
        if row and row[1] and os.path.exists(row[1]):
            try:
                self.db = DB(row[1])
                self.db.connect()
                self.current_drive = row[0]
                self._refresh()
            except Exception:
                pass
        self._refresh_history_combo()

    def _refresh_history_combo(self):
        """Refresh history dropdown (show all scan snapshots)."""
        cu = self.meta_conn.cursor()
        rows = cu.execute(
            "SELECT id, drive_letter, snapshot_path, root_path, scan_time, "
            "file_count, total_bytes FROM scans "
            "ORDER BY drive_letter, scan_time DESC"
        ).fetchall()
        if not rows:
            self.history_combo['values'] = [T("history_combo_empty")]
            self.history_var.set(T("history_combo_empty"))
            return
        values = []
        self._history_map = {}
        for sid, dl, sp, rp, st, fc, tb in rows:
            if not os.path.exists(sp):
                continue
            if dl and len(dl) == 1:
                display = "[{}] {}  ({} files)".format(dl, st, fc)
            else:
                display = "[DIR] {}  ({} files)".format(rp, fc)
            values.append(display)
            self._history_map[display] = (sid, sp)
        if not values:
            self.history_combo['values'] = [T("history_combo_empty")]
            self.history_var.set(T("history_combo_empty"))
            return
        self.history_combo['values'] = values
        self.history_var.set(values[0])

    def _on_history_select(self, event):
        """Handle history dropdown (load selected snapshot)."""
        selected = self.history_var.get()
        if selected == T("history_combo_empty") or not hasattr(self, '_history_map'):
            return
        info = self._history_map.get(selected)
        if not info:
            return
        scan_id, snapshot_path = info
        try:
            if self.db:
                self.db.close()
            self.db = DB(snapshot_path)
            self.db.connect()
            self._refresh()
            self._nav(self._current_tab)
            self._st("[OK] " + os.path.basename(snapshot_path))
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _set_lang(self, code):
        set_lang(code)
        self._refresh_lang_btns()
        # 刷新导航菜单文本
        for btn, (msg_key, idx) in zip(self.nav_btns, self._nav_items):
            btn.configure(text=T(msg_key))
        self._nav(self._current_tab)

    def _refresh_lang_btns(self):
        for label, code in self.LANGS:
            idx = self.LANGS.index((label, code))
            btn = self._lang_btns[idx]
            if code == _CURRENT_LANG:
                btn.configure(bg=self.AC, fg=self.BG)
            else:
                btn.configure(bg=self.BL, fg=self.FG)

    def _build(self):
        hdr = tk.Frame(self.root, bg=self.BG2, height=46)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="File Organizer Pro",
            font=("Microsoft YaHei UI", 14, "bold"),
            bg=self.BG2, fg=self.AC
        ).pack(side="left", padx=16, pady=6)
        tk.Label(
            hdr, text=T("app_subtitle"),
            bg=self.BG2, fg=self.GY, font=("Microsoft YaHei UI", 9)
        ).pack(side="left", padx=5, pady=6)

        # History dropdown (left of language selector)
        history_frame = tk.Frame(hdr, bg=self.BG2)
        history_frame.pack(side="right", padx=(0, 16))
        tk.Label(
            history_frame,
            text=T("history_label") + ": ",
            bg=self.BG2, fg=self.GY, font=("Microsoft YaHei UI", 8)
        ).pack(side="left", pady=6)
        self.history_combo = ttk.Combobox(
            history_frame,
            textvariable=self.history_var,
            state="readonly",
            width=28,
            font=("Microsoft YaHei UI", 9)
        )
        self.history_combo.pack(side="left", pady=6)
        self.history_combo.bind("<<ComboboxSelected>>", self._on_history_select)

        # Language selector
        lang_frame = tk.Frame(hdr, bg=self.BG2)
        lang_frame.pack(side="right", padx=(0, 8))
        tk.Label(
            lang_frame,
            text=T("lang_label") + " ",
            bg=self.BG2, fg=self.GY, font=("Microsoft YaHei UI", 8)
        ).pack(side="left", pady=6)
        for label, code in self.LANGS:
            btn = tk.Button(
                lang_frame, text=label,
                font=("Microsoft YaHei UI", 9, "bold"),
                bg=self.BL if code != _CURRENT_LANG else self.AC,
                fg=self.BG if code == _CURRENT_LANG else self.FG,
                relief="flat", padx=7, pady=2,
                cursor="hand2",
                command=lambda c=code: self._set_lang(c)
            )
            btn.pack(side="left", padx=1)
            self._lang_btns.append(btn)

        self.stat_lbl = tk.Label(
            hdr, text=T("not_scanned"),
            bg=self.BG2, fg=self.GY, font=("Microsoft YaHei UI", 9)
        )
        self.stat_lbl.pack(side="right", padx=4, pady=6)

        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=8, pady=(5, 5))

        nav = tk.Frame(main, bg=self.BG2, width=172)
        nav.pack(side="left", fill="y", padx=(0, 8))
        nav.pack_propagate(False)

        self._nav_items = [
            ("nav_0", 0), ("nav_1", 1), ("nav_2", 2),
            ("nav_3", 3), ("nav_4", 4), ("nav_5", 5),
            ("nav_6", 6), ("nav_7", 7), ("nav_8", 8),
        ]
        self.nav_btns = []
        for msg_key, idx in self._nav_items:
            btn = tk.Label(
                nav, text=T(msg_key),
                font=("Microsoft YaHei UI", 10),
                bg=self.BG2, fg=self.FG,
                cursor="hand2", anchor="w", padx=14, pady=9
            )
            btn.pack(fill="x", padx=4, pady=1)
            btn.bind("<Button-1>", lambda e, i=idx: self._nav(i))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=self.BL))
            btn.bind("<Leave>", lambda e, b=btn: b.configure(bg=self.BG2))
            self.nav_btns.append(btn)

        self.content = tk.Frame(main, bg=self.BG)
        self.content.pack(side="left", fill="both", expand=True)

        st = tk.Frame(self.root, bg=self.BG2, height=24)
        st.pack(fill="x")
        st.pack_propagate(False)
        self.st_lbl = tk.Label(
            st, text=T("status_ready"),
            bg=self.BG2, fg=self.GY,
            font=("Microsoft YaHei UI", 8), anchor="w"
        )
        self.st_lbl.pack(side="left", padx=12, fill="x", expand=True)
        self._nav(0)

    def _nav(self, idx):
        self._current_tab = idx
        for b in self.nav_btns:
            b.configure(bg=self.BG2, fg=self.FG)
        self.nav_btns[idx].configure(bg=self.BL, fg=self.AC)
        tabs = [
            self._tab_scan, self._tab_overview, self._tab_dup,
            self._tab_trends, self._tab_cats, self._tab_search,
            self._tab_cleanup, self._tab_history, self._tab_compare
        ]
        tabs[idx]()

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _st(self, msg):
        self.st_lbl.config(text=msg)
        self.root.update_idletasks()

    def _ok_db(self):
        if not self.db:
            messagebox.showwarning(T("dlg_tip"), T("dlg_scan_first"))
            self._nav(0)
            return False
        return True

    def _refresh(self):
        if not self.db:
            drive_info = ""
            if self.current_drive:
                drive_info = "[{}] ".format(self.current_drive)
            self.stat_lbl.config(text=drive_info + T("not_scanned"))
            return
        try:
            tf, td, tb = self.db.stats()
            drive_info = ""
            if self.current_drive:
                drive_info = "[{}] ".format(self.current_drive)
            self.stat_lbl.config(
                text="{}{:,} files  {:,} dirs  {:.1f} GB".format(
                    drive_info, tf, td, tb / 1024**3
                )
            )
        except Exception:
            pass

    def _tree(self, parent, cols, widths):
        frm = tk.Frame(parent)
        frm.pack(fill="both", expand=True, pady=(0, 4))
        sty = ttk.Style()
        sty.theme_use("clam")
        sty.configure(
            "Treeview",
            background=self.BG, foreground=self.FG,
            fieldbackground=self.BG, rowheight=22,
            font=("Microsoft YaHei UI", 9)
        )
        sty.configure(
            "Treeview.Heading",
            background=self.BG2, foreground=self.AC,
            font=("Microsoft YaHei UI", 9, "bold")
        )
        vsb = ttk.Scrollbar(frm, orient="vertical")
        hsb = ttk.Scrollbar(frm, orient="horizontal")
        tr = ttk.Treeview(
            frm, columns=cols, show="headings",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set
        )
        vsb.config(command=tr.yview)
        hsb.config(command=tr.xview)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")
        tr.pack(side="left", fill="both", expand=True)
        for col, w in zip(cols, widths):
            tr.heading(col, text=col, anchor="w")
            tr.column(col, width=w, minwidth=40)
        return tr

    def _box(self, parent, title):
        bx = tk.LabelFrame(
            parent, text="  " + title + "  ",
            bg=self.BG2, fg=self.AC,
            font=("Microsoft YaHei UI", 10, "bold"),
            padx=14, pady=10, labelanchor="n"
        )
        bx.pack(fill="x", pady=(0, 10))
        return bx

# ======================================================== TAB 0: Scan ========================================================
    def _tab_scan(self):
        self._clear()
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)

        bx1 = self._box(p, T("t0_title"))
        self.path_var = tk.StringVar(
            value=os.getcwd() if os.path.exists(os.getcwd()) else "C:\\"
        )
        tk.Entry(
            bx1, textvariable=self.path_var,
            font=("Consolas", 11), bg=self.BL, fg=self.FG,
            insertbackground=self.AC, relief="flat", width=62
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Button(
            bx1, text=T("t0_browse"), command=self._browse,
            bg=self.AC, fg=self.BG, font=("Microsoft YaHei UI", 10),
            relief="flat", padx=12, pady=4, cursor="hand2"
        ).pack(side="left")
        tk.Button(
            bx1, text=T("t0_load_db"), command=self._load_db,
            bg=self.PU, fg="white", font=("Microsoft YaHei UI", 9),
            relief="flat", padx=8, pady=4, cursor="hand2"
        ).pack(side="left", padx=(6, 0))

        br = tk.Frame(p, bg=self.BG)
        br.pack(fill="x", pady=(0, 6))
        self.scan_btn = tk.Button(
            br, text=T("t0_start"), command=self._do_scan,
            bg=self.AC, fg=self.BG, font=("Microsoft YaHei UI", 12, "bold"),
            relief="flat", padx=28, pady=8, cursor="hand2"
        )
        self.scan_btn.pack(side="left")
        self.stop_btn = tk.Button(
            br, text=T("t0_stop"), command=self._do_stop,
            state="disabled", bg=self.RD, fg="white",
            font=("Microsoft YaHei UI", 10), relief="flat",
            padx=16, pady=8, cursor="hand2"
        )
        self.stop_btn.pack(side="left", padx=(8, 0))

        # Hash enable checkbox
        self.hash_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            br, text=T("t0_hash"), variable=self.hash_var,
            bg=self.BG, fg=self.FG, selectcolor=self.BG2,
            font=("Microsoft YaHei UI", 9), activebackground=self.BG,
            activeforeground=self.FG
        ).pack(side="left", padx=(16, 0))

        self.pv = tk.DoubleVar()
        ttk.Progressbar(p, variable=self.pv, maximum=100).pack(
            fill="x", pady=(0, 4)
        )
        self.pl = tk.Label(
            p, text="", bg=self.BG, fg=self.YL, font=("Microsoft YaHei UI", 9)
        )
        self.pl.pack(anchor="w")

        bx2 = self._box(p, T("t0_log"))
        self.log_txt = scrolledtext.ScrolledText(
            bx2, height=14, bg=self.BG, fg=self.GR,
            font=("Consolas", 9), insertbackground=self.AC,
            relief="flat", state="disabled", wrap="none"
        )
        self.log_txt.pack(fill="both", expand=True)

    def _log(self, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        line = "[" + timestamp + "] " + msg
        # Write to log file
        try:
            log_file = os.path.join(init_log_dir(),
                                   "file_organizer_{}.log".format(
                                       time.strftime("%Y%m%d")))
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass
        # Write to UI
        try:
            if not hasattr(self, "log_txt") or not self.log_txt.winfo_exists():
                return
        except Exception:
            return
        self.log_txt.config(state="normal")
        self.log_txt.insert("end", "[" + time.strftime("%H:%M:%S") + "] " + msg + "\n")
        self.log_txt.see("end")
        self.log_txt.config(state="disabled")
        self.root.update_idletasks()

    def _browse(self):
        path = filedialog.askdirectory(title="Select folder or drive root")
        if path:
            self.path_var.set(path)

    def _load_db(self):
        path = filedialog.askopenfilename(
            title="Load existing database",
            filetypes=[("SQLite DB", "*.db"), ("All files", "*.*")]
        )
        if path and os.path.exists(path):
            try:
                if self.db:
                    self.db.close()
                self.db = DB(path)
                self.db.connect()
                self.current_drive = None
                # Try to infer drive from filename
                basename = os.path.basename(path)
                if basename.startswith("disk_") and basename.endswith(".db"):
                    self.current_drive = basename[5:-3].upper()
                self._refresh()
                self._log("[" + T("dlg_loaded") + "] " + path)
                self._st(T("dlg_loaded") + path)
            except Exception as e:
                messagebox.showerror(T("dlg_err"), "Load failed: " + str(e))

    def _do_scan(self):
        path = self.path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror(T("dlg_err"), T("t0_err_path") + path)
            return
        drive_letter = os.path.splitdrive(path)[0].rstrip(":").upper()
        if not drive_letter:
            drive_letter = "UNK"

        # New dated snapshot: each scan = one independent .db file
        timestamp = time.strftime("%Y%m%dT%H%M%S")
        snapshot_path = disk_snapshot_path(drive_letter, timestamp)
        self.current_drive = drive_letter

        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.pv.set(0)
        self._log("[START] {} -> {}".format(path, snapshot_path))

        def on_prog(state, fc, dc, bc):
            if state == "scan":
                self.pl.config(
                    text="[{}] Scanning: {:,} files  {:,} dirs  {:.1f} GB".format(
                        drive_letter, fc, dc, bc / 1024**3
                    )
                )
                if fc > 0:
                    progress = 50 * (1 - math.exp(-fc / 5000))
                else:
                    progress = 0
                self.pv.set(min(99, progress))
                self.root.update_idletasks()

        def on_done(fc, dc, bc, error=None):
            self.scan_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.pv.set(100)
            if error:
                self._log("[ERROR] " + error)
                messagebox.showerror(T("dlg_err"), error)
            else:
                self.root.after(0, lambda: self._on_scan_done(
                    drive_letter, snapshot_path, path, fc, dc, bc
                ))

        self.scanner = Scanner(path, snapshot_path, on_prog, on_done, self.hash_var.get())
        self.scanner.start()

    def _on_scan_done(self, drive_letter, snapshot_path, root_path, fc, dc, bc):
        """Called in main thread after scan completes."""
        if self.db:
            try:
                self.db.close()
            except Exception:
                pass
        self.db = DB(snapshot_path)
        self.db.connect()

        scan_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            cu = self.meta_conn.cursor()
            cu.execute(
                "INSERT OR REPLACE INTO drives "
                "(drive_letter, root_path, last_scan_time, "
                "file_count, dir_count, total_bytes, last_snapshot_path) "
                "VALUES (?,?,?,?,?,?,?)",
                (drive_letter, root_path, scan_time_str, fc, dc, bc, snapshot_path)
            )
            cu.execute(
                "INSERT INTO scans "
                "(drive_letter, snapshot_path, root_path, scan_time, "
                "file_count, dir_count, total_bytes) "
                "VALUES (?,?,?,?,?,?,?)",
                (drive_letter, snapshot_path, root_path, scan_time_str, fc, dc, bc)
            )
            self.meta_conn.commit()
        except Exception as e:
            self._log("[META DB ERROR] " + str(e))

        self._log("[DONE] {} {:,} files  {:,} dirs  {:.2f} GB".format(
            drive_letter, fc, dc, bc / 1024**3))
        self._refresh()
        self._refresh_history_combo()
        self._st("[{}] {}".format(drive_letter, os.path.basename(snapshot_path)))
        messagebox.showinfo(
            T("t0_done_title"),
            "[{}] ".format(drive_letter) + T("t0_done_msg").format(
                fc, dc, bc / 1024**3
            )
        )

    def _do_stop(self):
        if self.scanner:
            self.scanner.stop()
            self._log("[STOPPED]")
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

# ======================================================== TAB 1: Overview ========================================================
    def _tab_overview(self):
        self._clear()
        if not self._ok_db():
            return
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t1_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 12))

        tf, td, tb = self.db.stats()
        cards = [
            (T("t1_files"), "{:,}".format(tf), self.AC),
            (T("t1_dirs"), "{:,}".format(td), self.PU),
            (T("t1_size"), "{:.1f} GB".format(tb / 1024**3), self.GR),
            (T("t1_db"), self.db.path, self.YL),
        ]
        r1 = tk.Frame(p, bg=self.BG)
        r1.pack(fill="x", pady=(0, 12))
        for label, val, color in cards:
            cf = tk.Frame(r1, bg=self.BG2, padx=10)
            cf.pack(side="left", fill="both", expand=True, padx=3)
            tk.Label(
                cf, text=label, bg=self.BG2, fg=self.GY,
                font=("Microsoft YaHei UI", 9)
            ).pack(pady=(8, 2))
            tk.Label(
                cf, text=val, bg=self.BG2, fg=color,
                font=("Microsoft YaHei UI", 16, "bold")
            ).pack(pady=(0, 8))

        tk.Label(
            p, text=T("t1_by_ext"),
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.BG, fg=self.YL, anchor="w"
        ).pack(anchor="w", pady=(4, 4))
        self.ext_tree = self._tree(
            p, [T("t1_col_ext"), T("t1_col_files"), T("t1_col_size"), T("t1_col_bar")], [100, 80, 100, 350]
        )
        # 排序功能兘
        for col in (T("t1_col_files"), T("t1_col_size")):
            self.ext_tree.heading(col, command=lambda c=col: self._sort_ext_tree(c))
        ed = self.db.ext_stats()
        tb2 = sum(r[2] for r in ed) or 1
        for ext, cnt, b in ed[:25]:
            pct = b / tb2 * 100
            bar = chr(9608) * min(int(pct / 2), 35)
            self.ext_tree.insert("", "end", values=(
                ext or "(none)", "{:,}".format(cnt),
                "{:.1f}".format(b / 1024**3),
                "{:.1f}% {}".format(pct, bar)
            ))

        tk.Label(
            p, text=T("t1_by_month"),
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.BG, fg=self.YL, anchor="w"
        ).pack(anchor="w", pady=(12, 4))
        self.month_tree = self._tree(p, [T("t1_col_month"), T("t1_col_files"), T("t1_col_size")], [120, 100, 100])
        # 排序功能兘
        for col in (T("t1_col_files"), T("t1_col_size")):
            self.month_tree.heading(col, command=lambda c=col: self._sort_month_tree(c))
        for mo, cnt, b in self.db.trend()[:12]:
            self.month_tree.insert("", "end", values=(
                mo, "{:,}".format(cnt), "{:.1f}".format(b / 1024**3)
            ))

# ======================================================== TAB 2: Duplicates ========================================================
    def _tab_dup(self):
        self._clear()
        if not self._ok_db():
            return
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t2_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 8))

        cr = tk.Frame(p, bg=self.BG)
        cr.pack(fill="x", pady=(0, 6))
        tk.Label(
            cr, text=T("t2_min_size"), bg=self.BG, fg=self.FG
        ).pack(side="left")
        self.msv = tk.StringVar(value="1")
        tk.Entry(
            cr, textvariable=self.msv, width=7,
            bg=self.BL, fg=self.FG, relief="flat"
        ).pack(side="left", padx=5)
        tk.Button(
            cr, text=T("t2_find"), command=self._find_dup,
            bg=self.AC, fg=self.BG, font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=14, pady=5, cursor="hand2"
        ).pack(side="left", padx=(8, 0))
        self.dup_lbl = tk.Label(
            cr, text="", bg=self.BG, fg=self.YL,
            font=("Microsoft YaHei UI", 10)
        )
        self.dup_lbl.pack(side="left", padx=14)

        self.dup_tree = self._tree(
            p,
            [T("t2_col_name"), T("t2_col_size"), T("t2_col_copies"), T("t2_col_wasted"), T("t2_col_path")],
            [230, 80, 50, 90, 400]
        )
        # Configure sortable headers
        for col in (T("t2_col_size"), T("t2_col_copies"), T("t2_col_wasted")):
            self.dup_tree.heading(col, command=lambda c=col: self._sort_dup_tree(c))
        r2 = tk.Frame(p, bg=self.BG)
        r2.pack(fill="x", pady=(6, 0))
        tk.Button(
            r2, text=T("t2_del_btn"),
            command=self._preview_del,
            bg=self.RD, fg="white",
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=14, pady=6, cursor="hand2"
        ).pack(side="left")

    def _find_dup(self):
        try:
            mm = int(self.msv.get())
        except Exception:
            mm = 1
        self._log("[FIND] Duplicates (>{}MB)...".format(mm))
        rows = self.db.duplicates(mm)
        self.dup_data = rows
        wasted = sum((r[2] - 1) * r[1] / 1024**3 for r in rows)
        self.dup_lbl.config(
            text="{:,} groups  |  {:.1f} GB recoverable".format(
                len(rows), wasted
            )
        )
        for i in self.dup_tree.get_children():
            self.dup_tree.delete(i)
        for row in rows[:300]:
            name, size, copies, paths = row
            wg = (copies - 1) * size / 1024**3
            fp = (paths or "").split(chr(10))[0][:80]
            self.dup_tree.insert("", "end", values=(
                name[:45],
                "{:.2f}".format(size / 1024**3),
                copies,
                "{:.2f}".format(wg),
                fp
            ))

    def _sort_dup_tree(self, col):
        self._generic_sort_tree(self.dup_tree, col,
            '_dup_sort_col', '_dup_sort_asc',
            (T("t2_col_size"), T("t2_col_copies"), T("t2_col_wasted")))

    def _sort_ext_tree(self, col):
        self._generic_sort_tree(self.ext_tree, col,
            '_ext_sort_col', '_ext_sort_asc',
            (T("t1_col_files"), T("t1_col_size")))

    def _sort_month_tree(self, col):
        self._generic_sort_tree(self.month_tree, col,
            '_month_sort_col', '_month_sort_asc',
            (T("t1_col_files"), T("t1_col_size")))

# ======================================================== Generic sort tree helper ========================================================
    def _generic_sort_tree(self, tree, col, sort_col_attr, sort_asc_attr, all_sort_cols):
        """通用 Treeview 排序方法"""
        # 切换排序簭鏂瑰悜
        cur_col = getattr(self, sort_col_attr, None)
        cur_asc = getattr(self, sort_asc_attr, False)
        if cur_col == col:
            cur_asc = not cur_asc
        else:
            cur_col = col
            cur_asc = False  # First click: descending (largest first)
        setattr(self, sort_col_attr, cur_col)
        setattr(self, sort_asc_attr, cur_asc)

# Get all items for sorting
        items = [(tree.set(item, col), item) for item in tree.get_children('')]

# Test data - also copy to results
        try:
            items.sort(key=lambda x: float(x[0].replace(',', '')), reverse=not cur_asc)
        except ValueError:
            items.sort(key=lambda x: x[0], reverse=not cur_asc)

        # 重排
        for idx, (_, item) in enumerate(items):
            tree.move(item, '', idx)

# Update column header (add arrow indicator)
        for c in all_sort_cols:
            text = c
            if c == col:
                text = c + (" ▲" if cur_asc else " ▼")
            tree.heading(c, text=text)

    def _sort_trend_tree(self, col):
        self._generic_sort_tree(self.trend_tree, col,
            '_trend_sort_col', '_trend_sort_asc',
            (T("t3_col_files"), T("t3_col_size")))

    def _sort_cat_dir_tree(self, col):
        self._generic_sort_tree(self.cat_dir_tree, col,
            '_cat_dir_sort_col', '_cat_dir_sort_asc',
            (T("t4_col_files"), T("t4_col_size")))

    def _sort_cat_ext_tree(self, col):
        self._generic_sort_tree(self.cat_ext_tree, col,
            '_cat_ext_sort_col', '_cat_ext_sort_asc',
            (T("t4_col_files"), T("t4_col_size")))

    def _sort_sr_tree(self, col):
        self._generic_sort_tree(self.sr_tree, col,
            '_sr_sort_col', '_sr_sort_asc',
            (T("t5_col_size"),))

    def _sort_sm_tree(self, col):
        self._generic_sort_tree(self.sm_tree, col,
            '_sm_sort_col', '_sm_sort_asc',
            (T("t6_col_size"),))

    def _sort_hist_disk_tree(self, col):
        self._generic_sort_tree(self.hist_disk_tree, col,
            '_hist_disk_sort_col', '_hist_disk_sort_asc',
            (T("t7_col_files"), T("t7_col_dirs"), T("t7_col_size2")))

    def _sort_hist_scan_tree(self, col):
        self._generic_sort_tree(self.hist_scan_tree, col,
            '_hist_scan_sort_col', '_hist_scan_sort_asc',
            (T("t7_col_files"), T("t7_col_size2")))

    def _preview_del(self):
        if not self.dup_data:
            messagebox.showwarning(T("dlg_tip"), T("dlg_find_first"))
            return
        pw = tk.Toplevel(self.root)
        pw.title(T("t2_prev_title"))
        pw.geometry("960x660")
        pw.configure(bg=self.BG)
        tk.Label(
            pw, text=T("t2_prev_warn"),
            bg=self.BG, fg=self.YL,
            font=("Microsoft YaHei UI", 12, "bold")
        ).pack(pady=10)
        txt = scrolledtext.ScrolledText(
            pw, bg=self.BG, fg=self.FG,
            font=("Consolas", 9), state="normal", wrap="none"
        )
        txt.pack(fill="both", expand=True, padx=10, pady=5)
        txt.tag_config("k", foreground=self.GR)
        txt.tag_config("d", foreground=self.RD)
        txt.tag_config("h", foreground=self.YL)
        tot = 0
        for name, size, copies, paths in self.dup_data:
            wg = (copies - 1) * size
            tot += wg
            txt.insert(
                "end",
                "X {}  ({} copies -> del {}  waste {:.2f} GB)\n".format(
                    name, copies, copies - 1, wg / 1024**3
                ),
                "h"
            )
            if paths:
                all_p = paths.split(chr(10))
                txt.insert(
                    "end", "  " + T("t2_keep") + " " + all_p[0] + "\n", "k"
                )
                for pp in all_p[1:]:
                    txt.insert(
                        "end",
                        "  " + T("t2_del") + " " + pp.strip() + "\n", "d"
                    )
            txt.insert("end", "\n")
        txt.config(state="disabled")
        tk.Label(
            pw,
            text="Total recoverable: {:.1f} GB".format(tot / 1024**3),
            bg=self.BG, fg=self.YL,
            font=("Microsoft YaHei UI", 11, "bold")
        ).pack(pady=6)
        br2 = tk.Frame(pw, bg=self.BG)
        br2.pack(pady=8)

        def do_del():
            if not messagebox.askyesno(T("dlg_tip"), T("t2_confirm")):
                return
            pw.destroy()
            self._do_delete()

        tk.Button(
            br2, text=T("t2_confirm_btn"), command=do_del,
            bg=self.RD, fg="white",
            font=("Microsoft YaHei UI", 11, "bold"),
            relief="flat", padx=22, pady=7, cursor="hand2"
        ).pack(side="left")
        tk.Button(
            br2, text=T("t2_cancel"), command=pw.destroy,
            bg=self.GY, fg="white",
            font=("Microsoft YaHei UI", 10),
            relief="flat", padx=20, pady=7, cursor="hand2"
        ).pack(side="left", padx=10)

    def _do_delete(self):
        dcnt, ecnt, trec = 0, 0, 0
        for name, size, copies, paths in self.dup_data:
            if not paths:
                continue
            for pp in paths.split(chr(10))[1:]:
                pp = pp.strip()
                if not pp:
                    continue
                try:
                    if os.path.exists(pp):
                        os.remove(pp)
                        dcnt += 1
                        trec += size
                    else:
                        ecnt += 1
                except Exception:
                    ecnt += 1
        messagebox.showinfo(
            T("dlg_tip"),
            T("t2_done").format(dcnt, ecnt, trec / 1024**3)
        )
        self._log(
            "[DELETE] {:,} files, recovered {:.1f} GB".format(
                dcnt, trec / 1024**3
            )
        )
        self._nav(0)

# ======================================================== TAB 3: Trends ========================================================
    def _tab_trends(self):
        self._clear()
        if not self._ok_db():
            return
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t3_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 12))
        self.trend_tree = self._tree(
            p, [T("t3_col_month"), T("t3_col_files"), T("t3_col_size"), T("t3_col_bar")],
            [110, 90, 100, 450]
        )
        # 排序功能兘
        for col in (T("t3_col_files"), T("t3_col_size")):
            self.trend_tree.heading(col, command=lambda c=col: self._sort_trend_tree(c))
        rows = self.db.trend()
        mx = max((r[1] for r in rows), default=1)
        for mo, cnt, b in reversed(rows):
            bar = chr(9608) * int(cnt / mx * 45)
            self.trend_tree.insert("", "end", values=(
                mo, "{:,}".format(cnt),
                "{:.1f}".format(b / 1024**3), bar
            ))

# ======================================================== TAB 4: Categories ========================================================
    def _tab_cats(self):
        self._clear()
        if not self._ok_db():
            return
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t4_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 12))

# ======================================================== Pie charts (matplotlib) ========================================================
        ext_data = self.db.ext_stats()[:10]  # Top 10 extensions
        if ext_data:
            chart_frame = tk.Frame(p, bg=self.BG)
            chart_frame.pack(fill="x", pady=(0, 16))

            # 创建 Figure，包含两个子图
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
            fig.patch.set_facecolor(self.BG)

# Create and show pie chart
            labels1 = [e or "(none)" for e, c, s in ext_data]
            sizes1 = [c for e, c, s in ext_data]
            colors = plt.cm.Set3(range(len(labels1)))
            ax1.pie(sizes1, labels=labels1, autopct='%1.1f%%',
                    colors=colors, startangle=90,
                    textprops={'color': self.FG})
            ax1.set_title(T("t4_pie_count"), color=self.FG, fontsize=11)
            ax1.set_facecolor(self.BG)

# Destroy previous chart
            labels2 = [e or "(none)" for e, c, s in ext_data]
            sizes2 = [s / 1024**3 for e, c, s in ext_data]  # Convert to GB
            ax2.pie(sizes2, labels=labels2, autopct='%1.1f%%',
                    colors=colors, startangle=90,
                    textprops={'color': self.FG})
            ax2.set_title(T("t4_pie_size"), color=self.FG, fontsize=11)
            ax2.set_facecolor(self.BG)

            plt.tight_layout()

            # 嵌入到?Tkinter
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x")
            plt.close(fig)  # 释放内容瓨

# ======================================================== Tree view columns helper ========================================================
        tk.Label(
            p, text=T("t4_top_dirs"),
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.BG, fg=self.YL, anchor="w"
        ).pack(anchor="w", pady=(0, 4))
        self.cat_dir_tree = self._tree(
            p, [T("t4_col_dir"), T("t4_col_files"), T("t4_col_size")], [500, 80, 100]
        )
        # 排序功能兘
        for col in (T("t4_col_files"), T("t4_col_size")):
            self.cat_dir_tree.heading(col, command=lambda c=col: self._sort_cat_dir_tree(c))
        for path, fc, b in self.db.top_dirs(30):
            self.cat_dir_tree.insert("", "end", values=(
                path[:80], "{:,}".format(fc), "{:.1f}".format(b / 1024**3)
            ))

        tk.Label(
            p, text=T("t4_ext_dist"),
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.BG, fg=self.YL, anchor="w"
        ).pack(anchor="w", pady=(12, 4))
        self.cat_ext_tree = self._tree(
            p, [T("t4_col_ext2"), T("t4_col_files"), T("t4_col_size")], [150, 100, 100]
        )
        # 排序功能兘
        for col in (T("t4_col_files"), T("t4_col_size")):
            self.cat_ext_tree.heading(col, command=lambda c=col: self._sort_cat_ext_tree(c))
        for ext, cnt, b in self.db.ext_stats()[:20]:
            self.cat_ext_tree.insert("", "end", values=(
                ext or "(none)", "{:,}".format(cnt),
                "{:.1f}".format(b / 1024**3)
            ))

# ======================================================== TAB 5: Search ========================================================
    def _tab_search(self):
        self._clear()
        if not self._ok_db():
            return
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t5_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 10))

        sr = tk.Frame(p, bg=self.BG)
        sr.pack(fill="x", pady=(0, 8))
        tk.Label(sr, text=T("t5_keyword"), bg=self.BG, fg=self.FG).pack(
            side="left"
        )
        self.sv = tk.StringVar()
        tk.Entry(
            sr, textvariable=self.sv,
            font=("Consolas", 11), bg=self.BL, fg=self.FG,
            insertbackground=self.AC, relief="flat", width=40
        ).pack(side="left", padx=8)
        tk.Button(
            sr, text=T("t5_search_btn"), command=self._do_search,
            bg=self.AC, fg=self.BG,
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=16, pady=5, cursor="hand2"
        ).pack(side="left")
        self.sr_lbl = tk.Label(
            sr, text="", bg=self.BG, fg=self.GR,
            font=("Microsoft YaHei UI", 9)
        )
        self.sr_lbl.pack(side="left", padx=10)

        self.sr_tree = self._tree(
            p, [T("t5_col_name"), T("t5_col_path"), T("t5_col_size")], [200, 600, 100]
        )
        # 排序功能兘
        for col in (T("t5_col_size"),):
            self.sr_tree.heading(col, command=lambda c=col: self._sort_sr_tree(c))
        tk.Label(
            p, text=T("t5_tip"),
            bg=self.BG, fg=self.GY,
            font=("Microsoft YaHei UI", 8), anchor="w"
        ).pack(anchor="w", pady=(4, 0))

    def _do_search(self):
        q = self.sv.get().strip()
        if not q:
            messagebox.showwarning(T("dlg_tip"), T("t5_enter_kw"))
            return
        rows = self.db.search(q)
        self.sr_lbl.config(text="{:,} results".format(len(rows)))
        for i in self.sr_tree.get_children():
            self.sr_tree.delete(i)
        for name, path, size in rows:
            self.sr_tree.insert("", "end", values=(
                name[:40], path[:90], "{:.2f}".format(size / 1024**3)
            ))
# Rebind sort events after clearing tree
        for col in (T("t5_col_size"),):
            self.sr_tree.heading(col, command=lambda c=col: self._sort_sr_tree(c))

# ======================================================== TAB 6: Cleanup ========================================================
    def _tab_cleanup(self):
        self._clear()
        if not self._ok_db():
            return
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t6_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 12))

        bx1 = self._box(p, T("t6_small"))
        r1 = tk.Frame(bx1, bg=self.BG2)
        r1.pack(fill="x")
        tk.Label(
            r1, text=T("t6_small_thresh"),
            bg=self.BG2, fg=self.FG
        ).pack(side="left")
        self.sm_sv = tk.StringVar(value="1")
        tk.Entry(
            r1, textvariable=self.sm_sv, width=6,
            bg=self.BL, fg=self.FG, relief="flat"
        ).pack(side="left", padx=5)
        tk.Button(
            r1, text=T("t6_small_scan"), command=self._scan_small,
            bg=self.AC, fg=self.BG,
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=12, pady=4, cursor="hand2"
        ).pack(side="left", padx=(8, 0))
        self.sm_lbl = tk.Label(
            r1, text="", bg=self.BG2, fg=self.YL,
            font=("Microsoft YaHei UI", 9)
        )
        self.sm_lbl.pack(side="left", padx=10)

        self.sm_tree = self._tree(
            p, [T("t6_col_name"), T("t6_col_path"), T("t6_col_size")], [200, 600, 100]
        )
        # 排序功能兘
        for col in (T("t6_col_size"),):
            self.sm_tree.heading(col, command=lambda c=col: self._sort_sm_tree(c))
        r2 = tk.Frame(p, bg=self.BG)
        r2.pack(fill="x", pady=(6, 0))
        tk.Button(
            r2, text=T("t6_small_del"),
            command=self._del_small,
            bg=self.RD, fg="white",
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=14, pady=6, cursor="hand2"
        ).pack(side="left")

    def _scan_small(self):
        try:
            mm = int(self.sm_sv.get())
        except Exception:
            mm = 1
        rows = self.db.small_files(mm)
        tot = sum(r[2] for r in rows)
        self.sm_lbl.config(
            text="{:,} files, {:.1f} MB total".format(
                len(rows), tot / 1024**2
            )
        )
        for i in self.sm_tree.get_children():
            self.sm_tree.delete(i)
        for name, path, size in rows[:200]:
            self.sm_tree.insert("", "end", values=(
                name[:40], path[:90], "{:.2f}".format(size / 1024**2)
            ))

    def _del_small(self):
        items = self.sm_tree.get_children()
        if not items:
            messagebox.showwarning(T("dlg_tip"), T("t6_small_empty"))
            return
        if not messagebox.askyesno(
            T("dlg_tip"),
            T("t6_del_confirm").format(len(items))
        ):
            return
        dcnt, ecnt = 0, 0
        for iid in items:
            vals = self.sm_tree.item(iid)["values"]
            fp = vals[1]
            try:
                if os.path.exists(fp):
                    os.remove(fp)
                    dcnt += 1
                else:
                    ecnt += 1
            except Exception:
                ecnt += 1
        messagebox.showinfo(
            T("dlg_tip"),
            T("t6_del_done").format(dcnt, ecnt)
        )
        self._log("[CLEANUP] {:,} small files deleted".format(dcnt))
        self._scan_small()

# ======================================================== TAB 7: History ========================================================
    def _tab_history(self):
        self._clear()
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=16)
        tk.Label(
            p, text=T("t7_title"),
            font=("Microsoft YaHei UI", 15, "bold"), bg=self.BG, fg=self.AC
        ).pack(anchor="w", pady=(0, 12))

# ======================================================== Disk summary ========================================================
        tk.Label(
            p, text=T("t7_disk_sum"),
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.BG, fg=self.YL, anchor="w"
        ).pack(anchor="w", pady=(0, 4))
        self.hist_disk_tree = self._tree(
            p, [T("t7_col_drive"), T("t7_col_snapshot"), T("t7_col_last"), T("t7_col_files"), T("t7_col_dirs"), T("t7_col_size2"), T("t7_col_status")],
            [60, 380, 160, 80, 80, 90, 80]
        )
        # 排序功能兘
        sort_cols_disk = (T("t7_col_files"), T("t7_col_dirs"), T("t7_col_size2"))
        for col in sort_cols_disk:
            self.hist_disk_tree.heading(col, command=lambda c=col: self._sort_hist_disk_tree(c))
        cu = self.meta_conn.cursor()
        rows = cu.execute(
            "SELECT drive_letter, last_snapshot_path, last_scan_time, "
            "file_count, dir_count, total_bytes FROM drives "
            "ORDER BY last_scan_time DESC"
        ).fetchall()
        for drive, snap_path, scan_t, fc, dc, tb in rows:
            exists = os.path.exists(snap_path)
            status = "OK" if exists else "MISSING"
            self.hist_disk_tree.insert("", "end", iid="disk_" + drive, values=(
                drive + ":\\",
                snap_path,
                scan_t or "-",
                fc or 0,
                dc or 0,
                "{:.1f}".format((tb or 0) / 1024**3),
                status
            ))

        # Buttons below disk tree
        btn_frame = tk.Frame(p, bg=self.BG)
        btn_frame.pack(fill="x", pady=(4, 12))
        tk.Button(
            btn_frame, text=T("t7_load"),
            command=lambda: self._history_load(self.hist_disk_tree),
            bg=self.AC, fg=self.BG,
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=14, pady=5, cursor="hand2"
        ).pack(side="left")
        tk.Button(
            btn_frame, text=T("t7_del"),
            command=lambda: self._history_delete(self.hist_disk_tree),
            bg=self.RD, fg="white",
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=14, pady=5, cursor="hand2"
        ).pack(side="left", padx=(8, 0))
        tk.Button(
            btn_frame, text=T("t6_small"),
            command=self._tab_history,
            bg=self.GY, fg="white",
            font=("Microsoft YaHei UI", 9),
            relief="flat", padx=10, pady=5, cursor="hand2"
        ).pack(side="left", padx=(8, 0))

# ======================================================== Scan history ========================================================
        tk.Label(
            p, text=T("t7_history"),
            font=("Microsoft YaHei UI", 11, "bold"),
            bg=self.BG, fg=self.YL, anchor="w"
        ).pack(anchor="w", pady=(4, 4))
        self.hist_scan_tree = self._tree(
            p, [T("t7_col_no"), T("t7_col_drive"), T("t7_col_root"), T("t7_col_time"), T("t7_col_files"), T("t7_col_size2")],
            [40, 50, 300, 160, 80, 90]
        )
        # 排序功能兘
        sort_cols_scan = (T("t7_col_files"), T("t7_col_size2"))
        for col in sort_cols_scan:
            self.hist_scan_tree.heading(col, command=lambda c=col: self._sort_hist_scan_tree(c))
        hrows = cu.execute(
            "SELECT id, drive_letter, root_path, scan_time, "
            "file_count, total_bytes FROM scans "
            "ORDER BY scan_time DESC LIMIT 50"
        ).fetchall()
        for sid, drv, rp, st, fc, tb in hrows:
            self.hist_scan_tree.insert("", "end", values=(
                sid, drv + ":\\", (rp or "")[:80],
                st or "-", fc or 0,
                "{:.1f}".format((tb or 0) / 1024**3)
            ))

    def _history_load(self, tree):
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith("disk_"):
            return
        drive = iid[5:]
        cu = self.meta_conn.cursor()
        row = cu.execute(
            "SELECT last_snapshot_path FROM drives WHERE drive_letter=?", (drive,)
        ).fetchone()
        snap = row[0] if row else None
        if not snap or not os.path.exists(snap):
            messagebox.showwarning(T("dlg_tip"), "Snapshot not found: " + (snap if snap else "?"))
            return
        try:
            if self.db:
                self.db.close()
            self.db = DB(snap)
            self.db.connect()
            self.current_drive = drive
            self._refresh()
            self._st("[" + drive + "] " + T("dlg_loaded") + snap)
        except Exception as e:
            messagebox.showerror(T("dlg_err"), str(e))

    def _history_delete(self, tree):
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith("disk_"):
            return
        drive = iid[5:]
        cu = self.meta_conn.cursor()
        row = cu.execute(
            "SELECT last_snapshot_path FROM drives WHERE drive_letter=?", (drive,)
        ).fetchone()
        if not row:
            return
        snap = row[0]
        if not messagebox.askyesno(
            T("dlg_tip"),
            T("t7_del_confirm").format(drive=drive, path=snap)
        ):
            return
        # Close if currently loaded
        if self.current_drive == drive and self.db:
            self.db.close()
            self.db = None
            self.current_drive = None
            self._refresh()
        # Delete ALL snapshot files for this drive
        snap_rows = cu.execute(
            "SELECT snapshot_path FROM scans WHERE drive_letter=?", (drive,)
        ).fetchall()
        deleted = []
        for (sp,) in snap_rows:
            if sp and os.path.exists(sp):
                try:
                    os.remove(sp)
                    deleted.append(sp)
                except Exception:
                    pass
        self.meta_conn.execute("DELETE FROM scans WHERE drive_letter=?", (drive,))
        self.meta_conn.execute("DELETE FROM drives WHERE drive_letter=?", (drive,))
        self.meta_conn.commit()
        msg = "; ".join(deleted[:5]) + (" ..." if len(deleted) > 5 else "")
        messagebox.showinfo(T("dlg_tip"), T("t7_del_done").format(path=msg))
        self._tab_history()

# ======================================================== TAB 8: Compare ========================================================
    # TAB 8: Scan History Compare
# ======================================================== TAB 8: Compare ========================================================
    def _tab_compare(self):
        self._clear()
        p = tk.Frame(self.content, bg=self.BG)
        p.pack(fill="both", expand=True, padx=20, pady=12)

        # ── 标题行 ──────────────────────────────────────────────────────────
        hdr = tk.Frame(p, bg=self.BG)
        hdr.pack(fill="x", pady=(0, 2))
        tk.Label(
            hdr, text=T("t8_title"),
            font=("Microsoft YaHei UI", 15, "bold"),
            bg=self.BG, fg=self.AC, anchor="w"
        ).pack(side="left")
        tk.Label(
            hdr, text=T("t8_desc"),
            font=("Microsoft YaHei UI", 9),
            bg=self.BG, fg=self.GY, anchor="w"
        ).pack(side="left", padx=(12, 0))

        # ── 磁盘选择行 ───────────────────────────────────────────────────────
        drive_row = tk.Frame(p, bg=self.BG)
        drive_row.pack(fill="x", pady=(6, 0))
        tk.Label(drive_row, text=T("t8_drive"),
                 font=("Microsoft YaHei UI", 9), bg=self.BG, fg=self.FG
                 ).pack(side="left")
        self.cmp_drive_var = tk.StringVar()
        cmp_drive_combo = ttk.Combobox(
            drive_row, textvariable=self.cmp_drive_var,
            state="readonly", font=("Microsoft YaHei UI", 9), width=18
        )
        cmp_drive_combo.pack(side="left", padx=(4, 0))
        cmp_drive_combo.bind("<<ComboboxSelected>>",
                             lambda e: self._on_cmp_drive_changed())
        self.cmp_drive_combo = cmp_drive_combo

        # ════════════════════════════════════════════════════════════════════
        # 上半区（30%）：左列表 40% | 中间按钮 20% | 右列表 40%
        # ════════════════════════════════════════════════════════════════════
        top_pane = tk.Frame(p, bg=self.BG)
        top_pane.pack(fill="both", expand=False, pady=(10, 0))
        # 固定高度约 30% — 用 place 不合适，改用 pack + height 限制
        # 用三列 grid 实现 40/20/40 比例
        top_pane.columnconfigure(0, weight=40)
        top_pane.columnconfigure(1, weight=20)
        top_pane.columnconfigure(2, weight=40)
        top_pane.rowconfigure(0, weight=1)

        # ── 左列：扫描 A ─────────────────────────────────────────────────
        left_col = tk.Frame(top_pane, bg=self.BG2, padx=8, pady=6)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        tk.Label(left_col, text=T("t8_scan_a"),
                 font=("Microsoft YaHei UI", 10, "bold"),
                 bg=self.BG2, fg=self.YL, anchor="w"
                 ).pack(anchor="w", pady=(0, 4))
        self.cmp_a_var = tk.StringVar()
        cmp_a_lb_frame = tk.Frame(left_col, bg=self.BG2)
        cmp_a_lb_frame.pack(fill="both", expand=True)
        cmp_a_sb = ttk.Scrollbar(cmp_a_lb_frame, orient="vertical")
        cmp_a_sb.pack(side="right", fill="y")
        self.cmp_a_listbox = tk.Listbox(
            cmp_a_lb_frame, bg=self.BL, fg=self.FG,
            font=("Microsoft YaHei UI", 9),
            selectbackground=self.YL, selectforeground=self.BG,
            relief="flat", height=7,
            yscrollcommand=cmp_a_sb.set,
            exportselection=False
        )
        self.cmp_a_listbox.pack(side="left", fill="both", expand=True)
        cmp_a_sb.config(command=self.cmp_a_listbox.yview)
        self.cmp_a_listbox.bind("<<ListboxSelect>>",
                                lambda e: self._on_cmp_a_select())
        # A 列选中详情标签
        self.cmp_a_info_lbl = tk.Label(
            left_col, text="", bg=self.BG2, fg=self.GY,
            font=("Microsoft YaHei UI", 8), anchor="w", justify="left"
        )
        self.cmp_a_info_lbl.pack(fill="x", pady=(4, 0))

        # ── 中间列：对比按钮 ─────────────────────────────────────────────
        mid_col = tk.Frame(top_pane, bg=self.BG)
        mid_col.grid(row=0, column=1, sticky="nsew", padx=4)
        # 垂直居中
        mid_inner = tk.Frame(mid_col, bg=self.BG)
        mid_inner.place(relx=0.5, rely=0.5, anchor="center")
        self.cmp_btn = tk.Button(
            mid_inner, text=T("t8_compare_btn"),
            command=self._do_compare,
            bg=self.AC, fg=self.BG,
            font=("Microsoft YaHei UI", 10, "bold"),
            relief="flat", padx=12, pady=8, cursor="hand2",
            wraplength=80
        )
        self.cmp_btn.pack()
        # 选中提示标签
        self.cmp_sel_lbl = tk.Label(
            mid_inner, text="", bg=self.BG, fg=self.GY,
            font=("Microsoft YaHei UI", 8), wraplength=90, justify="center"
        )
        self.cmp_sel_lbl.pack(pady=(6, 0))

        # ── 右列：扫描 B ─────────────────────────────────────────────────
        right_col = tk.Frame(top_pane, bg=self.BG2, padx=8, pady=6)
        right_col.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        tk.Label(right_col, text=T("t8_scan_b"),
                 font=("Microsoft YaHei UI", 10, "bold"),
                 bg=self.BG2, fg=self.AC, anchor="w"
                 ).pack(anchor="w", pady=(0, 4))
        self.cmp_b_var = tk.StringVar()
        cmp_b_lb_frame = tk.Frame(right_col, bg=self.BG2)
        cmp_b_lb_frame.pack(fill="both", expand=True)
        cmp_b_sb = ttk.Scrollbar(cmp_b_lb_frame, orient="vertical")
        cmp_b_sb.pack(side="right", fill="y")
        self.cmp_b_listbox = tk.Listbox(
            cmp_b_lb_frame, bg=self.BL, fg=self.FG,
            font=("Microsoft YaHei UI", 9),
            selectbackground=self.AC, selectforeground=self.BG,
            relief="flat", height=7,
            yscrollcommand=cmp_b_sb.set,
            exportselection=False
        )
        self.cmp_b_listbox.pack(side="left", fill="both", expand=True)
        cmp_b_sb.config(command=self.cmp_b_listbox.yview)
        self.cmp_b_listbox.bind("<<ListboxSelect>>",
                                lambda e: self._on_cmp_b_select())
        # B 列选中详情标签
        self.cmp_b_info_lbl = tk.Label(
            right_col, text="", bg=self.BG2, fg=self.GY,
            font=("Microsoft YaHei UI", 8), anchor="w", justify="left"
        )
        self.cmp_b_info_lbl.pack(fill="x", pady=(4, 0))

        # ════════════════════════════════════════════════════════════════════
        # 下半区（70%）：统计摘要 + 结果列表
        # ════════════════════════════════════════════════════════════════════
        sep = tk.Frame(p, bg=self.BL, height=2)
        sep.pack(fill="x", pady=(10, 0))

        bot_pane = tk.Frame(p, bg=self.BG)
        bot_pane.pack(fill="both", expand=True, pady=(6, 0))

        # 统计摘要行
        res_header = tk.Frame(bot_pane, bg=self.BG)
        res_header.pack(fill="x", pady=(0, 6))
        self.cmp_added_lbl = tk.Label(
            res_header, text="", font=("Microsoft YaHei UI", 9),
            bg=self.BG, fg="#a6e3a1", anchor="w"
        )
        self.cmp_added_lbl.pack(side="left", padx=(0, 16))
        self.cmp_deleted_lbl = tk.Label(
            res_header, text="", font=("Microsoft YaHei UI", 9),
            bg=self.BG, fg=self.RD, anchor="w"
        )
        self.cmp_deleted_lbl.pack(side="left", padx=(0, 16))
        self.cmp_modified_lbl = tk.Label(
            res_header, text="", font=("Microsoft YaHei UI", 9),
            bg=self.BG, fg=self.YL, anchor="w"
        )
        self.cmp_modified_lbl.pack(side="left", padx=(0, 16))
        self.cmp_same_lbl = tk.Label(
            res_header, text="", font=("Microsoft YaHei UI", 9),
            bg=self.BG, fg=self.GY, anchor="w"
        )
        self.cmp_same_lbl.pack(side="left")

        # 结果树
        self.cmp_tree = self._tree(
            bot_pane,
            [T("t8_col_change"), T("t8_col_file"), T("t8_col_path"), T("t8_col_size")],
            [90, 200, 420, 90]
        )
        sort_cols = [T("t8_col_change"), T("t8_col_file"), T("t8_col_size")]
        for col in sort_cols:
            self.cmp_tree.heading(col, command=lambda c=col: self._sort_cmp_tree(c))

        # 内部状态
        self._cmp_scan_items = []   # list of (label, snapshot_path)

        # Pre-populate drives
        self._load_cmp_drives()

    def _load_cmp_drives(self):
        try:
            print(f"[DEBUG] _load_cmp_drives called, META_DB={META_DB}")
            cu = self.meta_conn.cursor()
            try:
                rows = cu.execute(
                    "SELECT DISTINCT drive_letter FROM scans ORDER BY drive_letter"
                ).fetchall()
                print(f"[DEBUG] Query 'scans' returned: {rows}")
            except sqlite3.OperationalError as e:
                print(f"[DEBUG] 'scans' query failed: {e}")
                rows = []
            if not rows:
                try:
                    rows = cu.execute(
                        "SELECT drive_letter FROM drives ORDER BY drive_letter"
                    ).fetchall()
                    print(f"[DEBUG] Query 'drives' returned: {rows}")
                except sqlite3.OperationalError as e:
                    print(f"[DEBUG] 'drives' query failed: {e}")
                    rows = []
            drive_list = [r[0] + ":\\" for r in rows if r[0]]
            print(f"[DEBUG] drive_list: {drive_list}")
            if hasattr(self, 'cmp_drive_combo'):
                print(f"[DEBUG] Setting combo values...")
                self.cmp_drive_combo["values"] = drive_list
                if drive_list:
                    self.cmp_drive_combo.set(drive_list[0])
                    self._on_cmp_drive_changed()
            else:
                print(f"[DEBUG] cmp_drive_combo not found!")
        except Exception as e:
            print("[ERROR] _load_cmp_drives:", e)

    def _on_cmp_drive_changed(self):
        drive = self.cmp_drive_var.get().rstrip(":\\")
        if not drive:
            return
        try:
            cu = self.meta_conn.cursor()
            rows = cu.execute(
                "SELECT id, scan_time, file_count, snapshot_path, root_path, total_bytes FROM scans "
                "WHERE drive_letter=? ORDER BY scan_time DESC",
                (drive,)
            ).fetchall()
            self._cmp_scan_items = []   # [(label, snapshot_path, scan_time, mtime, file_count, total_bytes, db_name), ...]
            items_labels = []
            for sid, st, fc, sp, rp, tb in rows:
                # 尝试找到实际存在的 DB 文件
                actual_path = self._find_snapshot_db(sp, drive, st)
                if not actual_path:
                    continue
                # 获取 DB 文件的修改时间
                try:
                    db_mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(actual_path)))
                except:
                    db_mtime = "?"
                # DB 文件名
                db_name = os.path.basename(actual_path)
                # 大小显示
                try:
                    size_gb = tb / 1024**3 if tb else 0
                    size_str = "{:.1f} GB".format(size_gb)
                except:
                    size_str = "?"
                # 列表标签：扫描时间 | DB文件名 | 文件数 | 大小 | DB修改时间
                label = "{} | {} | {:,} files | {} | DB:{}".format(
                    st, size_str, fc or 0, db_mtime, db_name
                )
                items_labels.append(label)
                self._cmp_scan_items.append((label, actual_path, st, db_mtime, fc or 0, tb or 0, db_name))
            # 填充两个 Listbox
            for lb in (getattr(self, 'cmp_a_listbox', None),
                       getattr(self, 'cmp_b_listbox', None)):
                if lb:
                    lb.delete(0, "end")
                    for lbl in items_labels:
                        lb.insert("end", lbl)
            self._update_cmp_sel_label()
        except Exception as e:
            print("[ERROR] _on_cmp_drive_changed:", e)

    def _find_snapshot_db(self, snapshot_path, drive_letter, scan_time):
        """Find actual snapshot DB file, with fallback logic.
        
        1. Try snapshot_path directly if it exists
        2. Try DB_DIR/{timestamp}_{drive}_{machine}.db pattern
        3. Try any *_{drive}_{machine}.db file in DB_DIR
        """
        # 1. Direct path
        if snapshot_path and os.path.exists(snapshot_path):
            return snapshot_path
        
        # 2. Try new naming pattern in DB_DIR
        # scan_time format: '2026-04-19 00:09:33' -> '20260419T000933'
        if scan_time:
            try:
                ts = scan_time.replace('-', '').replace(' ', 'T').replace(':', '')[:15]
                expected_path = os.path.join(
                    DB_DIR, 
                    "{}_{}_{}.db".format(ts, drive_letter.upper(), MACHINE_NAME)
                )
                if os.path.exists(expected_path):
                    return expected_path
            except:
                pass
        
        # 3. Fallback: find any matching DB in DB_DIR
        import glob
        pattern = os.path.join(DB_DIR, "*_{}_{}.db".format(drive_letter.upper(), MACHINE_NAME))
        matches = glob.glob(pattern)
        if matches:
            # Return the most recently modified one
            return max(matches, key=os.path.getmtime)
        
        return None

    def _on_cmp_a_select(self):
        """左侧列表选中：在列表下方显示选中的数据库信息"""
        lb = getattr(self, 'cmp_a_listbox', None)
        if not lb:
            return
        sel = lb.curselection()
        items = getattr(self, '_cmp_scan_items', [])
        lbl = getattr(self, 'cmp_a_info_lbl', None)
        if not lbl:
            return
        if sel and sel[0] < len(items):
            info = items[sel[0]]
            # info: (label, db_path, scan_time, db_mtime, file_count, total_bytes, db_name)
            try:
                gb = info[5] / 1024**3 if info[5] else 0
            except:
                gb = 0
            text = ("🕐 {}  |  📄 {:,} files  |  💾 {:.1f} GB\n"
                    "📁 {}  |  🗓 DB: {}").format(
                info[2], info[4], gb, info[6], info[3]
            )
            lbl.config(text=text, fg=self.YL)
        else:
            lbl.config(text=T("t8_no_sel"), fg=self.GY)
        self._update_cmp_sel_label()

    def _on_cmp_b_select(self):
        """右侧列表选中：在列表下方显示选中的数据库信息"""
        lb = getattr(self, 'cmp_b_listbox', None)
        if not lb:
            return
        sel = lb.curselection()
        items = getattr(self, '_cmp_scan_items', [])
        lbl = getattr(self, 'cmp_b_info_lbl', None)
        if not lbl:
            return
        if sel and sel[0] < len(items):
            info = items[sel[0]]
            try:
                gb = info[5] / 1024**3 if info[5] else 0
            except:
                gb = 0
            text = ("🕐 {}  |  📄 {:,} files  |  💾 {:.1f} GB\n"
                    "📁 {}  |  🗓 DB: {}").format(
                info[2], info[4], gb, info[6], info[3]
            )
            lbl.config(text=text, fg=self.AC)
        else:
            lbl.config(text=T("t8_no_sel"), fg=self.GY)
        self._update_cmp_sel_label()

    def _update_cmp_sel_label(self):
        """保持中间对比按钮下方提示（简化版）"""
        a_lb = getattr(self, 'cmp_a_listbox', None)
        b_lb = getattr(self, 'cmp_b_listbox', None)
        a_done = bool(a_lb and a_lb.curselection())
        b_done = bool(b_lb and b_lb.curselection())
        if a_done and b_done:
            text = "✅ {}".format(T("t8_ready"))
        else:
            text = T("t8_pick")
        if hasattr(self, 'cmp_sel_lbl'):
            self.cmp_sel_lbl.config(text=text)

    def _do_compare(self):
        a_lb = getattr(self, 'cmp_a_listbox', None)
        b_lb = getattr(self, 'cmp_b_listbox', None)
        a_sel = a_lb.curselection() if a_lb else ()
        b_sel = b_lb.curselection() if b_lb else ()
        if not a_sel or not b_sel:
            messagebox.showwarning(T("dlg_tip"), T("t8_need_two"))
            return
        a_idx = a_sel[0]
        b_idx = b_sel[0]
        items = getattr(self, '_cmp_scan_items', [])
        if a_idx >= len(items) or b_idx >= len(items):
            messagebox.showerror(T("dlg_err"), "Index out of range")
            return
        a_info = items[a_idx]
        b_info = items[b_idx]
        a_label, a_snap = a_info[0], a_info[1]
        b_label, b_snap = b_info[0], b_info[1]
        if a_label == b_label:
            messagebox.showwarning(T("dlg_tip"), T("t8_same_db"))
            return
        if not a_snap or not b_snap or not os.path.exists(a_snap) \
                or not os.path.exists(b_snap):
            messagebox.showerror(T("dlg_err"),
                "Snapshot DB not found")
            return

        try:
            old_db = DB(a_snap)
            old_db.connect()
            new_db = DB(b_snap)
            new_db.connect()
            result = self._compare_two_snapshots(old_db, new_db)
            old_db.close()
            new_db.close()
        except Exception as e:
            messagebox.showerror(T("dlg_err"), str(e))
            return

        # Display results
        for item in self.cmp_tree.get_children():
            self.cmp_tree.delete(item)

        added_sz = 0
        deleted_sz = 0
        modified_sz = 0
        same_cnt = 0

        change_color_map = {
            T("t8_new"): "#a6e3a1",
            T("t8_new_dir"): "#94e2d5",  # Teal for new folders
            T("t8_removed"): self.RD,
            T("t8_del_dir"): "#f5c2e7",   # Pink for deleted folders
            T("t8_changed"): self.YL,
            T("t8_same_size"): self.GY,
        }

        added_dirs = 0
        deleted_dirs = 0

        for row in result:
            kind, name, path, size_b, is_dir = row
            color = change_color_map.get(kind, self.FG)
            # Show folder indicator in name
            display_name = "[📁] " + name if is_dir else name
            self.cmp_tree.insert("", "end", values=(
                kind, display_name, path[:120], "{:.2f}".format(size_b / 1024**2) if not is_dir else "-"
            ), tags=(color,))
            if kind == T("t8_new"):
                added_sz += size_b
            elif kind == T("t8_new_dir"):
                added_dirs += 1
            elif kind == T("t8_removed"):
                deleted_sz += size_b
            elif kind == T("t8_del_dir"):
                deleted_dirs += 1
            elif kind == T("t8_changed"):
                modified_sz += size_b
            else:
                same_cnt += 1

        self.cmp_tree.tag_configure("#a6e3a1", foreground="#a6e3a1")
        self.cmp_tree.tag_configure("#94e2d5", foreground="#94e2d5")
        self.cmp_tree.tag_configure(self.RD, foreground=self.RD)
        self.cmp_tree.tag_configure("#f5c2e7", foreground="#f5c2e7")
        self.cmp_tree.tag_configure(self.YL, foreground=self.YL)
        self.cmp_tree.tag_configure(self.GY, foreground=self.GY)

        # Update stats with folder counts
        self.cmp_added_lbl.config(
            text=T("t8_added") + ": {} ({:.1f} MB) | {} {}".format(
                sum(1 for r in result if r[0] == T("t8_new")), added_sz / 1024**2,
                added_dirs, T("t8_new_dir")))
        self.cmp_deleted_lbl.config(
            text=T("t8_deleted") + ": {} ({:.1f} MB) | {} {}".format(
                sum(1 for r in result if r[0] == T("t8_removed")), deleted_sz / 1024**2,
                deleted_dirs, T("t8_del_dir")))
        self.cmp_modified_lbl.config(
            text=T("t8_modified") + ": {}".format(
                sum(1 for r in result if r[0] == T("t8_changed"))))
        self.cmp_same_lbl.config(
            text=T("t8_same") + ": {}".format(same_cnt))

    def _compare_two_snapshots(self, old_db, new_db):
        """Compare two snapshot DBs and return list of (change_type, name, path, size, is_dir)."""
        old_cu = old_db.conn.cursor()
        new_cu = new_db.conn.cursor()

        # Load old entries: path -> (name, size, mtime, hash, is_dir)
        old_entries = {}
        old_cu.execute(
            "SELECT name, path, size_bytes, mtime, content_hash, is_dir FROM dir_entries"
        )
        for name, path, size, mtime, hsh, is_dir in old_cu.fetchall():
            old_entries[path] = (name, size, mtime, hsh, is_dir)

        # Load new entries: path -> (name, size, mtime, hash, is_dir)
        new_entries = {}
        new_cu.execute(
            "SELECT name, path, size_bytes, mtime, content_hash, is_dir FROM dir_entries"
        )
        for name, path, size, mtime, hsh, is_dir in new_cu.fetchall():
            new_entries[path] = (name, size, mtime, hsh, is_dir)

        result = []

        # Find new and modified
        for path, (name, size, mtime, hsh, is_dir) in new_entries.items():
            if path not in old_entries:
                # New entry (file or folder)
                if is_dir:
                    result.append((T("t8_new_dir"), name, path, size, True))
                else:
                    result.append((T("t8_new"), name, path, size, False))
            else:
                old_name, old_size, old_mtime, old_hsh, old_is_dir = old_entries[path]
                # Only check for changes on files (folders don't have content changes)
                if not is_dir:
                    changed = False
                    # Size changed
                    if old_size != size:
                        changed = True
                    # Content hash changed (if available)
                    elif old_hsh and hsh and old_hsh != hsh:
                        changed = True
                    if changed:
                        result.append((T("t8_changed"), name, path, size, False))

        # Find deleted
        for path, (name, size, mtime, hsh, is_dir) in old_entries.items():
            if path not in new_entries:
                # Deleted entry (file or folder)
                if is_dir:
                    result.append((T("t8_del_dir"), name, path, size, True))
                else:
                    result.append((T("t8_removed"), name, path, size, False))

        return result

    def _sort_cmp_tree(self, col):
        items = [(self.cmp_tree.set(k, col), k) for k in self.cmp_tree.get_children("")]
        if col == T("t8_col_change"):
            # Sort order: new > removed > changed > same
            order = {T("t8_new"): 0, T("t8_removed"): 1, T("t8_changed"): 2, T("t8_same_size"): 3}
            items.sort(key=lambda x: order.get(x[0], 99))
        elif col == T("t8_col_size"):
            items.sort(key=lambda x: float(x[0].replace(",", "")), reverse=True)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=False)
        for index, (_, k) in enumerate(items):
            self.cmp_tree.move(k, "", index)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
