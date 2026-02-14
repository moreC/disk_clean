#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import time
from datetime import datetime

class CleanupPlanner:
    def __init__(self):
        # 定义要删除的目录列表
        self.cleanup_items = [
            {
                'name': 'Local\Temp 临时文件',
                'path': os.path.expanduser('~\\AppData\\Local\\Temp'),
                'expected_size': '~16 GB',
                'priority': 'high'
            },
            {
                'name': 'Thunder Network 迅雷临时文件',
                'path': os.path.expanduser('~\\AppData\\Local\\Temp\\Thunder Network'),
                'expected_size': '~6.5 GB',
                'priority': 'high'
            },
            {
                'name': 'QQLive 腾讯视频缓存',
                'path': os.path.expanduser('~\\AppData\\Roaming\\Tencent\\QQLive'),
                'expected_size': '~2.9 GB',
                'priority': 'medium'
            },
            {
                'name': 'DNF 游戏日志',
                'path': os.path.expanduser('~\\AppData\\LocalLow\\DNF'),
                'expected_size': '~94.77 MB',
                'priority': 'medium'
            },
            {
                'name': 'WeChat Files 微信文件',
                'path': os.path.expanduser('~\\Documents\\WeChat Files'),
                'expected_size': '~3.40 GB',
                'priority': 'low'
            }
        ]
        
        # 结果记录
        self.results = []
    
    def check_directory(self, path):
        """检查目录是否存在"""
        return os.path.exists(path)
    
    def get_directory_size(self, path):
        """获取目录大小"""
        if not os.path.exists(path):
            return 0
        
        try:
            # 使用PowerShell命令获取目录大小
            cmd = f"powershell -Command ""Get-ChildItem -Path '{path}' -Recurse | Measure-Object -Property Length -Sum | Select-Object Sum"""
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout.strip():
                # 解析输出
                size_str = result.stdout.strip()
                if 'Sum' in size_str:
                    # 尝试提取数字
                    import re
                    match = re.search(r'Sum\s