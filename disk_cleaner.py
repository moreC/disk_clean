#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import argparse
from datetime import datetime

class DiskCleaner:
    def __init__(self):
        # 定义无用文件类型
        self.useless_extensions = {
            '.tmp', '.temp', '.log', '.bak', '.old', '.swp', '.swo',
            '.crdownload', '.part', '.tmp1', '.tmp2', '.dmp', '.err',
            '.cache', '.dat', '.db-journal', '.sqlite-journal'
        }
        
        # 定义需要扫描的目录
        self.scan_dirs = [
            'C:\\',
            os.path.expanduser('~\\AppData\\Local\\Temp'),
            os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\Temporary Internet Files'),
            os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\INetCache'),
            os.path.expanduser('~\\Downloads'),
            'C:\\Windows\\Temp',
            'C:\\Windows\\Prefetch'
        ]
        
        # 定义需要排除的目录
        self.exclude_dirs = [
            'C:\\Windows',
            'C:\\$Recycle.Bin',
            'C:\\System Volume Information'
        ]
        
        # 结果存储
        self.useless_files = []
        self.total_size = 0
    
    def is_useless_file(self, file_path):
        """判断文件是否为无用文件"""
        # 检查文件扩展名
        ext = os.path.splitext(file_path)[1].lower()
        if ext in self.useless_extensions:
            return True
        
        # 检查文件名包含临时文件特征
        file_name = os.path.basename(file_path).lower()
        if any(keyword in file_name for keyword in ['temp', 'tmp', 'cache', 'log']):
            return True
        
        # 检查文件大小（大于100MB的临时文件）
        try:
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024 and ext in ['.tmp', '.temp', '.part']:
                return True
        except:
            pass
        
        return False
    
    def should_exclude(self, dir_path):
        """判断目录是否应该排除"""
        dir_path = os.path.normpath(dir_path)
        for exclude in self.exclude_dirs:
            exclude = os.path.normpath(exclude)
            if dir_path.startswith(exclude):
                return True
        return False
    
    def scan_directory(self, directory):
        """扫描目录"""
        if not os.path.exists(directory):
            return
        
        if self.should_exclude(directory):
            return
        
        try:
            for root, dirs, files in os.walk(directory):
                # 过滤掉应该排除的子目录
                dirs[:] = [d for d in dirs if not self.should_exclude(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if self.is_useless_file(file_path):
                            file_size = os.path.getsize(file_path)
                            self.useless_files.append({
                                'path': file_path,
                                'size': file_size,
                                'last_modified': os.path.getmtime(file_path)
                            })
                            self.total_size += file_size
                    except Exception as e:
                        # 忽略权限错误等
                        pass
        except Exception as e:
            # 忽略权限错误等
            pass
    
    def scan(self):
        """开始扫描"""
        print("开始扫描C盘无用文件...")
        start_time = time.time()
        
        for directory in self.scan_dirs:
            print(f"扫描目录: {directory}")
            self.scan_directory(directory)
        
        end_time = time.time()
        print(f"扫描完成，耗时: {end_time - start_time:.2f}秒")
    
    def get_human_readable_size(self, size):
        """获取人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def display_results(self):
        """显示扫描结果"""
        print("\n" + "=" * 80)
        print("扫描结果")
        print("=" * 80)
        print(f"发现无用文件数: {len(self.useless_files)}")
        print(f"总占用空间: {self.get_human_readable_size(self.total_size)}")
        print("\n详细文件列表:")
        print("-" * 80)
        
        # 按文件大小排序
        sorted_files = sorted(self.useless_files, key=lambda x: x['size'], reverse=True)
        
        for file_info in sorted_files[:50]:  # 只显示前50个文件
            size = self.get_human_readable_size(file_info['size'])
            last_modified = datetime.fromtimestamp(file_info['last_modified']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{file_info['path']} - {size} - 最后修改: {last_modified}")
        
        if len(sorted_files) > 50:
            print(f"... 还有 {len(sorted_files) - 50} 个文件未显示")
    
    def export_results(self, output_file):
        """导出结果到文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("扫描结果\n")
            f.write("=" * 80 + "\n")
            f.write(f"发现无用文件数: {len(self.useless_files)}\n")
            f.write(f"总占用空间: {self.get_human_readable_size(self.total_size)}\n")
            f.write("\n详细文件列表:\n")
            f.write("-" * 80 + "\n")
            
            sorted_files = sorted(self.useless_files, key=lambda x: x['size'], reverse=True)
            for file_info in sorted_files:
                size = self.get_human_readable_size(file_info['size'])
                last_modified = datetime.fromtimestamp(file_info['last_modified']).strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{file_info['path']} - {size} - 最后修改: {last_modified}\n")
        
        print(f"\n结果已导出到: {output_file}")

def main():
    parser = argparse.ArgumentParser(description='C盘无用文件扫描工具')
    parser.add_argument('--output', '-o', type=str, help='导出结果到文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细扫描过程')
    args = parser.parse_args()
    
    cleaner = DiskCleaner()
    cleaner.scan()
    cleaner.display_results()
    
    if args.output:
        cleaner.export_results(args.output)

if __name__ == '__main__':
    main()
