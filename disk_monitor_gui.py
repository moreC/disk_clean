#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import hashlib
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
from pathlib import Path


class DirCache:
    """目录大小缓存管理器"""
    
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.dir_cache_file = os.path.join(cache_dir, 'dir_cache.json')
        self.dir_cache = {}
        self._load_cache()
        
    def _load_cache(self):
        """加载目录缓存"""
        if os.path.exists(self.dir_cache_file):
            try:
                with open(self.dir_cache_file, 'r', encoding='utf-8') as f:
                    self.dir_cache = json.load(f)
            except:
                self.dir_cache = {}
                
    def save_cache(self):
        """保存目录缓存"""
        try:
            with open(self.dir_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.dir_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存目录缓存失败: {e}")
            
    def get_dir_signature(self, dir_path):
        """获取目录签名（用于检测变化）"""
        try:
            stat = os.stat(dir_path)
            return f"{stat.st_mtime}_{stat.st_ino}"
        except:
            return None
            
    def is_cached(self, dir_path):
        """检查目录是否在缓存中"""
        if dir_path not in self.dir_cache:
            return False, None
            
        cached_data = self.dir_cache[dir_path]
        current_sig = self.get_dir_signature(dir_path)
        
        if cached_data.get('signature') == current_sig:
            return True, cached_data
        return False, None
        
    def update_cache(self, dir_path, size, file_count, subdirs=None):
        """更新目录缓存"""
        sig = self.get_dir_signature(dir_path)
        if sig:
            self.dir_cache[dir_path] = {
                'signature': sig,
                'size': size,
                'file_count': file_count,
                'subdirs': subdirs or {},
                'cached_time': datetime.now().isoformat()
            }
            
    def clear_cache(self):
        """清空目录缓存"""
        self.dir_cache = {}
        self.save_cache()


class ScanCache:
    """扫描缓存管理器"""
    
    def __init__(self, cache_dir):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'scan_cache.json')
        self.cache_index_file = os.path.join(cache_dir, 'cache_index.json')
        self.cache = {}
        self.cache_index = {}
        self._load_cache()
        
    def _load_cache(self):
        """加载缓存"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
                
        if os.path.exists(self.cache_index_file):
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    self.cache_index = json.load(f)
            except:
                self.cache_index = {}
                
    def save_cache(self):
        """保存缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存缓存失败: {e}")
            
    def get_file_signature(self, file_path):
        """获取文件签名（大小+修改时间）"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'signature': f"{stat.st_size}_{stat.st_mtime}"
            }
        except:
            return None
            
    def is_cached(self, file_path):
        """检查文件是否在缓存中且未修改"""
        current_sig = self.get_file_signature(file_path)
        if not current_sig:
            return False, None
            
        cached_sig = self.cache_index.get(file_path)
        if not cached_sig:
            return False, None
            
        if cached_sig.get('signature') == current_sig['signature']:
            return True, self.cache.get(file_path)
            
        return False, None
        
    def update_cache(self, file_path, file_info):
        """更新缓存"""
        sig = self.get_file_signature(file_path)
        if sig:
            self.cache_index[file_path] = sig
            self.cache[file_path] = file_info
            
    def clear_cache(self):
        """清空缓存"""
        self.cache = {}
        self.cache_index = {}
        self.save_cache()
        
    def get_cache_stats(self):
        """获取缓存统计"""
        return {
            'cached_files': len(self.cache),
            'cache_size': len(json.dumps(self.cache).encode('utf-8'))
        }


class DiskMonitorGUI:
    """C盘大文件监控工具 - 带缓存功能的GUI版本"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("C盘大文件监控工具 - 智能缓存版")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 700)
        
        # 配置参数
        self.min_size_mb = 10
        self.scanning = False
        self.large_files = []
        self.useless_files = []
        self.scanned_count = 0
        self.cached_count = 0
        
        # 排除目录
        self.exclude_dirs = [
            'C:\\Windows',
            'C:\\$Recycle.Bin',
            'C:\\System Volume Information',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            'C:\\ProgramData'
        ]
        
        # 无用文件扩展名
        self.useless_extensions = {
            '.tmp', '.temp', '.log', '.bak', '.old', '.swp', '.swo',
            '.crdownload', '.part', '.tmp1', '.tmp2', '.dmp', '.err',
            '.cache', '.db-journal', '.sqlite-journal'
        }
        
        # 数据目录
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 初始化缓存
        self.cache = ScanCache(self.data_dir)
        self.dir_cache = DirCache(self.data_dir)
        
        # 目录统计
        self.dir_scanning = False
        self.dir_tree_data = {}
        
        self._setup_ui()
        self._load_last_scan()
        
    def _setup_ui(self):
        """设置UI界面"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # 最小文件大小设置
        ttk.Label(control_frame, text="最小文件大小(MB):").pack(side='left', padx=5)
        self.size_var = tk.StringVar(value="10")
        size_entry = ttk.Entry(control_frame, textvariable=self.size_var, width=10)
        size_entry.pack(side='left', padx=5)
        
        # 扫描按钮
        self.scan_btn = ttk.Button(
            control_frame, 
            text="开始扫描", 
            command=self._start_scan
        )
        self.scan_btn.pack(side='left', padx=20)
        
        # 快速扫描按钮（使用缓存）
        self.quick_scan_btn = ttk.Button(
            control_frame,
            text="快速扫描(使用缓存)",
            command=self._start_quick_scan
        )
        self.quick_scan_btn.pack(side='left', padx=5)
        
        # 停止按钮
        self.stop_btn = ttk.Button(
            control_frame, 
            text="停止扫描", 
            command=self._stop_scan,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=5)
        
        # 删除选中按钮
        self.delete_btn = ttk.Button(
            control_frame,
            text="删除选中文件",
            command=self._delete_selected,
            state='disabled'
        )
        self.delete_btn.pack(side='left', padx=20)
        
        # 缓存管理按钮
        ttk.Button(
            control_frame,
            text="清空缓存",
            command=self._clear_cache
        ).pack(side='right', padx=5)
        
        ttk.Button(
            control_frame,
            text="查看缓存状态",
            command=self._show_cache_status
        ).pack(side='right', padx=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            self.root, 
            textvariable=self.status_var, 
            relief='sunken',
            anchor='w'
        )
        status_bar.pack(side='bottom', fill='x', padx=5, pady=2)
        
        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.root,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(side='bottom', fill='x', padx=5, pady=2)
        
        # 创建Notebook（选项卡）
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 大文件选项卡
        self.large_files_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.large_files_frame, text='大文件列表')
        self._setup_large_files_tab()
        
        # 无用文件选项卡
        self.useless_files_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.useless_files_frame, text='可疑无用文件')
        self._setup_useless_files_tab()
        
        # 统计信息选项卡
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='统计信息')
        self._setup_stats_tab()
        
        # 缓存信息选项卡
        self.cache_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.cache_frame, text='缓存管理')
        self._setup_cache_tab()
        
        # 目录统计选项卡
        self.dir_stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.dir_stats_frame, text='目录统计')
        self._setup_dir_stats_tab()
        
    def _setup_large_files_tab(self):
        """设置大文件列表选项卡"""
        # 工具栏
        toolbar = ttk.Frame(self.large_files_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(toolbar, text="排序:").pack(side='left', padx=5)
        self.sort_var = tk.StringVar(value="size_desc")
        ttk.Radiobutton(
            toolbar, text="大小(大→小)", 
            variable=self.sort_var, value="size_desc",
            command=lambda: self._sort_files('large')
        ).pack(side='left', padx=5)
        ttk.Radiobutton(
            toolbar, text="修改时间(新→旧)", 
            variable=self.sort_var, value="time_desc",
            command=lambda: self._sort_files('large')
        ).pack(side='left', padx=5)
        
        # 搜索框
        ttk.Label(toolbar, text="搜索:").pack(side='left', padx=(30, 5))
        self.search_var = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.search_var, width=30).pack(side='left', padx=5)
        ttk.Button(toolbar, text="搜索", command=lambda: self._search_files('large')).pack(side='left', padx=5)
        
        # Treeview
        columns = ('select', 'path', 'size', 'modified', 'type', 'source')
        self.large_tree = ttk.Treeview(
            self.large_files_frame,
            columns=columns,
            show='headings',
            selectmode='extended'
        )
        
        self.large_tree.heading('select', text='选择')
        self.large_tree.heading('path', text='文件路径')
        self.large_tree.heading('size', text='文件大小')
        self.large_tree.heading('modified', text='修改时间')
        self.large_tree.heading('type', text='文件类型')
        self.large_tree.heading('source', text='来源')
        
        self.large_tree.column('select', width=50, anchor='center')
        self.large_tree.column('path', width=450)
        self.large_tree.column('size', width=100, anchor='center')
        self.large_tree.column('modified', width=150, anchor='center')
        self.large_tree.column('type', width=100)
        self.large_tree.column('source', width=80, anchor='center')
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(self.large_files_frame, orient='vertical', command=self.large_tree.yview)
        scrollbar_x = ttk.Scrollbar(self.large_files_frame, orient='horizontal', command=self.large_tree.xview)
        self.large_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.large_tree.pack(side='left', fill='both', expand=True)
        scrollbar_y.pack(side='right', fill='y')
        scrollbar_x.pack(side='bottom', fill='x')
        
        # 绑定复选框点击
        self.large_tree.bind('<ButtonRelease-1>', self._on_tree_click)
        
    def _setup_useless_files_tab(self):
        """设置无用文件选项卡"""
        # 工具栏
        toolbar = ttk.Frame(self.useless_files_frame)
        toolbar.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(toolbar, text="文件类型过滤:").pack(side='left', padx=5)
        self.filter_var = tk.StringVar(value="all")
        filters = ['all', '.tmp', '.log', '.cache', '.bak']
        for f in filters:
            ttk.Radiobutton(
                toolbar, text=f if f != 'all' else '全部',
                variable=self.filter_var, value=f,
                command=lambda: self._filter_useless()
            ).pack(side='left', padx=5)
        
        # Treeview
        columns = ('select', 'path', 'size', 'reason', 'age_days', 'source')
        self.useless_tree = ttk.Treeview(
            self.useless_files_frame,
            columns=columns,
            show='headings',
            selectmode='extended'
        )
        
        self.useless_tree.heading('select', text='选择')
        self.useless_tree.heading('path', text='文件路径')
        self.useless_tree.heading('size', text='文件大小')
        self.useless_tree.heading('reason', text='可疑原因')
        self.useless_tree.heading('age_days', text='文件年龄(天)')
        self.useless_tree.heading('source', text='来源')
        
        self.useless_tree.column('select', width=50, anchor='center')
        self.useless_tree.column('path', width=450)
        self.useless_tree.column('size', width=100, anchor='center')
        self.useless_tree.column('reason', width=150)
        self.useless_tree.column('age_days', width=100, anchor='center')
        self.useless_tree.column('source', width=80, anchor='center')
        
        scrollbar_y = ttk.Scrollbar(self.useless_files_frame, orient='vertical', command=self.useless_tree.yview)
        scrollbar_x = ttk.Scrollbar(self.useless_files_frame, orient='horizontal', command=self.useless_tree.xview)
        self.useless_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.useless_tree.pack(side='left', fill='both', expand=True)
        scrollbar_y.pack(side='right', fill='y')
        scrollbar_x.pack(side='bottom', fill='x')
        
        self.useless_tree.bind('<ButtonRelease-1>', self._on_tree_click)
        
    def _setup_stats_tab(self):
        """设置统计信息选项卡"""
        self.stats_text = scrolledtext.ScrolledText(
            self.stats_frame,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.stats_text.pack(fill='both', expand=True, padx=5, pady=5)
        
    def _setup_cache_tab(self):
        """设置缓存管理选项卡"""
        # 缓存控制面板
        control = ttk.Frame(self.cache_frame, padding="10")
        control.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            control,
            text="导出缓存到文件",
            command=self._export_cache
        ).pack(side='left', padx=5)
        
        ttk.Button(
            control,
            text="从文件导入缓存",
            command=self._import_cache
        ).pack(side='left', padx=5)
        
        ttk.Button(
            control,
            text="清理过期缓存",
            command=self._clean_expired_cache
        ).pack(side='left', padx=5)
        
        # 缓存内容显示
        self.cache_text = scrolledtext.ScrolledText(
            self.cache_frame,
            wrap=tk.WORD,
            font=('Consolas', 10)
        )
        self.cache_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        self._update_cache_display()
        
    def _setup_dir_stats_tab(self):
        """设置目录统计选项卡"""
        # 控制面板
        control = ttk.Frame(self.dir_stats_frame, padding="10")
        control.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(control, text="扫描路径:").pack(side='left', padx=5)
        self.dir_scan_path_var = tk.StringVar(value="C:\\")
        ttk.Entry(control, textvariable=self.dir_scan_path_var, width=50).pack(side='left', padx=5)
        
        ttk.Button(
            control,
            text="浏览",
            command=self._browse_dir
        ).pack(side='left', padx=5)
        
        # 是否包含系统目录
        self.include_system_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            control,
            text="包含系统目录",
            variable=self.include_system_var
        ).pack(side='left', padx=20)
        
        self.dir_scan_btn = ttk.Button(
            control,
            text="扫描目录大小",
            command=self._start_dir_scan
        )
        self.dir_scan_btn.pack(side='left', padx=10)
        
        self.dir_stop_btn = ttk.Button(
            control,
            text="停止",
            command=self._stop_dir_scan,
            state='disabled'
        )
        self.dir_stop_btn.pack(side='left', padx=5)
        
        ttk.Button(
            control,
            text="展开全部",
            command=lambda: self._expand_all_dir_tree(True)
        ).pack(side='right', padx=5)
        
        ttk.Button(
            control,
            text="收起全部",
            command=lambda: self._expand_all_dir_tree(False)
        ).pack(side='right', padx=5)
        
        # 目录树
        columns = ('size', 'file_count', 'status')
        self.dir_tree = ttk.Treeview(
            self.dir_stats_frame,
            columns=columns,
            show='tree headings',
            selectmode='browse'
        )
        
        self.dir_tree.heading('#0', text='目录名称')
        self.dir_tree.heading('size', text='大小')
        self.dir_tree.heading('file_count', text='文件数')
        self.dir_tree.heading('status', text='状态')
        
        self.dir_tree.column('#0', width=400)
        self.dir_tree.column('size', width=120, anchor='center')
        self.dir_tree.column('file_count', width=80, anchor='center')
        self.dir_tree.column('status', width=100, anchor='center')
        
        # 滚动条
        scrollbar_y = ttk.Scrollbar(self.dir_stats_frame, orient='vertical', command=self.dir_tree.yview)
        scrollbar_x = ttk.Scrollbar(self.dir_stats_frame, orient='horizontal', command=self.dir_tree.xview)
        self.dir_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.dir_tree.pack(side='left', fill='both', expand=True)
        scrollbar_y.pack(side='right', fill='y')
        scrollbar_x.pack(side='bottom', fill='x')
        
        # 双击展开/收起
        self.dir_tree.bind('<Double-1>', self._on_dir_tree_double_click)
        
    def _browse_dir(self):
        """浏览选择目录"""
        from tkinter import filedialog
        try:
            path = filedialog.askdirectory(
                parent=self.root,
                title="选择要扫描的目录",
                mustexist=True
            )
            if path:
                self.dir_scan_path_var.set(path)
        except Exception as e:
            messagebox.showerror("错误", f"选择目录失败: {e}")
            
    def _expand_all_dir_tree(self, expand=True):
        """展开或收起所有节点"""
        def toggle_children(item):
            if expand:
                self.dir_tree.item(item, open=True)
            else:
                self.dir_tree.item(item, open=False)
            for child in self.dir_tree.get_children(item):
                toggle_children(child)
                
        for item in self.dir_tree.get_children():
            toggle_children(item)
            
    def _on_dir_tree_double_click(self, event):
        """双击目录树节点"""
        item = self.dir_tree.identify_row(event.y)
        if item:
            current_open = self.dir_tree.item(item, 'open')
            self.dir_tree.item(item, open=not current_open)
        
    def _load_last_scan(self):
        """加载上次扫描结果"""
        last_scan_file = os.path.join(self.data_dir, 'last_scan.json')
        if os.path.exists(last_scan_file):
            try:
                with open(last_scan_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.large_files = data.get('large_files', [])
                    self.useless_files = data.get('useless_files', [])
                    self._refresh_list()
                    self._update_status(f"已加载上次扫描结果: {len(self.large_files)} 个大文件")
            except:
                pass
                
    def _save_last_scan(self):
        """保存扫描结果"""
        last_scan_file = os.path.join(self.data_dir, 'last_scan.json')
        try:
            with open(last_scan_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'scan_time': datetime.now().isoformat(),
                    'large_files': self.large_files,
                    'useless_files': self.useless_files
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存扫描结果失败: {e}")
            
    def _start_scan(self):
        """开始完整扫描"""
        self._do_scan(use_cache=False)
        
    def _start_quick_scan(self):
        """开始快速扫描（使用缓存）"""
        self._do_scan(use_cache=True)
        
    def _do_scan(self, use_cache=True):
        """执行扫描"""
        try:
            self.min_size_mb = int(self.size_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
            return
            
        self.scanning = True
        self.scan_btn.config(state='disabled')
        self.quick_scan_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.delete_btn.config(state='disabled')
        
        # 清空现有数据（如果不是快速扫描）
        if not use_cache:
            self.large_files = []
            self.useless_files = []
            self._clear_trees()
        
        self.scanned_count = 0
        self.cached_count = 0
        
        # 在新线程中运行扫描
        scan_thread = threading.Thread(
            target=self._scan_disk, 
            args=(use_cache,),
            daemon=True
        )
        scan_thread.start()
        
    def _stop_scan(self):
        """停止扫描"""
        self.scanning = False
        self.status_var.set("扫描已停止")
        self.scan_btn.config(state='normal')
        self.quick_scan_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
    def _scan_disk(self, use_cache=True):
        """扫描磁盘"""
        min_size = self.min_size_mb * 1024 * 1024
        total_scanned = 0
        
        scan_type = "快速扫描" if use_cache else "完整扫描"
        self._update_status(f"开始{scan_type}C盘...")
        
        # 如果快速扫描，先从缓存加载
        if use_cache:
            self._load_from_cache(min_size)
        
        try:
            for root, dirs, files in os.walk('C:\\'):
                if not self.scanning:
                    break
                    
                # 跳过排除目录
                dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d))]
                
                for file in files:
                    if not self.scanning:
                        break
                        
                    file_path = os.path.join(root, file)
                    
                    try:
                        # 检查是否是链接或特殊文件
                        if os.path.islink(file_path):
                            continue
                        
                        # 检查缓存
                        if use_cache:
                            is_cached, cached_info = self.cache.is_cached(file_path)
                            if is_cached and cached_info:
                                self.cached_count += 1
                                # 检查是否满足大小条件
                                if cached_info.get('size', 0) >= min_size:
                                    self._update_from_cache(cached_info)
                                continue
                        
                        # 未缓存或缓存过期，重新扫描
                        stat = os.stat(file_path)
                        file_size = stat.st_size
                        
                        # 大文件检测
                        if file_size >= min_size:
                            file_info = {
                                'path': file_path,
                                'size': file_size,
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                'type': os.path.splitext(file)[1].lower() or '未知',
                                'source': '扫描'
                            }
                            self.large_files.append(file_info)
                            self._add_to_large_tree(file_info)
                            
                            # 更新缓存
                            self.cache.update_cache(file_path, file_info)
                            
                        # 无用文件检测
                        if self._is_useless_file(file_path, stat):
                            age_days = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days
                            useless_info = {
                                'path': file_path,
                                'size': file_size,
                                'reason': self._get_useless_reason(file_path),
                                'age_days': age_days,
                                'source': '扫描'
                            }
                            self.useless_files.append(useless_info)
                            self._add_to_useless_tree(useless_info)
                            
                            # 更新缓存
                            self.cache.update_cache(file_path, useless_info)
                        
                        total_scanned += 1
                        self.scanned_count += 1
                        
                        if total_scanned % 100 == 0:
                            cache_info = f"(缓存命中: {self.cached_count})" if use_cache else ""
                            self._update_status(
                                f"已扫描 {total_scanned} 个文件 {cache_info}"
                            )
                            
                        # 定期保存缓存
                        if total_scanned % 500 == 0:
                            self.cache.save_cache()
                            
                    except (OSError, PermissionError):
                        continue
                    except Exception as e:
                        print(f"处理文件出错 {file_path}: {e}")
                        continue
                        
        except Exception as e:
            self._update_status(f"扫描出错: {str(e)}")
            
        finally:
            # 保存缓存和扫描结果
            self.cache.save_cache()
            self._save_last_scan()
            
            self.scanning = False
            self.root.after(0, self._scan_complete, use_cache)
            
    def _load_from_cache(self, min_size):
        """从缓存加载数据"""
        self._update_status("正在从缓存加载...")
        
        for file_path, file_info in self.cache.cache.items():
            if not self.scanning:
                break
                
            try:
                # 验证文件是否仍然存在且未修改
                current_sig = self.cache.get_file_signature(file_path)
                cached_sig = self.cache.cache_index.get(file_path)
                
                if not current_sig or not cached_sig:
                    continue
                    
                if current_sig['signature'] != cached_sig['signature']:
                    continue
                
                # 检查大小条件
                if file_info.get('size', 0) >= min_size:
                    file_info['source'] = '缓存'
                    self.large_files.append(file_info)
                    self._add_to_large_tree(file_info)
                    
                # 检查是否是无用文件
                if 'reason' in file_info:
                    file_info['source'] = '缓存'
                    self.useless_files.append(file_info)
                    self._add_to_useless_tree(file_info)
                    
            except:
                continue
                
    def _update_from_cache(self, cached_info):
        """从缓存更新显示"""
        if cached_info.get('size', 0) >= self.min_size_mb * 1024 * 1024:
            cached_info['source'] = '缓存'
            if cached_info not in self.large_files:
                self.large_files.append(cached_info)
                self._add_to_large_tree(cached_info)
                
    def _should_exclude(self, path):
        """检查是否应该排除该路径"""
        path = os.path.normpath(path)
        for exclude in self.exclude_dirs:
            if path.startswith(os.path.normpath(exclude)):
                return True
        return False
        
    def _is_useless_file(self, file_path, stat):
        """检查是否是无用文件"""
        file_name = os.path.basename(file_path).lower()
        ext = os.path.splitext(file_path)[1].lower()
        
        # 检查扩展名
        if ext in self.useless_extensions:
            return True
            
        # 检查文件名特征
        useless_patterns = ['temp', 'tmp', 'cache', '.old', '.bak', 'crash']
        if any(pattern in file_name for pattern in useless_patterns):
            return True
            
        return False
        
    def _get_useless_reason(self, file_path):
        """获取无用文件原因"""
        file_name = os.path.basename(file_path).lower()
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in self.useless_extensions:
            return f"临时文件 ({ext})"
        elif 'temp' in file_name or 'tmp' in file_name:
            return "临时文件"
        elif 'cache' in file_name:
            return "缓存文件"
        elif '.old' in file_name or '.bak' in file_name:
            return "备份文件"
        else:
            return "可疑文件"
            
    def _add_to_large_tree(self, file_info):
        """添加到大文件树"""
        def add():
            modified_str = file_info['modified']
            if isinstance(modified_str, str):
                try:
                    dt = datetime.fromisoformat(modified_str)
                    modified_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
                    
            self.large_tree.insert(
                '',
                'end',
                values=(
                    '☐',
                    file_info['path'],
                    self._human_readable_size(file_info['size']),
                    modified_str,
                    file_info.get('type', '未知'),
                    file_info.get('source', '扫描')
                ),
                tags=('unchecked',)
            )
        self.root.after(0, add)
        
    def _add_to_useless_tree(self, file_info):
        """添加到无用文件树"""
        def add():
            self.useless_tree.insert(
                '',
                'end',
                values=(
                    '☐',
                    file_info['path'],
                    self._human_readable_size(file_info['size']),
                    file_info.get('reason', '可疑文件'),
                    file_info.get('age_days', 0),
                    file_info.get('source', '扫描')
                ),
                tags=('unchecked',)
            )
        self.root.after(0, add)
        
    def _on_tree_click(self, event):
        """处理树形控件点击事件"""
        tree = event.widget
        region = tree.identify_region(event.x, event.y)
        
        if region == 'cell':
            column = tree.identify_column(event.x)
            item = tree.identify_row(event.y)
            
            if column == '#1' and item:  # 选择列
                current_val = tree.set(item, 'select')
                new_val = '☑' if current_val == '☐' else '☐'
                tree.set(item, 'select', new_val)
                tree.item(item, tags=('checked' if new_val == '☑' else 'unchecked',))
                
    def _scan_complete(self, use_cache):
        """扫描完成处理"""
        self.scan_btn.config(state='normal')
        self.quick_scan_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.delete_btn.config(state='normal')
        
        self._update_stats(use_cache)
        self._update_cache_display()
        
        scan_type = "快速扫描" if use_cache else "完整扫描"
        cache_info = f"，缓存命中 {self.cached_count} 个" if use_cache else ""
        self._update_status(
            f"{scan_type}完成！发现 {len(self.large_files)} 个大文件，"
            f"{len(self.useless_files)} 个可疑无用文件{cache_info}"
        )
        
    def _update_stats(self, use_cache=False):
        """更新统计信息"""
        total_large_size = sum(f['size'] for f in self.large_files)
        total_useless_size = sum(f['size'] for f in self.useless_files)
        
        cache_stats = self.cache.get_cache_stats()
        
        stats = f"""
{'='*60}
C盘扫描统计报告
扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
扫描模式: {'快速扫描(使用缓存)' if use_cache else '完整扫描'}
{'='*60}

大文件统计:
  - 文件数量: {len(self.large_files)} 个
  - 总大小: {self._human_readable_size(total_large_size)}
  - 平均大小: {self._human_readable_size(total_large_size // max(len(self.large_files), 1))}

可疑无用文件统计:
  - 文件数量: {len(self.useless_files)} 个
  - 总大小: {self._human_readable_size(total_useless_size)}
  - 可释放空间: {self._human_readable_size(total_useless_size)}

缓存统计:
  - 缓存文件数: {cache_stats['cached_files']} 个
  - 本次缓存命中: {self.cached_count} 个
  - 缓存文件大小: {self._human_readable_size(cache_stats['cache_size'])}

文件类型分布 (Top 10):
"""
        
        # 统计文件类型
        type_count = {}
        for f in self.large_files:
            ext = f.get('type', '未知')
            type_count[ext] = type_count.get(ext, {'count': 0, 'size': 0})
            type_count[ext]['count'] += 1
            type_count[ext]['size'] += f['size']
            
        sorted_types = sorted(type_count.items(), key=lambda x: x[1]['size'], reverse=True)[:10]
        for ext, info in sorted_types:
            stats += f"  {ext:15} {info['count']:5} 个  {self._human_readable_size(info['size']):>12}\n"
            
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', stats)
        
    def _delete_selected(self):
        """删除选中的文件"""
        selected_large = []
        selected_useless = []
        
        # 获取选中的大文件
        for item in self.large_tree.get_children():
            if self.large_tree.set(item, 'select') == '☑':
                selected_large.append(self.large_tree.set(item, 'path'))
                
        # 获取选中的无用文件
        for item in self.useless_tree.get_children():
            if self.useless_tree.set(item, 'select') == '☑':
                selected_useless.append(self.useless_tree.set(item, 'path'))
                
        all_selected = selected_large + selected_useless
        
        if not all_selected:
            messagebox.showwarning("提示", "请先选择要删除的文件！")
            return
            
        # 确认对话框
        confirm = messagebox.askyesno(
            "确认删除",
            f"确定要删除选中的 {len(all_selected)} 个文件吗？\n"
            f"此操作不可恢复！"
        )
        
        if not confirm:
            return
            
        # 执行删除
        deleted = 0
        failed = 0
        total_freed = 0
        
        for file_path in all_selected:
            try:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_freed += size
                    deleted += 1
                    
                    # 从缓存中移除
                    if file_path in self.cache.cache:
                        del self.cache.cache[file_path]
                    if file_path in self.cache.cache_index:
                        del self.cache.cache_index[file_path]
                        
            except Exception as e:
                failed += 1
                print(f"删除失败 {file_path}: {e}")
                
        # 保存更新后的缓存
        self.cache.save_cache()
        
        messagebox.showinfo(
            "删除完成",
            f"成功删除: {deleted} 个文件\n"
            f"删除失败: {failed} 个文件\n"
            f"释放空间: {self._human_readable_size(total_freed)}"
        )
        
        # 刷新列表
        self._refresh_list()
        self._update_cache_display()
        
    def _refresh_list(self):
        """刷新列表"""
        if not self.large_files and not self.useless_files:
            return
            
        self._clear_trees()
        
        for file_info in self.large_files:
            self._add_to_large_tree(file_info)
            
        for file_info in self.useless_files:
            self._add_to_useless_tree(file_info)
            
    def _clear_trees(self):
        """清空树形控件"""
        for item in self.large_tree.get_children():
            self.large_tree.delete(item)
        for item in self.useless_tree.get_children():
            self.useless_tree.delete(item)
            
    def _sort_files(self, tree_type):
        """排序文件"""
        if tree_type == 'large':
            if self.sort_var.get() == 'size_desc':
                self.large_files.sort(key=lambda x: x['size'], reverse=True)
            else:
                self.large_files.sort(
                    key=lambda x: x.get('modified', ''),
                    reverse=True
                )
            self._refresh_list()
            
    def _search_files(self, tree_type):
        """搜索文件"""
        keyword = self.search_var.get().lower()
        if not keyword:
            self._refresh_list()
            return
            
        self._clear_trees()
        
        for file_info in self.large_files:
            if keyword in file_info['path'].lower():
                self._add_to_large_tree(file_info)
                
    def _filter_useless(self):
        """过滤无用文件"""
        filter_type = self.filter_var.get()
        
        for item in self.useless_tree.get_children():
            self.useless_tree.delete(item)
            
        for file_info in self.useless_files:
            if filter_type == 'all' or filter_type in file_info['path'].lower():
                self._add_to_useless_tree(file_info)
                
    def _clear_cache(self):
        """清空缓存"""
        if messagebox.askyesno("确认", "确定要清空所有缓存吗？"):
            self.cache.clear_cache()
            self.dir_cache.clear_cache()
            self._update_cache_display()
            messagebox.showinfo("完成", "缓存已清空(包括文件缓存和目录缓存)")
            
    def _show_cache_status(self):
        """显示缓存状态"""
        stats = self.cache.get_cache_stats()
        messagebox.showinfo(
            "缓存状态",
            f"缓存文件数: {stats['cached_files']} 个\n"
            f"缓存大小: {self._human_readable_size(stats['cache_size'])}\n"
            f"缓存文件: {self.cache.cache_file}"
        )
        
    def _export_cache(self):
        """导出缓存"""
        from tkinter import filedialog
        try:
            filename = filedialog.asksaveasfilename(
                parent=self.root,
                title="导出缓存",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump({
                        'cache': self.cache.cache,
                        'cache_index': self.cache.cache_index,
                        'export_time': datetime.now().isoformat()
                    }, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", f"缓存已导出到:\n{filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")
                
    def _import_cache(self):
        """导入缓存"""
        from tkinter import filedialog
        try:
            filename = filedialog.askopenfilename(
                parent=self.root,
                title="导入缓存",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cache.cache = data.get('cache', {})
                    self.cache.cache_index = data.get('cache_index', {})
                    self.cache.save_cache()
                    self._update_cache_display()
                messagebox.showinfo("成功", f"缓存已导入")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {e}")
                
    def _clean_expired_cache(self):
        """清理过期缓存（文件已不存在的）"""
        removed = 0
        for file_path in list(self.cache.cache.keys()):
            if not os.path.exists(file_path):
                del self.cache.cache[file_path]
                if file_path in self.cache.cache_index:
                    del self.cache.cache_index[file_path]
                removed += 1
                
        self.cache.save_cache()
        self._update_cache_display()
        messagebox.showinfo("完成", f"已清理 {removed} 个过期缓存项")
        
    def _update_cache_display(self):
        """更新缓存显示"""
        stats = self.cache.get_cache_stats()
        
        display = f"""
缓存统计信息
{'='*60}
缓存文件数: {stats['cached_files']} 个
缓存大小: {self._human_readable_size(stats['cache_size'])}
缓存文件路径: {self.cache.cache_file}

缓存文件列表 (前50个):
"""
        
        for i, (path, info) in enumerate(list(self.cache.cache.items())[:50]):
            size = info.get('size', 0)
            display += f"{i+1}. {path}\n   大小: {self._human_readable_size(size)}\n"
            
        if len(self.cache.cache) > 50:
            display += f"\n... 还有 {len(self.cache.cache) - 50} 个文件 ...\n"
            
        self.cache_text.delete('1.0', tk.END)
        self.cache_text.insert('1.0', display)
        
    def _start_dir_scan(self):
        """开始目录扫描"""
        scan_path = self.dir_scan_path_var.get()
        if not os.path.exists(scan_path):
            messagebox.showerror("错误", f"路径不存在: {scan_path}")
            return
            
        if not os.path.isdir(scan_path):
            messagebox.showerror("错误", f"不是有效目录: {scan_path}")
            return
            
        self.dir_scanning = True
        self.dir_scan_btn.config(state='disabled')
        self.dir_stop_btn.config(state='normal')
        
        # 清空现有数据
        for item in self.dir_tree.get_children():
            self.dir_tree.delete(item)
        self.dir_tree_data = {}
        
        # 在新线程中运行扫描
        scan_thread = threading.Thread(
            target=self._scan_directory,
            args=(scan_path, ''),
            daemon=True
        )
        scan_thread.start()
        
    def _stop_dir_scan(self):
        """停止目录扫描"""
        self.dir_scanning = False
        self._update_status("目录扫描已停止")
        self.dir_scan_btn.config(state='normal')
        self.dir_stop_btn.config(state='disabled')
        
    def _scan_directory(self, root_path, parent_item=''):
        """递归扫描目录大小"""
        root_path = os.path.normpath(root_path)
        include_system = self.include_system_var.get()
        
        # 检查是否停止
        if not self.dir_scanning:
            return
            
        try:
            # 检查缓存（使用包含系统目录的设置作为缓存键的一部分）
            cache_key = f"{root_path}_system_{include_system}"
            is_cached, cached_data = self.dir_cache.is_cached(cache_key)
            
            if is_cached and cached_data:
                # 从缓存加载
                total_size = cached_data['size']
                file_count = cached_data['file_count']
                subdirs = cached_data.get('subdirs', {})
                status = "缓存"
            else:
                # 重新计算
                total_size = 0
                file_count = 0
                subdirs = {}
                scanned_subdirs = []
                skipped_dirs = []
                
                try:
                    for entry in os.scandir(root_path):
                        if not self.dir_scanning:
                            return
                            
                        try:
                            if entry.is_file(follow_symlinks=False):
                                try:
                                    stat = entry.stat()
                                    total_size += stat.st_size
                                    file_count += 1
                                except (OSError, PermissionError):
                                    pass
                            elif entry.is_dir(follow_symlinks=False):
                                # 排除特定目录（根据用户选择）
                                if not include_system and self._should_exclude(entry.path):
                                    skipped_dirs.append(entry.name)
                                    continue
                                # 递归扫描子目录
                                sub_size, sub_count, sub_subdirs = self._scan_directory_recursive(entry.path, include_system)
                                if sub_size > 0 or sub_count > 0:
                                    subdirs[entry.name] = {
                                        'size': sub_size,
                                        'file_count': sub_count,
                                        'subdirs': sub_subdirs
                                    }
                                    scanned_subdirs.append(entry.name)
                                    total_size += sub_size
                                    file_count += sub_count
                        except (OSError, PermissionError):
                            continue
                            
                except PermissionError:
                    status = "无权限"
                    self.root.after(0, lambda: self._update_status(f"无权限访问: {root_path}"))
                except Exception as e:
                    status = "错误"
                    print(f"扫描目录出错 {root_path}: {e}")
                else:
                    status = "已扫描"
                    if skipped_dirs:
                        print(f"跳过的目录: {skipped_dirs}")
                    # 更新缓存
                    self.dir_cache.update_cache(cache_key, total_size, file_count, subdirs)
                    # 定期保存缓存
                    if file_count % 100 == 0:
                        self.dir_cache.save_cache()
                        
            # 如果是根目录，添加到树形控件
            if parent_item == '':
                self.root.after(0, lambda: self._add_dir_to_tree(
                    '', os.path.basename(root_path) or root_path,
                    total_size, file_count, status, root_path
                ))
                # 添加子目录
                for subdir_name, subdir_data in subdirs.items():
                    self._add_subdirs_to_tree(
                        '', subdir_name, subdir_data,
                        os.path.join(root_path, subdir_name)
                    )
                    
            # 扫描完成
            if parent_item == '':
                self.dir_cache.save_cache()
                self.dir_scanning = False
                self.root.after(0, lambda: self._dir_scan_complete(total_size, file_count))
                
        except Exception as e:
            print(f"扫描目录时出错: {e}")
            self.dir_scanning = False
            self.root.after(0, self._dir_scan_complete, 0, 0)
            
    def _scan_directory_recursive(self, dir_path, include_system=True):
        """递归扫描目录（返回大小和文件数）"""
        dir_path = os.path.normpath(dir_path)
        
        # 检查缓存
        cache_key = f"{dir_path}_system_{include_system}"
        is_cached, cached_data = self.dir_cache.is_cached(cache_key)
        if is_cached and cached_data:
            return cached_data['size'], cached_data['file_count'], cached_data.get('subdirs', {})
            
        total_size = 0
        file_count = 0
        subdirs = {}
        
        try:
            for entry in os.scandir(dir_path):
                if not self.dir_scanning:
                    return total_size, file_count, subdirs
                    
                try:
                    if entry.is_file(follow_symlinks=False):
                        try:
                            stat = entry.stat()
                            total_size += stat.st_size
                            file_count += 1
                        except (OSError, PermissionError):
                            pass
                    elif entry.is_dir(follow_symlinks=False):
                        if not include_system and self._should_exclude(entry.path):
                            continue
                        sub_size, sub_count, sub_subdirs = self._scan_directory_recursive(entry.path, include_system)
                        if sub_size > 0 or sub_count > 0:
                            subdirs[entry.name] = {
                                'size': sub_size,
                                'file_count': sub_count,
                                'subdirs': sub_subdirs
                            }
                            total_size += sub_size
                            file_count += sub_count
                except (OSError, PermissionError):
                    continue
                    
        except PermissionError:
            pass
        except Exception as e:
            print(f"扫描子目录出错 {dir_path}: {e}")
            
        # 更新缓存
        self.dir_cache.update_cache(cache_key, total_size, file_count, subdirs)
        return total_size, file_count, subdirs
        
    def _add_dir_to_tree(self, parent, name, size, file_count, status, full_path):
        """添加目录到树形控件"""
        item = self.dir_tree.insert(
            parent,
            'end',
            text=name,
            values=(
                self._human_readable_size(size),
                file_count,
                status
            ),
            tags=('normal',)
        )
        self.dir_tree_data[item] = {
            'path': full_path,
            'size': size,
            'file_count': file_count
        }
        
        # 根据大小设置颜色
        if size > 1024 * 1024 * 1024:  # > 1GB
            self.dir_tree.item(item, tags=('large',))
        elif size > 100 * 1024 * 1024:  # > 100MB
            self.dir_tree.item(item, tags=('medium',))
            
        return item
        
    def _add_subdirs_to_tree(self, parent_item, subdir_name, subdir_data, full_path):
        """递归添加子目录到树"""
        item = self.dir_tree.insert(
            parent_item,
            'end',
            text=subdir_name,
            values=(
                self._human_readable_size(subdir_data['size']),
                subdir_data['file_count'],
                '已扫描'
            ),
            tags=('normal',)
        )
        self.dir_tree_data[item] = {
            'path': full_path,
            'size': subdir_data['size'],
            'file_count': subdir_data['file_count']
        }
        
        # 根据大小设置颜色
        if subdir_data['size'] > 1024 * 1024 * 1024:
            self.dir_tree.item(item, tags=('large',))
        elif subdir_data['size'] > 100 * 1024 * 1024:
            self.dir_tree.item(item, tags=('medium',))
            
        # 递归添加子目录
        for child_name, child_data in subdir_data.get('subdirs', {}).items():
            self._add_subdirs_to_tree(
                item,
                child_name,
                child_data,
                os.path.join(full_path, child_name)
            )
            
    def _dir_scan_complete(self, total_size=0, total_files=0):
        """目录扫描完成"""
        self.dir_scan_btn.config(state='normal')
        self.dir_stop_btn.config(state='disabled')
        
        # 如果没有传入参数，计算总大小
        if total_size == 0:
            for item in self.dir_tree.get_children():
                data = self.dir_tree_data.get(item, {})
                total_size += data.get('size', 0)
                total_files += data.get('file_count', 0)
        
        # 获取C盘实际使用情况
        try:
            import shutil
            c_usage = shutil.disk_usage('C:\\')
            c_total = c_usage.total
            c_used = c_usage.used
            c_free = c_usage.free
            
            scan_info = f"扫描结果: {self._human_readable_size(total_size)} | "
            disk_info = f"C盘实际: 已用 {self._human_readable_size(c_used)} / 总计 {self._human_readable_size(c_total)} | "
            diff_info = f"差额: {self._human_readable_size(c_used - total_size)} (可能因权限无法访问的系统文件)"
        except:
            scan_info = f"扫描完成！总计: {self._human_readable_size(total_size)}, {total_files} 个文件"
            disk_info = ""
            diff_info = ""
            
        self._update_status(scan_info + disk_info + diff_info)
        
        # 配置标签颜色
        self.dir_tree.tag_configure('large', foreground='red', font=('Arial', 9, 'bold'))
        self.dir_tree.tag_configure('medium', foreground='orange')
        self.dir_tree.tag_configure('normal', foreground='black')
        
    def _update_status(self, message):
        """更新状态栏"""
        def update():
            self.status_var.set(message)
        self.root.after(0, update)
        
    def _human_readable_size(self, size):
        """转换为人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"


def main():
    """主函数"""
    root = tk.Tk()
    app = DiskMonitorGUI(root)
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('vista')
    
    root.mainloop()


if __name__ == '__main__':
    main()
