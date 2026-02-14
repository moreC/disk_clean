@echo off
echo ========================================
echo C盘大文件检查 - 定时任务脚本
echo ========================================
echo.

REM 设置Python路径
set PYTHON_PATH=python

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0

REM 切换到脚本目录
cd /d "%SCRIPT_DIR%"

REM 运行大文件检查
echo [%date% %time%] 开始执行大文件检查...
%PYTHON_PATH% disk_checker.py
echo [%date% %time%] 检查完成!
echo.

REM 显示日志目录
echo 日志文件保存在: %SCRIPT_DIR%logs\
echo 数据文件保存在: %SCRIPT_DIR%data\
echo.

pause
