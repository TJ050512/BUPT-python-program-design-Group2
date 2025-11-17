@echo off
chcp 65001 >nul
title 北京邮电大学教学管理系统 - 客户端

echo ================================================================
echo 北京邮电大学本科教学管理系统 - 网络客户端
echo ================================================================
echo.
echo 正在启动客户端程序...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8或更高版本
    echo.
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM 启动客户端
python 启动客户端.py

if errorlevel 1 (
    echo.
    echo [错误] 客户端启动失败
    echo.
    echo 故障排查:
    echo   1. 确认已安装所有依赖: pip install -r requirements.txt
    echo   2. 查看日志文件: logs\app.log
    echo   3. 确认Python版本 ^>= 3.8
    echo.
    pause
)

exit /b 0

