"""
北京邮电大学本科教学管理系统 - 网络客户端启动程序
支持连接到远程服务器
"""

import sys
import os
from pathlib import Path

# 设置标准输出编码为UTF-8（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import Logger
from utils.config_manager import Config
from network.client import Client
import customtkinter as ctk
from tkinter import messagebox


def setup_environment():
    """设置运行环境"""
    # 创建必要的目录
    directories = ['logs', 'data', 'exports', 'config', 'assets', 'assets/icons']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 初始化日志系统
    Logger.init()
    Logger.info("=" * 60)
    Logger.info("北京邮电大学教学管理系统客户端启动")
    Logger.info("=" * 60)
    
    # 加载配置
    try:
        Config.load('config/config.yaml')
        Logger.info("配置文件加载成功")
    except Exception as e:
        Logger.error(f"配置文件加载失败: {e}")
        Logger.info("使用默认配置")


class ServerConnectDialog:
    """服务器连接对话框"""
    
    BUPT_BLUE = "#003087"
    BUPT_LIGHT_BLUE = "#0066CC"
    
    def __init__(self, root):
        """初始化连接对话框"""
        self.root = root
        self.root.title("连接到服务器 - 北京邮电大学教学管理系统")
        
        # 设置窗口大小和位置
        window_width = 700
        window_height = 650
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口不可调整大小
        self.root.resizable(False, False)
        
        self.client = None
        self.connected = False
        
        # 创建界面
        self.create_widgets()
        
        Logger.info("服务器连接对话框初始化完成")
    
    def create_widgets(self):
        """创建界面组件"""
        # 主容器 - 使用白色背景
        main_frame = ctk.CTkFrame(self.root, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 顶部标题区域 - 蓝色背景
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=120)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # 标题
        title_label = ctk.CTkLabel(
            header_frame,
            text="🌐 连接到服务器",
            font=("Microsoft YaHei UI", 32, "bold"),
            text_color="white",
            fg_color="transparent"
        )
        title_label.pack(pady=(25, 5))
        
        subtitle_label = ctk.CTkLabel(
            header_frame,
            text="请输入服务器地址和端口信息",
            font=("Microsoft YaHei UI", 14),
            text_color="white",
            fg_color="transparent"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=50, pady=40)
        
        # 表单容器
        form_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        
        # 服务器地址输入区域
        host_section = ctk.CTkFrame(form_frame, fg_color="transparent")
        host_section.pack(fill="x", pady=(0, 25))
        
        host_label = ctk.CTkLabel(
            host_section,
            text="服务器地址",
            font=("Microsoft YaHei UI", 15, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        host_label.pack(fill="x", pady=(0, 8))
        
        self.host_entry = ctk.CTkEntry(
            host_section,
            height=50,
            font=("Microsoft YaHei UI", 15),
            placeholder_text="例如: 10.29.100.39 或 localhost",
            border_color="#CCCCCC",
            border_width=1,
            fg_color="white",
            text_color="black"
        )
        self.host_entry.pack(fill="x", pady=(0, 8))
        
        # 提示信息框
        hint_frame = ctk.CTkFrame(
            host_section,
            fg_color="#F0F7FF",
            corner_radius=5
        )
        hint_frame.pack(fill="x", pady=(0, 0))
        
        host_hint = ctk.CTkLabel(
            hint_frame,
            text="💡 本机测试: localhost 或 127.0.0.1\n   局域网测试: 输入服务器显示的IP地址（如 10.29.100.39）",
            font=("Microsoft YaHei UI", 12),
            text_color="#555555",
            justify="left",
            anchor="w",
            fg_color="transparent"
        )
        host_hint.pack(fill="x", padx=12, pady=10)
        
        # 端口输入区域
        port_section = ctk.CTkFrame(form_frame, fg_color="transparent")
        port_section.pack(fill="x", pady=(0, 30))
        
        port_label = ctk.CTkLabel(
            port_section,
            text="端口号",
            font=("Microsoft YaHei UI", 15, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        port_label.pack(fill="x", pady=(0, 8))
        
        self.port_entry = ctk.CTkEntry(
            port_section,
            height=50,
            font=("Microsoft YaHei UI", 15),
            placeholder_text="默认: 8888",
            border_color="#CCCCCC",
            border_width=1,
            fg_color="white",
            text_color="black"
        )
        self.port_entry.insert(0, "8888")  # 默认端口
        self.port_entry.pack(fill="x", pady=(0, 8))
        
        port_hint_frame = ctk.CTkFrame(
            port_section,
            fg_color="#F0F7FF",
            corner_radius=5
        )
        port_hint_frame.pack(fill="x")
        
        port_hint = ctk.CTkLabel(
            port_hint_frame,
            text="💡 使用服务器启动时显示的端口号（默认: 8888）",
            font=("Microsoft YaHei UI", 12),
            text_color="#555555",
            anchor="w",
            fg_color="transparent"
        )
        port_hint.pack(fill="x", padx=12, pady=10)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        # 连接按钮 - 主要按钮，更大更醒目
        connect_button = ctk.CTkButton(
            button_frame,
            text="🔗 连接服务器",
            height=55,
            font=("Microsoft YaHei UI", 18, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            text_color="white",
            corner_radius=8,
            command=self.do_connect
        )
        connect_button.pack(fill="x", pady=(0, 15))
        
        # 分隔线
        separator = ctk.CTkFrame(
            button_frame,
            fg_color="#E0E0E0",
            height=1
        )
        separator.pack(fill="x", pady=(0, 15))
        
        # 本地模式按钮 - 次要按钮
        local_button = ctk.CTkButton(
            button_frame,
            text="💻 本地模式（使用本地数据库）",
            height=50,
            font=("Microsoft YaHei UI", 15),
            fg_color="#6C757D",
            hover_color="#5A6268",
            text_color="white",
            corner_radius=8,
            command=self.use_local_mode
        )
        local_button.pack(fill="x")
        
        # 绑定回车键
        self.host_entry.bind('<Return>', lambda e: self.port_entry.focus())
        self.port_entry.bind('<Return>', lambda e: self.do_connect())
        
        # 聚焦到服务器地址输入框
        self.host_entry.focus()
    
    def do_connect(self):
        """执行连接"""
        host = self.host_entry.get().strip()
        port_str = self.port_entry.get().strip()
        
        if not host:
            messagebox.showwarning("提示", "请输入服务器地址")
            self.host_entry.focus()
            return
        
        if not port_str:
            messagebox.showwarning("提示", "请输入端口号")
            self.port_entry.focus()
            return
        
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                raise ValueError("端口号超出范围")
        except ValueError:
            messagebox.showerror("错误", "端口号必须是1-65535之间的整数")
            self.port_entry.focus()
            return
        
        # 显示加载状态
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            Logger.info(f"正在连接服务器: {host}:{port}")
            
            # 创建客户端并连接
            self.client = Client(host=host, port=port, timeout=10)
            success, message = self.client.connect()
            
            if success:
                Logger.info(f"连接服务器成功: {host}:{port}")
                self.connected = True
                
                # 关闭连接对话框
                self.root.withdraw()
                
                # 打开登录窗口
                self.open_login_window()
            else:
                Logger.error(f"连接服务器失败: {message}")
                messagebox.showerror(
                    "连接失败",
                    f"无法连接到服务器 {host}:{port}\n\n"
                    f"错误信息: {message}\n\n"
                    f"故障排查：\n"
                    f"1. 确认服务器已启动\n"
                    f"2. 确认服务器地址和端口正确\n"
                    f"3. 检查防火墙设置\n"
                    f"4. 确认两台电脑在同一网络"
                )
        except Exception as e:
            Logger.error(f"连接异常: {e}", exc_info=True)
            messagebox.showerror("错误", f"连接过程出现异常：\n{str(e)}")
        finally:
            self.root.config(cursor="")
    
    def use_local_mode(self):
        """使用本地模式"""
        result = messagebox.askyesno(
            "本地模式",
            "您将使用本地数据库模式\n\n"
            "该模式下所有数据都存储在本地，\n"
            "无需连接服务器。\n\n"
            "是否继续？"
        )
        
        if result:
            Logger.info("用户选择本地模式")
            self.connected = False
            self.client = None
            
            # 关闭连接对话框
            self.root.withdraw()
            
            # 打开登录窗口（本地模式）
            self.open_login_window()
    
    def open_login_window(self):
        """打开登录窗口"""
        try:
            from gui.login_window import LoginWindow
            
            # 创建新窗口
            login_root = ctk.CTkToplevel(self.root)
            
            # 创建登录窗口
            login_app = LoginWindow(login_root)
            
            # 如果是网络模式，替换数据库为网络客户端适配器
            if self.client:
                from network_login import NetworkDatabaseAdapter
                adapter = NetworkDatabaseAdapter(self.client)
                login_app.db = adapter
                login_app.user_manager.db = adapter
                Logger.info("已切换到网络模式")
            
            # 设置关闭事件
            def on_login_close():
                if messagebox.askokcancel("退出", "确定要退出系统吗？"):
                    Logger.info("用户关闭登录窗口")
                    # 断开客户端连接
                    if self.client:
                        self.client.disconnect()
                    login_root.destroy()
                    self.root.quit()
            
            login_root.protocol("WM_DELETE_WINDOW", on_login_close)
            
        except Exception as e:
            Logger.error(f"打开登录窗口失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"打开登录窗口失败：\n{str(e)}")
            self.root.deiconify()
    
    def on_close(self):
        """关闭窗口"""
        if messagebox.askokcancel("退出", "确定要退出吗？"):
            Logger.info("用户关闭连接对话框")
            if self.client:
                self.client.disconnect()
            self.root.quit()


def main():
    """主函数"""
    try:
        # 设置环境
        setup_environment()
        
        # 设置customtkinter外观
        ctk.set_appearance_mode("light")  # 浅色模式（北邮主题）
        ctk.set_default_color_theme("blue")  # 蓝色主题
        
        print("=" * 70)
        print("🌐 北京邮电大学教学管理系统 - 网络客户端")
        print("=" * 70)
        print()
        print("欢迎使用！请在弹出的窗口中输入服务器信息")
        print()
        print("提示：")
        print("  • 本机测试: 使用 localhost 或 127.0.0.1")
        print("  • 局域网测试: 使用服务器启动时显示的IP地址")
        print("  • 默认端口: 8888")
        print("  • 或者选择\"本地模式\"直接使用本地数据库")
        print()
        print("=" * 70)
        print()
        
        # 创建主窗口
        root = ctk.CTk()
        
        # 创建连接对话框
        app = ServerConnectDialog(root)
        
        # 设置关闭事件
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        
        Logger.info("北京邮电大学教学管理系统客户端界面初始化完成")
        
        # 运行主循环
        root.mainloop()
        
    except KeyboardInterrupt:
        Logger.info("用户中断程序")
    except Exception as e:
        Logger.error(f"程序异常退出: {e}", exc_info=True)
        print(f"\n错误: {e}")
        print("程序异常退出，请查看日志文件 logs/app.log")
    finally:
        Logger.info("北京邮电大学教学管理系统客户端关闭")
        Logger.info("=" * 60)


if __name__ == "__main__":
    main()

