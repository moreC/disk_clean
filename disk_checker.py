#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import argparse
from datetime import datetime

class DiskLargeFileChecker:
    def __init__(self, min_size_mb=10):
        self.min_size = min_size_mb * 1024 * 1024
        self.scan_paths = [
            'C:\\',
            os.path.expanduser('~\\AppData'),
            os.path.expanduser('~\\Documents')
        ]
        
        # 排除的目录
        self.exclude_dirs = [
            'C:\\Windows',
            'C:\\$Recycle.Bin',
            'C:\\System Volume Information',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            'C:\\ProgramData'
        ]
        
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
    
    def should_exclude(self, path):
        """检查路径是否应该排除"""
        path = os.path.normpath(path)
        for exclude in self.exclude_dirs:
            exclude = os.path.normpath(exclude)
            if path.startswith(exclude):
                return True
        return False
    
    def get_human_readable_size(self, size):
        """获取人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def scan_large_files(self):
        """扫描大文件"""
        large_files = {}
        
        print("开始扫描C盘大文件...")
        start_time = time.time()
        
        for scan_path in self.scan_paths:
            if not os.path.exists(scan_path):
                continue
            
            if self.should_exclude(scan_path):
                continue
            
            print(f"扫描目录: {scan_path}")
            
            try:
                for root, dirs, files in os.walk(scan_path):
                    # 过滤排除的目录
                    dirs[:] = [d for d in dirs if not self.should_exclude(os.path.join(root, d))]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        try:
                            file_size = os.path.getsize(file_path)
                            
                            if file_size >= self.min_size:
                                large_files[file_path] = {
                                    'size': file_size,
                                    'modified': os.path.getmtime(file_path),
                                    'created': os.path.getctime(file_path)
                                }
                        except Exception:
                            pass
            except Exception as e:
                print(f"扫描失败: {scan_path} - {str(e)}")
        
        end_time = time.time()
        print(f"扫描完成，耗时: {end_time - start_time:.2f}秒")
        print(f"发现大文件数量: {len(large_files)}")
        
        return large_files
    
    def load_previous_scan(self):
        """加载之前的扫描记录"""
        scan_file = os.path.join(self.data_dir, 'large_files.json')
        
        if os.path.exists(scan_file):
            try:
                with open(scan_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {}
    
    def save_scan_result(self, large_files):
        """保存扫描结果"""
        scan_file = os.path.join(self.data_dir, 'large_files.json')
        
        # 只保存文件路径和基本信息，不保存所有属性
        files_to_save = {}
        for path, info in large_files.items():
            files_to_save[path] = {
                'size': info['size'],
                'modified': info['modified'],
                'created': info['created']
            }
        
        with open(scan_file, 'w', encoding='utf-8') as f:
            json.dump(files_to_save, f, ensure_ascii=False, indent=2)
    
    def find_new_files(self, current_files, previous_files):
        """找出新增的大文件"""
        new_files = []
        
        for file_path, info in current_files.items():
            if file_path not in previous_files:
                new_files.append({
                    'path': file_path,
                    'size': info['size'],
                    'modified': info['modified'],
                    'created': info['created']
                })
        
        # 按大小排序
        new_files.sort(key=lambda x: x['size'], reverse=True)
        
        return new_files
    
    def generate_report(self, new_files, is_first_scan=False):
        """生成报告"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_first_scan:
            report_file = os.path.join(self.log_dir, f'large_files_{datetime.now().strftime("%Y%m%d")}_initial.txt')
        else:
            report_file = os.path.join(self.log_dir, f'large_files_{datetime.now().strftime("%Y%m%d")}.txt')
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"C盘大文件检查报告\n")
            f.write(f"检查时间: {timestamp}\n")
            f.write(f"最小文件大小: {self.min_size // (1024*1024)} MB\n")
            f.write("=" * 80 + "\n\n")
            
            if is_first_scan:
                f.write(f"首次扫描，共发现 {len(new_files)} 个大文件:\n\n")
            else:
                f.write(f"新增大文件数量: {len(new_files)} 个\n\n")
            
            for i, file_info in enumerate(new_files, 1):
                f.write(f"{i}. 文件路径: {file_info['path']}\n")
                f.write(f"   文件大小: {self.get_human_readable_size(file_info['size'])}\n")
                created_time = datetime.fromtimestamp(file_info['created']).strftime('%Y-%m-%d %H:%M:%S')
                modified_time = datetime.fromtimestamp(file_info['modified']).strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"   创建时间: {created_time}\n")
                f.write(f"   修改时间: {modified_time}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print(f"报告已生成: {report_file}")
        return report_file
    
    def run(self, save_result=True):
        """运行检查"""
        # 扫描当前大文件
        current_files = self.scan_large_files()
        
        # 加载之前的扫描记录
        previous_files = self.load_previous_scan()
        
        # 找出新增文件
        if previous_files:
            new_files = self.find_new_files(current_files, previous_files)
            is_first_scan = False
        else:
            new_files = []
            for path, info in current_files.items():
                new_files.append({
                    'path': path,
                    'size': info['size'],
                    'modified': info['modified'],
                    'created': info['created']
                })
            new_files.sort(key=lambda x: x['size'], reverse=True)
            is_first_scan = True
        
        # 生成报告
        report_file = self.generate_report(new_files, is_first_scan)
        
        # 保存当前扫描结果
        if save_result:
            self.save_scan_result(current_files)
        
        # 打印摘要
        print("\n" + "=" * 80)
        print("检查完成!")
        print("=" * 80)
        
        if is_first_scan:
            print(f"首次扫描，共发现 {len(new_files)} 个大文件")
        else:
            print(f"新增大文件数量: {len(new_files)} 个")
        
        if new_files:
            print("\n新增大文件列表 (前10个):")
            for i, file_info in enumerate(new_files[:10], 1):
                print(f"  {i}. {self.get_human_readable_size(file_info['size'])} - {file_info['path']}")
        
        print(f"\n详细报告: {report_file}")
        
        return new_files

def main():
    parser = argparse.ArgumentParser(description='C盘大文件检查工具')
    parser.add_argument('--min-size', '-m', type=int, default=10, help='最小文件大小(MB)')
    parser.add_argument('--no-save', action='store_true', help='不保存扫描结果')
    args = parser.parse_args()
    
    checker = DiskLargeFileChecker(min_size_mb=args.min_size)
    checker.run(save_result=not args.no_save)

if __name__ == '__main__':
    main()
