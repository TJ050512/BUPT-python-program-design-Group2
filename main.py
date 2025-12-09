#!/usr/bin/env python3
"""
北京邮电大学教学管理系统 - 主程序入口
Main Entry Point for BUPT Teaching Management System
"""

import sys
import customtkinter as ctk
from gui.login_window import LoginWindow
from utils.logger import Logger

def main():
    """主函数"""
    try:
        # 设置CustomTkinter外观
        ctk.set_appearance_mode("light")  # 亮色模式
        ctk.set_default_color_theme("blue")  # 蓝色主题
        
        Logger.info("=" * 80)
        Logger.info("北京邮电大学教学管理系统启动")
        Logger.info("=" * 80)
        
        # 创建根窗口
        root = ctk.CTk()
        
        # 创建登录窗口
        app = LoginWindow(root)
        
        # 运行主循环
        root.mainloop()
        
        Logger.info("系统正常关闭")
        
    except KeyboardInterrupt:
        Logger.info("用户中断程序")
        sys.exit(0)
    except Exception as e:
        Logger.error(f"系统启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
