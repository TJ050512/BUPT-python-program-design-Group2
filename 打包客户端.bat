@echo off
REM 打包客户端为exe文件
chcp 65001 >nul 2>&1
title Build Client Executable

echo ================================================================
echo Building BUPT Teaching System Client Executable
echo ================================================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python first.
    pause
    exit /b 1
)

REM 检查PyInstaller是否安装
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    echo.
)

echo Building executable...
echo.

REM 打包客户端
pyinstaller --name="BUPT客户端" ^
    --onefile ^
    --windowed ^
    --icon=assets/icons/bupt_logo.png ^
    --add-data "gui;gui" ^
    --add-data "core;core" ^
    --add-data "network;network" ^
    --add-data "utils;utils" ^
    --add-data "data;data" ^
    --add-data "config;config" ^
    --add-data "assets;assets" ^
    --hidden-import=customtkinter ^
    --hidden-import=PIL ^
    --hidden-import=bcrypt ^
    --hidden-import=yaml ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=matplotlib ^
    --hidden-import=seaborn ^
    --hidden-import=openpyxl ^
    --hidden-import=colorlog ^
    --hidden-import=dateutil ^
    --collect-all customtkinter ^
    --collect-all PIL ^
    启动客户端.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Build completed!
echo ================================================================
echo.
echo Executable location: dist\BUPT客户端.exe
echo.
echo You can now distribute this exe file without Python installation.
echo.
pause

