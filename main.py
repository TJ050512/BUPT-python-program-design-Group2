"""
北京邮电大学教学管理系统 - 主程序入口
Main Entry Point for BUPT Teaching Management System
"""

import sys
import customtkinter as ctk
from gui.login_window import LoginWindow
from utils.logger import Logger
import os
import re

def main():
    """主函数"""
    try:
        # 可选命令行参数：设置当前学期（例如 2024-2025-1 / 2024-2025-2）
        # 用法: python main.py 2024-2025-1
        current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
        if len(sys.argv) > 1:
            sem_arg = sys.argv[1].strip()
            if re.match(r"^\d{4}-\d{4}-(1|2)$", sem_arg):
                current_semester = sem_arg
                os.environ["CURRENT_SEMESTER"] = current_semester
            else:
                Logger.warning(f"学期参数格式不正确，已忽略: {sem_arg}，示例: 2024-2025-1")
        else:
            # 若未传参但环境变量未设，仍使用默认值
            os.environ.setdefault("CURRENT_SEMESTER", current_semester)

        # 设置CustomTkinter外观
        ctk.set_appearance_mode("light")  # 亮色模式
        ctk.set_default_color_theme("blue")  # 蓝色主题
        
        Logger.info("=" * 80)
        Logger.info("北京邮电大学教学管理系统启动")
        Logger.info(f"当前学期: {os.getenv('CURRENT_SEMESTER')}")
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
