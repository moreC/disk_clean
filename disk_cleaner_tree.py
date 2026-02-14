#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import shutil
import zipfile
from datetime import datetime

class DiskCleanerTree:
    def __init__(self):
        self.total_size = 0
        self.max_depth = 3
    
    def get_human_readable_size(self, size):
        """获取人类可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    
    def get_dir_size(self, path):
        """计算目录大小"""
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    try:
                        total += entry.stat().st_size
                    except:
                        pass
                elif entry.is_dir():
                    try:
                        total += self.get_dir_size(entry.path)
                    except:
                        pass
        except Exception as e:
            print(f"无法访问目录: {path} - {str(e)}")
        return total
    
    def print_tree(self, path, prefix="", depth=0):
        """打印目录树"""
        if depth > self.max_depth:
            return
        
        try:
            entries = []
            for entry in os.scandir(path):
                if entry.is_dir():
                    try:
                        size = self.get_dir_size(entry.path)
                        entries.append((entry.name, size, True))
                    except:
                        pass
                elif entry.is_file():
                    try:
                        size = entry.stat().st_size
                        entries.append((entry.name, size, False))
                    except:
                        pass
            
            # 按大小排序
            entries.sort(key=lambda x: x[1], reverse=True)
            
            count = len(entries)
            for i, (name, size, is_dir) in enumerate(entries):
                is_last = i == count - 1
                connector = "└── " if is_last else "├── "
                
                print(f"{prefix}{connector}{name} ({self.get_human_readable_size(size)})")
                
                if is_dir and depth < self.max_depth:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    self.print_tree(os.path.join(path, name), new_prefix, depth + 1)
                    
        except Exception as e:
            print(f"遍历目录失败: {path} - {str(e)}")
    
    def find_large_dirs(self, path, min_size=2*1024*1024*1024, depth=0):
        """查找大于指定大小的目录"""
        large_dirs = []
        
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    try:
                        size = self.get_dir_size(entry.path)
                        if size >= min_size:
                            large_dirs.append((entry.path, size))
                        
                        # 递归查找子目录
                        sub_large = self.find_large_dirs(entry.path, min_size, depth + 1)
                        large_dirs.extend(sub_large)
                    except:
                        pass
        except Exception as e:
            print(f"遍历目录失败: {path} - {str(e)}")
        
        return large_dirs
    
    def archive_dir(self, dir_path, output_dir):
        """归档目录为zip文件"""
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成归档文件名
            dir_name = os.path.basename(dir_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"{dir_name}_{timestamp}.zip"
            zip_path = os.path.join(output_dir, zip_filename)
            
            print(f"开始归档: {dir_path}")
            print(f"输出文件: {zip_path}")
            
            # 创建zip文件
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, dir_path)
                        zipf.write(file_path, arcname)
            
            print(f"归档完成: {zip_path}")
            return zip_path
        except Exception as e:
            print(f"归档失败: {dir_path} - {str(e)}")
            return None
    
    def generate_tree(self, root_path, max_depth=3):
        """生成目录树"""
        print(f"开始生成目录树: {root_path}")
        print(f"最大深度: {max_depth}")
        print("=" * 80)
        
        self.max_depth = max_depth
        
        # 计算根目录大小
        root_size = self.get_dir_size(root_path)
        print(f"{os.path.basename(root_path) or root_path} ({self.get_human_readable_size(root_size)})")
        
        # 打印子目录树
        self.print_tree(root_path, "", 1)
        
        print("=" * 80)
        print("目录树生成完成")
    
    def process_large_dirs(self, root_path, min_size_gb=2, archive=False, output_dir="./archives"):
        """处理大于指定大小的目录"""
        min_size = min_size_gb * 1024 * 1024 * 1024
        
        print(f"开始查找大于 {min_size_gb}GB 的目录...")
        print(f"搜索路径: {root_path}")
        print("=" * 80)
        
        large_dirs = self.find_large_dirs(root_path, min_size)
        
        if not large_dirs:
            print("未找到大于指定大小的目录")
            return
        
        print(f"找到 {len(large_dirs)} 个大于 {min_size_gb}GB 的目录:")
        print("-" * 80)
        
        for dir_path, size in large_dirs:
            print(f"{dir_path} ({self.get_human_readable_size(size)})")
        
        if archive:
            print("\n开始归档...")
            print("-" * 80)
            
            for dir_path, size in large_dirs:
                self.archive_dir(dir_path, output_dir)
            
            print("\n归档完成！")

def main():
    parser = argparse.ArgumentParser(description='C盘目录大小树形结构生成工具')
    parser.add_argument('--path', '-p', type=str, default='C:\\', help='根目录路径')
    parser.add_argument('--depth', '-d', type=int, default=3, help='最大显示深度')
    parser.add_argument('--find-large', '-f', action='store_true', help='查找大于指定大小的目录')
    parser.add_argument('--min-size', '-m', type=float, default=2.0, help='最小目录大小(GB)')
    parser.add_argument('--archive', '-a', action='store_true', help='归档找到的大目录')
    parser.add_argument('--output-dir', '-o', type=str, default='./archives', help='归档输出目录')
    args = parser.parse_args()
    
    tree_generator = DiskCleanerTree()
    
    if args.find_large:
        tree_generator.process_large_dirs(args.path, args.min_size, args.archive, args.output_dir)
    else:
        tree_generator.generate_tree(args.path, args.depth)

if __name__ == '__main__':
    main()
