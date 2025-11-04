"""
登录窗口 - 北京邮电大学教学管理系统
支持学生和教师登录
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from PIL import Image
from utils.logger import Logger
from utils.crypto import CryptoUtil
from data.database import get_database
from core.user_manager import UserManager


class LoginWindow:
    """登录窗口类"""
    
    # 北邮蓝色主题
    BUPT_BLUE = "#003087"
    BUPT_LIGHT_BLUE = "#0066CC"
    
    def __init__(self, root):
        """
        初始化登录窗口
        
        Args:
            root: 主窗口对象
        """
        self.root = root
        self.root.title("北京邮电大学本科教学管理系统")
        
        # 设置窗口大小和位置
        window_width = 800
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 设置窗口不可调整大小
        self.root.resizable(False, False)
        
        # 初始化数据库和用户管理器
        self.db = get_database()
        self.db.init_demo_data()  # 初始化演示数据
        self.user_manager = UserManager(self.db)
        
        # 创建界面
        self.create_widgets()
        
        Logger.info("登录窗口初始化完成")
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 主容器
        main_frame = ctk.CTkFrame(self.root, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 左侧 - 北邮Logo和标题区
        left_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, width=350)
        left_frame.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        left_frame.pack_propagate(False)
        
        # Logo占位（如果有logo图片，可以在这里加载）
        try:
            logo_path = Path("assets/icons/bupt_logo.png")
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                logo_ctk_image = ctk.CTkImage(
                    light_image=logo_image,
                    dark_image=logo_image,
                    size=(120, 120)
                )
                logo_label = ctk.CTkLabel(
                    left_frame,
                    image=logo_ctk_image,
                    text="",
                    fg_color="transparent"
                )
                logo_label.pack(pady=(80, 20))
                Logger.info("校徽图片加载成功")
            else:
                # 如果没有图片，使用emoji占位
                logo_label = ctk.CTkLabel(
                    left_frame,
                    text="🎓",
                    font=("Microsoft YaHei UI", 80),
                    text_color="white",
                    fg_color="transparent"
                )
                logo_label.pack(pady=(80, 20))
        except Exception as e:
            Logger.warning(f"校徽图片加载失败，使用emoji: {e}")
            logo_label = ctk.CTkLabel(
                left_frame,
                text="🎓",
                font=("Microsoft YaHei UI", 80),
                text_color="white",
                fg_color="transparent"
            )
            logo_label.pack(pady=(80, 20))
        
        # 系统标题
        title_label = ctk.CTkLabel(
            left_frame,
            text="北京邮电大学",
            font=("Microsoft YaHei UI", 32, "bold"),
            text_color="white",
            fg_color="transparent"
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ctk.CTkLabel(
            left_frame,
            text="本科教学管理系统",
            font=("Microsoft YaHei UI", 20),
            text_color="white",
            fg_color="transparent"
        )
        subtitle_label.pack(pady=(0, 20))
        
        # 版本信息
        version_label = ctk.CTkLabel(
            left_frame,
            text="Teaching Management System v1.2",
            font=("Microsoft YaHei UI", 12),
            text_color="white",
            fg_color="transparent"
        )
        version_label.pack(side="bottom", pady=20)
        
        # 右侧 - 登录表单区
        right_frame = ctk.CTkFrame(main_frame, fg_color="white")
        right_frame.pack(side="right", fill="both", expand=True, padx=40, pady=60)
        
        # 登录表单容器
        form_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        form_frame.pack(expand=True)
        
        # 标题
        login_title = ctk.CTkLabel(
            form_frame,
            text="欢迎登录",
            font=("Microsoft YaHei UI", 28, "bold"),
            text_color=self.BUPT_BLUE
        )
        login_title.pack(pady=(0, 10))
        
        login_subtitle = ctk.CTkLabel(
            form_frame,
            text="请输入您的学号/工号和密码",
            font=("Microsoft YaHei UI", 13),
            text_color="gray"
        )
        login_subtitle.pack(pady=(0, 40))
        
        # 用户类型选择
        type_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=(0, 20))
        
        self.user_type_var = ctk.StringVar(value="student")
        
        student_radio = ctk.CTkRadioButton(
            type_frame,
            text="学生",
            variable=self.user_type_var,
            value="student",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE
        )
        student_radio.pack(side="left", padx=(0, 30))
        
        teacher_radio = ctk.CTkRadioButton(
            type_frame,
            text="教师",
            variable=self.user_type_var,
            value="teacher",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE
        )
        teacher_radio.pack(side="left")
        
        # 用户名输入
        username_label = ctk.CTkLabel(
            form_frame,
            text="账号",
            font=("Microsoft YaHei UI", 14),
            text_color="gray",
            anchor="w"
        )
        username_label.pack(fill="x", pady=(0, 5))
        
        self.username_entry = ctk.CTkEntry(
            form_frame,
            height=45,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入学号或工号",
            border_color=self.BUPT_BLUE,
            fg_color="white"
        )
        self.username_entry.pack(fill="x", pady=(0, 20))
        
        # 密码输入
        password_label = ctk.CTkLabel(
            form_frame,
            text="密码",
            font=("Microsoft YaHei UI", 14),
            text_color="gray",
            anchor="w"
        )
        password_label.pack(fill="x", pady=(0, 5))
        
        self.password_entry = ctk.CTkEntry(
            form_frame,
            height=45,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入密码",
            show="●",
            border_color=self.BUPT_BLUE,
            fg_color="white"
        )
        self.password_entry.pack(fill="x", pady=(0, 30))
        
        # 绑定回车键登录
        self.password_entry.bind('<Return>', lambda e: self.do_login())
        
        # 登录按钮
        login_button = ctk.CTkButton(
            form_frame,
            text="登 录",
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=self.do_login
        )
        login_button.pack(fill="x", pady=(0, 15))
        
    def do_login(self):
        """执行登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("提示", "请输入完整的登录信息")
            return
        
        # 显示加载状态
        self.root.config(cursor="wait")
        self.root.update()
        
        try:
            # 调用用户管理器登录
            success, user, message = self.user_manager.login(username, password)
            
            if success:
                Logger.info(f"用户登录成功: {user.name} ({user.user_type})")
                
                # 关闭登录窗口
                self.root.withdraw()
                
                # 根据用户类型打开对应的主窗口
                if user.is_student():
                    self.open_student_window(user)
                else:
                    self.open_teacher_window(user)
            else:
                messagebox.showerror("登录失败", message)
                self.password_entry.delete(0, 'end')
        
        except Exception as e:
            Logger.error(f"登录异常: {e}")
            messagebox.showerror("错误", "登录过程出现异常，请稍后重试")
        
        finally:
            self.root.config(cursor="")
    
    def open_student_window(self, user):
        """打开学生端主窗口"""
        try:
            from gui.student_window import StudentWindow
            
            # 创建新窗口
            student_win = ctk.CTkToplevel(self.root)
            StudentWindow(student_win, user, self.db, self.on_logout)
            
        except Exception as e:
            Logger.error(f"打开学生窗口失败: {e}")
            messagebox.showerror("错误", "打开学生窗口失败")
            self.root.deiconify()
    
    def open_teacher_window(self, user):
        """打开教师端主窗口"""
        try:
            from gui.teacher_window import TeacherWindow
            
            # 创建新窗口
            teacher_win = ctk.CTkToplevel(self.root)
            TeacherWindow(teacher_win, user, self.db, self.on_logout)
            
        except Exception as e:
            Logger.error(f"打开教师窗口失败: {e}")
            messagebox.showerror("错误", "打开教师窗口失败")
            self.root.deiconify()
    
    def on_logout(self):
        """注销回调"""
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.root.deiconify()
        Logger.info("用户已注销")
    
    def on_close(self):
        """关闭窗口"""
        if messagebox.askokcancel("退出", "确定要退出系统吗？"):
            Logger.info("用户关闭登录窗口")
            self.root.quit()


if __name__ == "__main__":
    # 测试登录窗口
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    app = LoginWindow(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
