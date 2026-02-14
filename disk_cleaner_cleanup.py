#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import time
import argparse
from datetime import datetime

class DiskCleanerCleanup:
    def __init__(self):
        # 定义要清理的目录和文件类型
        self.cleanup_targets = {
            'temp_files': {
                'description': '用户临时文件',
                'paths': [
                    os.path.expanduser('~\\AppData\\Local\\Temp'),
                    'C:\\Windows\\Temp'
                ],
                'patterns': ['*.tmp', '*.temp', '*.log', '*.bak', '*.old', '*.swp', '*.swo',
                           '*.crdownload', '*.part', '*.tmp1', '*.tmp2', '*.dmp', '*.err',
                           '*.cache', '*.dat', '*.db-journal', '*.sqlite-journal']
            },
            'game_logs': {
                'description': '游戏日志文件',
                'paths': [
                    os.path.expanduser('~\\AppData\\LocalLow\\mulonggame\\Mobile Legends_ Bang Bang\\Flog')
                ],
                'patterns': ['*.log']
            },
            'enterprise_logs': {
                'description': '企业软件日志',
                'paths': [
                    'C:\\ProgramData\\ZtsmEnt\\TDHS\\LOG',
                    'C:\\Program Files (x86)\\ZtsmEnt'
                ],
                'patterns': ['*.log', '*.bak']
            },
            'browser_cache': {
                'description': '浏览器缓存',
                'paths': [
                    os.path.expanduser('~\\AppData\\Local\\Microsoft\\Windows\\WebCache')
                ],
                'patterns': ['*.dat', '*.bin']
            },
            'downloads': {
                'description': '未完成的下载',
                'paths': [
                    os.path.expanduser('~\\Downloads')
                ],
                'patterns': ['*.crdownload', '*.part']
            }
        }
        
        # 结果统计
        self.cleaned_files = 0
        self.freed_space = 0
        self.failed_files = []
    
    def get_human_readable_size(self, size):
        """获取人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def should_keep(self, file_path):
        """判断是否应该保留文件"""
        # 保留系统关键文件
        critical_keywords = ['system', 'boot', 'windows', 'program', 'service']
        file_name = os.path.basename(file_path).lower()
        if any(keyword in file_name for keyword in critical_keywords):
            return True
        
        # 保留最近修改的文件（24小时内）
        try:
            mtime = os.path.getmtime(file_path)
            if time.time() - mtime < 24 * 3600:
                return True
        except:
            pass
        
        return False
    
    def cleanup_directory(self, directory, patterns):
        """清理目录中的文件"""
        if not os.path.exists(directory):
            return
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # 检查是否应该保留
                    if self.should_keep(file_path):
                        continue
                    
                    # 检查文件是否匹配模式
                    ext = os.path.splitext(file)[1].lower()
                    if any(file.endswith(pat.replace('*', '')) for pat in patterns):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            self.cleaned_files += 1
                            self.freed_space += file_size
                            print(f"已清理: {file_path} ({self.get_human_readable_size(file_size)})")
                        except Exception as e:
                            self.failed_files.append((file_path, str(e)))
                            print(f"清理失败: {file_path} - {str(e)}")
        except Exception as e:
            print(f"遍历目录失败: {directory} - {str(e)}")
    
    def cleanup(self):
        """开始清理"""
        print("开始清理无用文件...")
        start_time = time.time()
        
        for target_name, target in self.cleanup_targets.items():
            print(f"\n=== 清理: {target['description']} ===")
            for path in target['paths']:
                print(f"清理目录: {path}")
                self.cleanup_directory(path, target['patterns'])
        
        end_time = time.time()
        print(f"\n=== 清理完成 ===")
        print(f"清理文件数: {self.cleaned_files}")
        print(f"释放空间: {self.get_human_readable_size(self.freed_space)}")
        print(f"清理耗时: {end_time - start_time:.2f}秒")
        
        if self.failed_files:
            print(f"\n=== 清理失败的文件 ({len(self.failed_files)}) ===")
            for file_path, error in self.failed_files[:10]:  # 只显示前10个
                print(f"{file_path} - {error}")
            if len(self.failed_files) > 10:
                print(f"... 还有 {len(self.failed_files) - 10} 个文件清理失败")
    
    def dry_run(self):
        """模拟清理（不实际删除）"""
        print("开始模拟清理（不实际删除）...")
        start_time = time.time()
        
        total_files = 0
        total_size = 0
        
        for target_name, target in self.cleanup_targets.items():
            print(f"\n=== 模拟清理: {target['description']} ===")
            for path in target['paths']:
                print(f"扫描目录: {path}")
                if not os.path.exists(path):
                    print(f"目录不存在: {path}")
                    continue
                
                try:
                    for root, dirs, files in os.walk(path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            
                            # 检查是否应该保留
                            if self.should_keep(file_path):
                                continue
                            
                            # 检查文件是否匹配模式
                            ext = os.path.splitext(file)[1].lower()
                            if any(file.endswith(pat.replace('*', '')) for pat in target['patterns']):
                                try:
                                    file_size = os.path.getsize(file_path)
                                    total_files += 1
                                    total_size += file_size
                                    print(f"将清理: {file_path} ({self.get_human_readable_size(file_size)})")
                                except Exception as e:
                                    print(f"无法访问: {file_path} - {str(e)}")
                except Exception as e:
                    print(f"遍历目录失败: {path} - {str(e)}")
        
        end_time = time.time()
        print(f"\n=== 模拟清理完成 ===")
        print(f"预计清理文件数: {total_files}")
        print(f"预计释放空间: {self.get_human_readable_size(total_size)}")
        print(f"扫描耗时: {end_time - start_time:.2f}秒")

def main():
    parser = argparse.ArgumentParser(description='C盘无用文件清理工具')
    parser.add_argument('--dry-run', '-d', action='store_true', help='模拟清理，不实际删除文件')
    args = parser.parse_args()
    
    cleaner = DiskCleanerCleanup()
    
    if args.dry_run:
        cleaner.dry_run()
    else:
        # 确认清理
        confirm = input("\n警告: 此操作将永久删除文件。是否继续？(y/n): ")
        if confirm.lower() == 'y':
            cleaner.cleanup()
        else:
            print("清理操作已取消")

if __name__ == '__main__':
    main()
