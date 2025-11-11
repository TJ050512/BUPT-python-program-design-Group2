"""
登录窗口 - 北京邮电大学教学管理系统
支持学生和教师登录
"""

import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
from PIL import Image
from typing import Optional, Dict
from utils.logger import Logger
from utils.crypto import CryptoUtil
from data.database import get_database
from core.user_manager import UserManager
from utils.validator import Validator


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
            text="请输入您的账号和密码",
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
        student_radio.pack(side="left", padx=(0, 20))
        
        teacher_radio = ctk.CTkRadioButton(
            type_frame,
            text="教师",
            variable=self.user_type_var,
            value="teacher",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE
        )
        teacher_radio.pack(side="left", padx=(0, 20))
        
        admin_radio = ctk.CTkRadioButton(
            type_frame,
            text="管理员",
            variable=self.user_type_var,
            value="admin",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE
        )
        admin_radio.pack(side="left")
        
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
            placeholder_text="请输入账号（学号/工号/管理员ID）",
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
        
        # 忘记密码链接
        forgot_password_label = ctk.CTkLabel(
            form_frame,
            text="忘记密码？",
            font=("Microsoft YaHei UI", 12),
            text_color=self.BUPT_BLUE,
            cursor="hand2"
        )
        forgot_password_label.pack(pady=(0, 10))
        forgot_password_label.bind("<Button-1>", lambda e: self.show_forgot_password_dialog())
        
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
            # 获取用户类型
            user_type = self.user_type_var.get()
            
            # 调用用户管理器登录
            success, user, message = self.user_manager.login(username, password, user_type)
            
            if success:
                Logger.info(f"用户登录成功: {user.name} ({user.user_type})")
                
                # 检查是否为默认密码（仅学生和教师）
                if (user.is_student() or user.is_teacher()) and \
                   self.user_manager.is_default_password(password, user.user_type):
                    # 显示修改密码提醒对话框（非强制）
                    self.show_change_password_dialog(user, password)
                    # 无论用户选择修改还是跳过，都允许登录
                
                # 关闭登录窗口
                self.root.withdraw()
                
                # 根据用户类型打开对应的主窗口
                if user.is_student():
                    self.open_student_window(user)
                elif user.is_admin():
                    self.open_admin_window(user)
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
    
    def open_admin_window(self, user):
        """打开管理员端主窗口"""
        try:
            from gui.admin_window import AdminWindow
            
            # 创建新窗口
            admin_win = ctk.CTkToplevel(self.root)
            AdminWindow(admin_win, user, self.db, self.on_logout)
            
        except Exception as e:
            Logger.error(f"打开管理员窗口失败: {e}")
            messagebox.showerror("错误", "打开管理员窗口失败")
            self.root.deiconify()
    
    def show_change_password_dialog(self, user, current_password):
        """显示修改密码提醒对话框（非强制）"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("安全提醒")
        dialog.geometry("500x500")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"500x500+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color="#FFA500", height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="⚠️ 安全提醒",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # 提示信息
        warning_label = ctk.CTkLabel(
            content_frame,
            text="检测到您正在使用默认密码，为了账户安全，\n建议您修改密码！",
            font=("Microsoft YaHei UI", 14),
            text_color="#FF8C00",
            justify="center"
        )
        warning_label.pack(pady=(0, 20))
        
        # 用户信息
        user_info_label = ctk.CTkLabel(
            content_frame,
            text=f"用户：{user.name} ({user.id})",
            font=("Microsoft YaHei UI", 12),
            text_color="#666666"
        )
        user_info_label.pack(pady=(0, 30))
        
        # 新密码输入
        new_password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        new_password_frame.pack(fill="x", pady=10)
        
        new_password_label = ctk.CTkLabel(
            new_password_frame,
            text="新密码：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            width=100,
            anchor="w"
        )
        new_password_label.pack(side="left", padx=(0, 10))
        
        new_password_entry = ctk.CTkEntry(
            new_password_frame,
            width=300,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入新密码（6-20个字符）",
            show="●"
        )
        new_password_entry.pack(side="left", fill="x", expand=True)
        
        # 确认密码输入
        confirm_password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        confirm_password_frame.pack(fill="x", pady=10)
        
        confirm_password_label = ctk.CTkLabel(
            confirm_password_frame,
            text="确认密码：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            width=100,
            anchor="w"
        )
        confirm_password_label.pack(side="left", padx=(0, 10))
        
        confirm_password_entry = ctk.CTkEntry(
            confirm_password_frame,
            width=300,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请再次输入新密码",
            show="●"
        )
        confirm_password_entry.pack(side="left", fill="x", expand=True)
        
        # 密码要求提示
        password_hint = ctk.CTkLabel(
            content_frame,
            text="密码要求：6-20个字符，建议包含字母和数字",
            font=("Microsoft YaHei UI", 11),
            text_color="#999999"
        )
        password_hint.pack(pady=(10, 30))
        
        def confirm_change():
            new_password = new_password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            
            # 验证输入
            if not new_password:
                messagebox.showwarning("提示", "请输入新密码")
                new_password_entry.focus()
                return
            
            if not confirm_password:
                messagebox.showwarning("提示", "请确认新密码")
                confirm_password_entry.focus()
                return
            
            if new_password != confirm_password:
                messagebox.showerror("错误", "两次输入的密码不一致，请重新输入")
                new_password_entry.delete(0, 'end')
                confirm_password_entry.delete(0, 'end')
                new_password_entry.focus()
                return
            
            # 验证密码格式
            is_valid, error_msg = Validator.is_valid_password(new_password)
            if not is_valid:
                messagebox.showerror("错误", error_msg)
                new_password_entry.delete(0, 'end')
                confirm_password_entry.delete(0, 'end')
                new_password_entry.focus()
                return
            
            # 检查是否仍为默认密码
            if self.user_manager.is_default_password(new_password, user.user_type):
                messagebox.showerror("错误", "新密码不能与默认密码相同，请设置其他密码")
                new_password_entry.delete(0, 'end')
                confirm_password_entry.delete(0, 'end')
                new_password_entry.focus()
                return
            
            # 更新密码
            success, message = self.user_manager.update_password(
                user.id, user.user_type, new_password
            )
            
            if success:
                Logger.info(f"用户修改密码成功: {user.name} ({user.id})")
                messagebox.showinfo("成功", "密码修改成功！")
                dialog.destroy()
            else:
                messagebox.showerror("错误", message)
        
        def skip_change():
            """跳过修改密码"""
            dialog.destroy()
        
        # 按钮区域
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认修改",
            width=130,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_change
        )
        confirm_btn.pack(side="left", padx=(0, 10))
        
        skip_btn = ctk.CTkButton(
            button_frame,
            text="下次再修改",
            width=130,
            height=45,
            font=("Microsoft YaHei UI", 16),
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=skip_change
        )
        skip_btn.pack(side="left", padx=(0, 10))
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            width=100,
            height=45,
            font=("Microsoft YaHei UI", 16),
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=skip_change
        )
        cancel_btn.pack(side="left")
        
        # 绑定回车键
        new_password_entry.bind('<Return>', lambda e: confirm_password_entry.focus())
        confirm_password_entry.bind('<Return>', lambda e: confirm_change())
        
        # 聚焦到新密码输入框
        new_password_entry.focus()
        
        # 等待对话框关闭
        dialog.wait_window()
    
    def on_logout(self):
        """注销回调"""
        self.username_entry.delete(0, 'end')
        self.password_entry.delete(0, 'end')
        self.root.deiconify()
        Logger.info("用户已注销")
    
    def show_forgot_password_dialog(self):
        """显示忘记密码对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("找回密码")
        dialog.geometry("550x650")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f"550x650+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="找回密码",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域（可滚动）
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 步骤提示
        step_label = ctk.CTkLabel(
            content_frame,
            text="请填写以下信息以验证身份",
            font=("Microsoft YaHei UI", 14),
            text_color="gray"
        )
        step_label.pack(pady=(0, 10))
        
        # 管理员提示
        admin_warning_label = ctk.CTkLabel(
            content_frame,
            text="⚠️ 注意：管理员账号不支持密码重置功能",
            font=("Microsoft YaHei UI", 12),
            text_color="#FF6B6B"
        )
        admin_warning_label.pack(pady=(0, 20))
        
        # 用户类型选择
        type_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=(0, 20))
        
        user_type_var = ctk.StringVar(value="student")
        
        student_radio = ctk.CTkRadioButton(
            type_frame,
            text="学生",
            variable=user_type_var,
            value="student",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE
        )
        student_radio.pack(side="left", padx=(0, 20))
        
        teacher_radio = ctk.CTkRadioButton(
            type_frame,
            text="教师",
            variable=user_type_var,
            value="teacher",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE
        )
        teacher_radio.pack(side="left")
        
        # 账号输入
        account_label = ctk.CTkLabel(
            content_frame,
            text="账号（学号/工号）*",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        account_label.pack(fill="x", pady=(0, 5))
        
        account_entry = ctk.CTkEntry(
            content_frame,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入学号或工号"
        )
        account_entry.pack(fill="x", pady=(0, 15))
        
        # 姓名输入
        name_label = ctk.CTkLabel(
            content_frame,
            text="姓名 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        name_label.pack(fill="x", pady=(0, 5))
        
        name_entry = ctk.CTkEntry(
            content_frame,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入真实姓名"
        )
        name_entry.pack(fill="x", pady=(0, 15))
        
        # 手机号码输入
        phone_label = ctk.CTkLabel(
            content_frame,
            text="手机号码 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        phone_label.pack(fill="x", pady=(0, 5))
        
        phone_entry = ctk.CTkEntry(
            content_frame,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入注册时填写的手机号码"
        )
        phone_entry.pack(fill="x", pady=(0, 15))
        
        # 验证码输入区域
        code_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        code_frame.pack(fill="x", pady=(0, 15))
        
        code_label = ctk.CTkLabel(
            code_frame,
            text="验证码 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w",
            width=100
        )
        code_label.pack(side="left", padx=(0, 10))
        
        code_entry = ctk.CTkEntry(
            code_frame,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入验证码",
            width=200
        )
        code_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # 存储验证码
        verification_code = None
        code_sent = False
        
        def send_verification_code():
            """发送验证码"""
            nonlocal verification_code, code_sent
            
            account = account_entry.get().strip()
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            user_type = user_type_var.get()
            
            # 验证必填字段
            if not account:
                messagebox.showwarning("提示", "请输入账号")
                account_entry.focus()
                return
            
            if not name:
                messagebox.showwarning("提示", "请输入姓名")
                name_entry.focus()
                return
            
            if not phone:
                messagebox.showwarning("提示", "请输入手机号码")
                phone_entry.focus()
                return
            
            # 验证手机号格式
            if not phone.isdigit() or len(phone) != 11:
                messagebox.showerror("错误", "手机号码格式不正确，请输入11位数字")
                phone_entry.focus()
                return
            
            # 检查是否为管理员账号（管理员不支持密码重置）
            if account.startswith('admin'):
                messagebox.showerror("错误", "管理员账号不支持密码重置功能\n\n如需重置管理员密码，请联系系统管理员")
                return
            
            # 验证用户信息
            user_info = self._verify_user_info(account, name, phone, user_type)
            if not user_info:
                messagebox.showerror("错误", "账号、姓名或手机号码不匹配，请检查后重试")
                return
            
            # 生成6位数字验证码
            import random
            verification_code = str(random.randint(100000, 999999))
            code_sent = True
            
            # 模拟发送短信（实际应用中这里应该调用短信服务API）
            Logger.info(f"验证码已发送到 {phone}: {verification_code}")
            
            # 显示验证码（实际应用中应该通过短信发送，这里为了方便测试显示）
            messagebox.showinfo("验证码已发送", 
                f"验证码已发送到手机 {phone}\n\n"
                f"验证码：{verification_code}\n\n"
                f"（演示模式：实际应用中验证码将通过短信发送）")
            
            send_code_btn.configure(state="disabled", text=f"已发送（{verification_code}）")
            code_entry.focus()
        
        send_code_btn = ctk.CTkButton(
            code_frame,
            text="发送验证码",
            width=120,
            height=40,
            font=("Microsoft YaHei UI", 13),
            fg_color=self.BUPT_LIGHT_BLUE,
            hover_color=self.BUPT_BLUE,
            command=send_verification_code
        )
        send_code_btn.pack(side="left")
        
        # 新密码输入
        new_password_label = ctk.CTkLabel(
            content_frame,
            text="新密码 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        new_password_label.pack(fill="x", pady=(0, 5))
        
        new_password_entry = ctk.CTkEntry(
            content_frame,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入新密码（6-20个字符）",
            show="●"
        )
        new_password_entry.pack(fill="x", pady=(0, 15))
        
        # 确认密码输入
        confirm_password_label = ctk.CTkLabel(
            content_frame,
            text="确认新密码 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        confirm_password_label.pack(fill="x", pady=(0, 5))
        
        confirm_password_entry = ctk.CTkEntry(
            content_frame,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请再次输入新密码",
            show="●"
        )
        confirm_password_entry.pack(fill="x", pady=(0, 20))
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        def confirm_reset():
            """确认重置密码"""
            nonlocal verification_code, code_sent
            
            account = account_entry.get().strip()
            name = name_entry.get().strip()
            phone = phone_entry.get().strip()
            code = code_entry.get().strip()
            new_password = new_password_entry.get().strip()
            confirm_password = confirm_password_entry.get().strip()
            user_type = user_type_var.get()
            
            # 验证必填字段
            if not account or not name or not phone:
                messagebox.showwarning("提示", "请填写完整的身份信息")
                return
            
            if not code:
                messagebox.showwarning("提示", "请输入验证码")
                code_entry.focus()
                return
            
            if not new_password:
                messagebox.showwarning("提示", "请输入新密码")
                new_password_entry.focus()
                return
            
            if not confirm_password:
                messagebox.showwarning("提示", "请确认新密码")
                confirm_password_entry.focus()
                return
            
            # 验证验证码
            if not code_sent or code != verification_code:
                messagebox.showerror("错误", "验证码错误，请重新获取")
                code_entry.delete(0, 'end')
                code_entry.focus()
                return
            
            # 验证密码一致性
            if new_password != confirm_password:
                messagebox.showerror("错误", "两次输入的密码不一致")
                new_password_entry.delete(0, 'end')
                confirm_password_entry.delete(0, 'end')
                new_password_entry.focus()
                return
            
            # 验证密码格式
            is_valid, error_msg = Validator.is_valid_password(new_password)
            if not is_valid:
                messagebox.showerror("错误", error_msg)
                new_password_entry.delete(0, 'end')
                confirm_password_entry.delete(0, 'end')
                new_password_entry.focus()
                return
            
            # 再次检查是否为管理员账号
            if account.startswith('admin'):
                messagebox.showerror("错误", "管理员账号不支持密码重置功能\n\n如需重置管理员密码，请联系系统管理员")
                return
            
            # 再次验证用户信息
            user_info = self._verify_user_info(account, name, phone, user_type)
            if not user_info:
                messagebox.showerror("错误", "身份验证失败，请检查信息后重试")
                return
            
            # 重置密码
            success, message = self.user_manager.update_password(account, user_type, new_password)
            
            if success:
                Logger.info(f"用户通过忘记密码功能重置密码: {account} ({user_type})")
                messagebox.showinfo("成功", "密码重置成功！\n\n请使用新密码登录")
                dialog.destroy()
            else:
                messagebox.showerror("错误", message)
        
        def cancel_reset():
            """取消重置"""
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认重置",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_reset
        )
        confirm_btn.pack(side="right", padx=(10, 0))
        
        # 取消按钮
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            width=120,
            height=45,
            font=("Microsoft YaHei UI", 16),
            fg_color="#CCCCCC",
            hover_color="#BBBBBB",
            text_color="black",
            command=cancel_reset
        )
        cancel_btn.pack(side="right")
        
        # 绑定回车键
        account_entry.bind('<Return>', lambda e: name_entry.focus())
        name_entry.bind('<Return>', lambda e: phone_entry.focus())
        phone_entry.bind('<Return>', lambda e: send_verification_code())
        code_entry.bind('<Return>', lambda e: new_password_entry.focus())
        new_password_entry.bind('<Return>', lambda e: confirm_password_entry.focus())
        confirm_password_entry.bind('<Return>', lambda e: confirm_reset())
        
        # 聚焦到账号输入框
        account_entry.focus()
    
    def _verify_user_info(self, account: str, name: str, phone: str, user_type: str) -> Optional[Dict]:
        """
        验证用户信息（账号、姓名、手机号是否匹配）
        
        Args:
            account: 账号（学号/工号）
            name: 姓名
            phone: 手机号码
            user_type: 用户类型（student/teacher）
        
        Returns:
            用户信息字典，验证失败返回None
        """
        try:
            if user_type == 'student':
                sql = """
                    SELECT student_id, name, phone 
                    FROM students 
                    WHERE student_id = ? AND name = ? AND phone = ?
                """
            elif user_type == 'teacher':
                sql = """
                    SELECT teacher_id, name, phone 
                    FROM teachers 
                    WHERE teacher_id = ? AND name = ? AND phone = ?
                """
            else:
                return None
            
            result = self.db.execute_query(sql, (account, name, phone))
            
            if result and len(result) > 0:
                return result[0]
            return None
            
        except Exception as e:
            Logger.error(f"验证用户信息失败: {e}")
            return None
    
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
