#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

def create_scheduled_task():
    """创建Windows定时任务"""
    
    task_name = "DiskFileCheck"
    script_path = os.path.abspath("disk_checker.py")
    python_path = sys.executable
    
    # 创建任务的命令
    command = [
        "schtasks",
        "/create",
        "/tn", task_name,
        "/tr", f'"{python_path}" "{script_path}"',
        "/sc", "daily",
        "/st", "20:00",
        "/f"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("定时任务创建成功!")
            print(f"任务名称: {task_name}")
            print(f"执行时间: 每天 20:00")
            print(f"执行脚本: {script_path}")
            return True
        else:
            print(f"创建失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"创建失败: {str(e)}")
        return False

def delete_scheduled_task():
    """删除定时任务"""
    task_name = "DiskFileCheck"
    
    command = ["schtasks", "/delete", "/tn", task_name, "/f"]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("定时任务已删除")
            return True
        else:
            print(f"删除失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"删除失败: {str(e)}")
        return False

def query_scheduled_task():
    """查询定时任务"""
    task_name = "DiskFileCheck"
    
    command = ["schtasks", "/query", "/tn", task_name, "/fo", "list"]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("定时任务信息:")
            print(result.stdout)
            return True
        else:
            print("定时任务不存在")
            return False
    except Exception as e:
        print(f"查询失败: {str(e)}")
        return False

def run_now():
    """立即运行任务"""
    task_name = "DiskFileCheck"
    
    command = ["schtasks", "/run", "/tn", task_name]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print("任务已启动")
            return True
        else:
            print(f"启动失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"启动失败: {str(e)}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="定时任务管理工具")
    parser.add_argument("--create", action="store_true", help="创建定时任务")
    parser.add_argument("--delete", action="store_true", help="删除定时任务")
    parser.add_argument("--query", action="store_true", help="查询定时任务")
    parser.add_argument("--run", action="store_true", help="立即运行任务")
    
    args = parser.parse_args()
    
    if args.create:
        create_scheduled_task()
    elif args.delete:
        delete_scheduled_task()
    elif args.query:
        query_scheduled_task()
    elif args.run:
        run_now()
    else:
        print("请指定操作: --create, --delete, --query, --run")
        print("示例:")
        print("  python task_manager.py --create  # 创建定时任务")
        print("  python task_manager.py --query   # 查询定时任务")
        print("  python task_manager.py --run     # 立即运行任务")
        print("  python task_manager.py --delete  # 删除定时任务")
