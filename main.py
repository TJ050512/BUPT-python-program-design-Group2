"""
北京邮电大学本科教学管理系统 - 主程序入口
Python课程实践项目
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import Logger
from utils.config_manager import Config
from gui.login_window import LoginWindow
import customtkinter as ctk


def setup_environment():
    """设置运行环境"""
    # 创建必要的目录
    directories = ['logs', 'data', 'exports', 'config', 'assets', 'assets/icons']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 初始化日志系统
    Logger.init()
    Logger.info("=" * 60)
    Logger.info("北京邮电大学教学管理系统启动")
    Logger.info("=" * 60)
    
    # 加载配置
    try:
        Config.load('config/config.yaml')
        Logger.info("配置文件加载成功")
    except Exception as e:
        Logger.error(f"配置文件加载失败: {e}")
        Logger.info("使用默认配置")


def main():
    """主函数"""
    try:
        # 设置环境
        setup_environment()
        
        # 设置customtkinter外观
        ctk.set_appearance_mode("light")  # 浅色模式（北邮主题）
        ctk.set_default_color_theme("blue")  # 蓝色主题
        
        # 创建主窗口
        root = ctk.CTk()
        
        # 创建登录窗口
        app = LoginWindow(root)
        
        # 设置关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        
        Logger.info("北京邮电大学教学管理系统界面初始化完成")
        
        # 运行主循环
        root.mainloop()
        
    except KeyboardInterrupt:
        Logger.info("用户中断程序")
    except Exception as e:
        Logger.error(f"程序异常退出: {e}", exc_info=True)
    finally:
        Logger.info("北京邮电大学教学管理系统关闭")
        Logger.info("=" * 60)


if __name__ == "__main__":
    main()

