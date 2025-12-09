"""
管理员端主窗口 - 北京邮电大学教学管理系统
提供用户管理、课程管理、系统设置等功能
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
from pathlib import Path
from PIL import Image
from utils.logger import Logger
from core.course_manager import CourseManager
from core.user_manager import UserManager
from core.enrollment_manager import EnrollmentManager
from core.points_manager import PointsManager
from core.bidding_manager import BiddingManager
from utils.crypto import CryptoUtil
import re
from datetime import datetime
from utils.config_manager import Config
import yaml


class AdminWindow:
    """管理员端主窗口类"""
    
    # 北邮蓝色主题
    BUPT_BLUE = "#003087"
    BUPT_LIGHT_BLUE = "#0066CC"
    
    def __init__(self, root, user, db, logout_callback):
        """
        初始化管理员端窗口
        
        Args:
            root: 窗口对象
            user: 用户对象
            db: 数据库实例
            logout_callback: 注销回调函数
        """
        self.root = root
        self.user = user
        self.db = db
        self.logout_callback = logout_callback
        
        # 初始化管理器
        self.course_manager = CourseManager(db)
        self.user_manager = UserManager(db)
        self.enrollment_manager = EnrollmentManager(db)
        self.points_manager = PointsManager(db)
        self.bidding_manager = BiddingManager(db, self.points_manager)
        
        # 设置窗口
        self.root.title(f"北京邮电大学教学管理系统 - 管理员端 - {user.name}")
        
        window_width = 1400
        window_height = 800
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建界面
        self.create_widgets()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        Logger.info(f"管理员端窗口打开: {user.name}")
    
    def enable_mousewheel_scroll(self, scrollable_frame):
        """为CTkScrollableFrame启用鼠标滚轮滚动"""
        def on_mousewheel(event):
            try:
                # CTkScrollableFrame内部有一个canvas，我们需要滚动它
                canvas = None
                
                # 方法1: 尝试访问_parent_canvas属性
                if hasattr(scrollable_frame, '_parent_canvas'):
                    canvas = scrollable_frame._parent_canvas
                # 方法2: 尝试访问_canvas属性
                elif hasattr(scrollable_frame, '_canvas'):
                    canvas = scrollable_frame._canvas
                # 方法3: 从子组件中查找Canvas
                else:
                    def find_canvas(widget):
                        if isinstance(widget, tk.Canvas):
                            return widget
                        for child in widget.winfo_children():
                            result = find_canvas(child)
                            if result:
                                return result
                        return None
                    canvas = find_canvas(scrollable_frame)
                
                if canvas and canvas.winfo_exists():
                    # 计算滚动量
                    scroll_amount = 0
                    if hasattr(event, 'delta'):
                        # Windows/Mac: delta是滚动的像素数，通常120的倍数
                        scroll_amount = int(-event.delta / 120)
                    elif event.num == 4:
                        # Linux向上滚动
                        scroll_amount = -1
                    elif event.num == 5:
                        # Linux向下滚动
                        scroll_amount = 1
                    
                    if scroll_amount != 0:
                        canvas.yview_scroll(scroll_amount, "units")
            except Exception:
                pass
        
        # 绑定鼠标滚轮事件
        scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        scrollable_frame.bind("<Button-4>", on_mousewheel)  # Linux向上滚动
        scrollable_frame.bind("<Button-5>", on_mousewheel)  # Linux向下滚动
        
        # 为所有子组件也绑定事件（确保鼠标在任何子组件上都能滚动）
        def bind_to_children(widget):
            try:
                widget.bind("<MouseWheel>", on_mousewheel)
                widget.bind("<Button-4>", on_mousewheel)
                widget.bind("<Button-5>", on_mousewheel)
                for child in widget.winfo_children():
                    bind_to_children(child)
            except Exception:
                pass
        
        bind_to_children(scrollable_frame)
    
    def create_widgets(self):
        """创建界面组件"""
        
        # 顶部导航栏
        top_frame = ctk.CTkFrame(self.root, height=70, fg_color=self.BUPT_BLUE)
        top_frame.pack(fill="x", side="top")
        top_frame.pack_propagate(False)
        
        # Logo和标题容器
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        
        # 尝试加载校徽
        try:
            logo_path = Path("assets/icons/bupt_logo.png")
            if logo_path.exists():
                logo_image = Image.open(logo_path)
                logo_ctk_image = ctk.CTkImage(
                    light_image=logo_image,
                    dark_image=logo_image,
                    size=(40, 40)
                )
                logo_label = ctk.CTkLabel(
                    title_frame,
                    image=logo_ctk_image,
                    text=""
                )
                logo_label.pack(side="left", padx=(0, 10))
        except Exception as e:
            Logger.warning(f"顶部校徽加载失败: {e}")
        
        # 标题
        title_label = ctk.CTkLabel(
            title_frame,
            text="北京邮电大学教学管理系统 - 管理员端",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color="white"
        )
        title_label.pack(side="left")
        
        # 用户信息
        user_info_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        user_info_frame.pack(side="right", padx=20)
        
        user_label = ctk.CTkLabel(
            user_info_frame,
            text=f"欢迎，{self.user.name} ({self.user.id})",
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color="white"
        )
        user_label.pack(side="left", padx=(0, 15))
        
        logout_button = ctk.CTkButton(
            user_info_frame,
            text="退出登录",
            width=100,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color="transparent",
            border_width=2,
            border_color="white",
            hover_color=self.BUPT_LIGHT_BLUE,
            corner_radius=8,
            command=self.do_logout
        )
        logout_button.pack(side="left")
        
        # 主容器
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True)
        
        # 左侧菜单
        left_menu = ctk.CTkFrame(main_container, width=220, fg_color="#F0F0F0")
        left_menu.pack(side="left", fill="y")
        left_menu.pack_propagate(False)
        
        menu_title = ctk.CTkLabel(
            left_menu,
            text="功能菜单",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color=self.BUPT_BLUE
        )
        menu_title.pack(pady=25)
        
        # 菜单按钮
        self.menu_buttons = []
        
        menus = [
            ("👥 用户管理", self.show_user_management),
            ("📚 课程管理", self.show_course_management),
            ("📊 数据统计", self.show_statistics),
            ("📝 系统日志", self.show_system_logs),
            ("⚙️ 系统设置", self.show_system_settings),
            ("👤 个人信息", self.show_personal_info)
        ]
        
        for text, command in menus:
            btn = ctk.CTkButton(
                left_menu,
                text=text,
                width=210,
                height=50,
                font=("Microsoft YaHei UI", 16),
                fg_color="transparent",
                text_color="gray",
                hover_color=self.BUPT_LIGHT_BLUE,
                anchor="w",
                corner_radius=8,
                command=command
            )
            btn.pack(pady=6, padx=10)
            self.menu_buttons.append(btn)
        
        # 右侧内容区
        self.content_frame = ctk.CTkFrame(main_container, fg_color="white")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # 默认显示用户管理
        self.show_user_management()
    
    def clear_content(self):
        """清空内容区"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def set_active_menu(self, index):
        """设置活动菜单"""
        for i, btn in enumerate(self.menu_buttons):
            if i == index:
                btn.configure(fg_color=self.BUPT_BLUE, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="gray")
    
    def show_user_management(self):
        """显示用户管理"""
        self.set_active_menu(0)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="用户管理",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 创建标签页
        tabview = ctk.CTkTabview(self.content_frame, fg_color="white")
        tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 添加标签页
        tabview.add("用户列表")
        tabview.add("积分管理")
        
        # 用户列表标签页
        user_list_tab = tabview.tab("用户列表")
        
        # 用户类型选择
        type_frame = ctk.CTkFrame(user_list_tab, fg_color="#F0F8FF", corner_radius=10)
        type_frame.pack(fill="x", padx=20, pady=10)
        
        type_inner_frame = ctk.CTkFrame(type_frame, fg_color="transparent")
        type_inner_frame.pack(pady=15, padx=20)
        
        type_label = ctk.CTkLabel(
            type_inner_frame,
            text="用户类型：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE
        )
        type_label.pack(side="left", padx=(0, 15))
        
        self.user_type_var = ctk.StringVar(value="student")
        
        student_radio = ctk.CTkRadioButton(
            type_inner_frame,
            text="学生",
            variable=self.user_type_var,
            value="student",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            command=self.refresh_user_list
        )
        student_radio.pack(side="left", padx=(0, 20))
        
        teacher_radio = ctk.CTkRadioButton(
            type_inner_frame,
            text="教师",
            variable=self.user_type_var,
            value="teacher",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            command=self.refresh_user_list
        )
        teacher_radio.pack(side="left", padx=(0, 20))
        
        admin_radio = ctk.CTkRadioButton(
            type_inner_frame,
            text="管理员",
            variable=self.user_type_var,
            value="admin",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            command=self.refresh_user_list
        )
        admin_radio.pack(side="left")
        
        # 操作按钮
        button_frame = ctk.CTkFrame(user_list_tab, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        add_button = ctk.CTkButton(
            button_frame,
            text="添加用户",
            width=120,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=self.add_user_dialog
        )
        add_button.pack(side="left", padx=(0, 10))
        
        refresh_button = ctk.CTkButton(
            button_frame,
            text="刷新",
            width=100,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_LIGHT_BLUE,
            command=self.refresh_user_list
        )
        refresh_button.pack(side="left")
        
        # 用户列表容器
        self.user_list_frame = ctk.CTkFrame(user_list_tab, corner_radius=10)
        self.user_list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 初始显示学生列表
        self.refresh_user_list()
        
        # 积分管理标签页
        points_tab = tabview.tab("积分管理")
        self.show_points_management_tab(points_tab)
    
    def show_points_management_tab(self, points_tab):
        """显示积分管理标签页"""
        # 顶部操作按钮区域
        button_frame = ctk.CTkFrame(points_tab, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        refresh_button = ctk.CTkButton(
            button_frame,
            text="刷新",
            width=100,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_LIGHT_BLUE,
            command=lambda: self.refresh_points_list(points_list_frame)
        )
        refresh_button.pack(side="left", padx=(0, 10))
        
        batch_reset_button = ctk.CTkButton(
            button_frame,
            text="批量重置积分",
            width=140,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            command=lambda: self.batch_reset_points_dialog(points_list_frame)
        )
        batch_reset_button.pack(side="left", padx=(0, 10))
        
        bidding_button = ctk.CTkButton(
            button_frame,
            text="查看选修课竞价",
            width=140,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color="#4CAF50",
            hover_color="#45A049",
            command=self.show_elective_bidding_dialog
        )
        bidding_button.pack(side="left")
        
        # 积分列表容器
        points_list_frame = ctk.CTkFrame(points_tab, corner_radius=10)
        points_list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 初始显示积分列表
        self.refresh_points_list(points_list_frame)
    
    def refresh_points_list(self, container_frame):
        """刷新积分列表"""
        # 清空容器
        for widget in container_frame.winfo_children():
            widget.destroy()
        
        # 查询所有学生的积分信息
        sql = """
            SELECT 
                s.student_id,
                s.name,
                s.major,
                s.grade,
                s.class_name,
                s.course_points,
                COALESCE(
                    (SELECT SUM(points_bid) 
                     FROM course_biddings 
                     WHERE student_id = s.student_id AND status='pending'), 
                    0
                ) as pending_points
            FROM students s
            WHERE s.status='active'
            ORDER BY s.student_id
        """
        
        students = self.db.execute_query(sql)
        
        if not students:
            no_data_label = ctk.CTkLabel(
                container_frame,
                text="暂无学生数据",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 统计信息
        total_students = len(students)
        total_points = sum(s.get('course_points', 0) or 0 for s in students)
        avg_points = total_points / total_students if total_students > 0 else 0
        
        stats_frame = ctk.CTkFrame(container_frame, fg_color="#F0F8FF", corner_radius=10)
        stats_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(pady=10, padx=20)
        
        stats_text = f"总学生数: {total_students}    总积分: {total_points}    平均积分: {avg_points:.1f}"
        stats_label = ctk.CTkLabel(
            stats_inner,
            text=stats_text,
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE
        )
        stats_label.pack()
        
        # 创建表格
        style = ttk.Style()
        style.configure("Points.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=35,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Points.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        
        columns = ("student_id", "name", "major", "grade", "class", "points", "pending", "available", "action")
        tree = ttk.Treeview(
            container_frame,
            columns=columns,
            show="headings",
            height=20,
            style="Points.Treeview"
        )
        
        tree.heading("student_id", text="学号")
        tree.heading("name", text="姓名")
        tree.heading("major", text="专业")
        tree.heading("grade", text="年级")
        tree.heading("class", text="班级")
        tree.heading("points", text="总积分")
        tree.heading("pending", text="冻结积分")
        tree.heading("available", text="可用积分")
        tree.heading("action", text="操作")
        
        tree.column("student_id", width=100)
        tree.column("name", width=80)
        tree.column("major", width=150)
        tree.column("grade", width=60)
        tree.column("class", width=80)
        tree.column("points", width=80)
        tree.column("pending", width=80)
        tree.column("available", width=80)
        tree.column("action", width=80)
        
        for student in students:
            course_points = student.get('course_points', 0) or 0
            pending_points = student.get('pending_points', 0) or 0
            available_points = course_points - pending_points
            
            tree.insert("", "end", values=(
                student['student_id'],
                student['name'],
                student.get('major', ''),
                student.get('grade', ''),
                student.get('class_name', ''),
                course_points,
                pending_points,
                available_points,
                "调整"
            ), tags=(student['student_id'],))
        
        # 双击调整积分
        def on_double_click(event):
            try:
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    student_id = item['values'][0]
                    student_name = item['values'][1]
                    current_points = item['values'][5]
                    self.adjust_student_points_dialog(student_id, student_name, current_points, container_frame)
            except Exception as e:
                Logger.error(f"打开调整积分对话框失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"打开对话框失败：{str(e)}")
        
        tree.bind("<Double-1>", on_double_click)
        
        scrollbar = ttk.Scrollbar(container_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10, padx=(0, 20))
    
    def adjust_student_points_dialog(self, student_id, student_name, current_points, container_frame):
        """调整学生积分对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("调整学生积分")
        dialog.geometry("600x600")
        dialog.resizable(True, True)  # 允许调整大小
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"600x600+{x}+{y}")
        dialog.minsize(550, 550)  # 设置最小尺寸
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="调整学生积分",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域 - 不使用expand，给按钮留空间
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        # 学生信息
        info_frame = ctk.CTkFrame(content_frame, fg_color="#F0F8FF", corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 12))
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=f"学号: {student_id}    姓名: {student_name}\n当前积分: {current_points}",
            font=("Microsoft YaHei UI", 14),
            text_color=self.BUPT_BLUE,
            justify="left"
        )
        info_label.pack(pady=12, padx=20)
        
        # 调整类型
        type_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=8)
        
        type_label = ctk.CTkLabel(
            type_frame,
            text="调整类型：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            width=100,
            anchor="w"
        )
        type_label.pack(side="left", padx=(0, 10))
        
        adjust_type_var = ctk.StringVar(value="add")
        
        add_radio = ctk.CTkRadioButton(
            type_frame,
            text="增加",
            variable=adjust_type_var,
            value="add",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE
        )
        add_radio.pack(side="left", padx=(0, 20))
        
        deduct_radio = ctk.CTkRadioButton(
            type_frame,
            text="减少",
            variable=adjust_type_var,
            value="deduct",
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE
        )
        deduct_radio.pack(side="left")
        
        # 积分数量
        points_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        points_frame.pack(fill="x", pady=8)
        
        points_label = ctk.CTkLabel(
            points_frame,
            text="积分数量 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            width=100,
            anchor="w"
        )
        points_label.pack(side="left", padx=(0, 10))
        
        points_entry = ctk.CTkEntry(
            points_frame,
            width=300,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="请输入积分数量"
        )
        points_entry.pack(side="left", fill="x", expand=True)
        
        # 调整原因
        reason_label = ctk.CTkLabel(
            content_frame,
            text="调整原因 *",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            anchor="w"
        )
        reason_label.pack(fill="x", pady=(8, 5))
        
        reason_text = ctk.CTkTextbox(
            content_frame,
            width=400,
            height=60,
            font=("Microsoft YaHei UI", 13)
        )
        reason_text.pack(fill="x", pady=(0, 8))
        
        # 按钮区域 - 放在main_frame底部，不在content_frame里
        button_frame = ctk.CTkFrame(main_frame, fg_color="white", height=80)
        button_frame.pack(fill="x", side="bottom", pady=(0, 20))
        button_frame.pack_propagate(False)  # 防止被压缩
        
        def do_adjust():
            # 验证输入
            try:
                points = int(points_entry.get().strip())
                if points <= 0:
                    messagebox.showerror("错误", "积分数量必须大于0", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的积分数量", parent=dialog)
                return
            
            reason = reason_text.get("1.0", "end").strip()
            if not reason:
                messagebox.showerror("错误", "请输入调整原因", parent=dialog)
                return
            
            # 根据类型计算积分变化
            adjust_type = adjust_type_var.get()
            if adjust_type == "add":
                points_change = points
            else:
                points_change = -points
            
            # 调用管理员调整积分方法
            success, msg = self.points_manager.admin_adjust_points(
                self.user.id,
                student_id,
                points_change,
                reason
            )
            
            if success:
                messagebox.showinfo("成功", msg, parent=dialog)
                dialog.destroy()
                # 刷新积分列表
                self.refresh_points_list(container_frame)
            else:
                messagebox.showerror("错误", msg, parent=dialog)
        
        # 创建一个居中的按钮容器
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.pack(expand=True)
        
        confirm_button = ctk.CTkButton(
            button_container,
            text="确认调整",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 15, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=do_adjust
        )
        confirm_button.pack(side="left", padx=15)
        
        cancel_button = ctk.CTkButton(
            button_container,
            text="取消",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 15, "bold"),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy
        )
        cancel_button.pack(side="left", padx=15)
        
        # 绑定回车键确认
        points_entry.bind("<Return>", lambda e: do_adjust())
        
        # 聚焦到输入框
        points_entry.focus()
    
    def batch_reset_points_dialog(self, container_frame):
        """批量重置积分对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("批量重置积分")
        dialog.geometry("550x450")
        dialog.resizable(True, True)  # 允许调整大小
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (450 // 2)
        dialog.geometry(f"550x450+{x}+{y}")
        dialog.minsize(500, 400)  # 设置最小尺寸
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color="#FF6B6B", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="批量重置积分",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域 - 不使用expand，给按钮留空间
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        # 警告信息
        warning_frame = ctk.CTkFrame(content_frame, fg_color="#FFF3CD", corner_radius=10)
        warning_frame.pack(fill="x", pady=(0, 15))
        
        warning_label = ctk.CTkLabel(
            warning_frame,
            text="⚠️  此操作将重置所有活跃学生的积分\n请谨慎操作，该操作不可撤销！",
            font=("Microsoft YaHei UI", 13),
            text_color="#856404",
            justify="center"
        )
        warning_label.pack(pady=12, padx=20)
        
        # 重置积分值
        points_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        points_frame.pack(fill="x", pady=10)
        
        points_label = ctk.CTkLabel(
            points_frame,
            text="重置积分值：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            width=120,
            anchor="w"
        )
        points_label.pack(side="left", padx=(0, 10))
        
        points_entry = ctk.CTkEntry(
            points_frame,
            width=260,
            height=40,
            font=("Microsoft YaHei UI", 14)
        )
        points_entry.insert(0, "200")  # 默认值
        points_entry.pack(side="left", fill="x", expand=True)
        
        # 确认文本
        confirm_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        confirm_frame.pack(fill="x", pady=15)
        
        confirm_label = ctk.CTkLabel(
            confirm_frame,
            text="请输入 RESET 确认操作：",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE,
            width=200,
            anchor="w"
        )
        confirm_label.pack(side="left", padx=(0, 10))
        
        confirm_entry = ctk.CTkEntry(
            confirm_frame,
            width=180,
            height=40,
            font=("Microsoft YaHei UI", 14),
            placeholder_text="输入 RESET"
        )
        confirm_entry.pack(side="left", fill="x", expand=True)
        
        # 按钮区域 - 放在main_frame底部，不在content_frame里
        button_frame = ctk.CTkFrame(main_frame, fg_color="white", height=80)
        button_frame.pack(fill="x", side="bottom", pady=(0, 20))
        button_frame.pack_propagate(False)  # 防止被压缩
        
        def do_reset():
            # 验证确认文本
            if confirm_entry.get().strip() != "RESET":
                messagebox.showerror("错误", "请输入 RESET 确认操作", parent=dialog)
                return
            
            # 验证积分值
            try:
                points = int(points_entry.get().strip())
                if points < 0:
                    messagebox.showerror("错误", "积分不能为负数", parent=dialog)
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的积分值", parent=dialog)
                return
            
            # 再次确认
            if not messagebox.askyesno(
                "最终确认",
                f"确定要将所有学生的积分重置为 {points} 分吗？\n此操作不可撤销！",
                parent=dialog
            ):
                return
            
            # 调用批量重置方法
            success, msg = self.points_manager.batch_reset_points(
                self.user.id,
                points
            )
            
            if success:
                messagebox.showinfo("成功", msg, parent=dialog)
                dialog.destroy()
                # 刷新积分列表
                self.refresh_points_list(container_frame)
            else:
                messagebox.showerror("错误", msg, parent=dialog)
        
        # 创建一个居中的按钮容器
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.pack(expand=True)
        
        reset_button = ctk.CTkButton(
            button_container,
            text="确认重置",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 15, "bold"),
            fg_color="#FF6B6B",
            hover_color="#FF5252",
            command=do_reset
        )
        reset_button.pack(side="left", padx=15)
        
        cancel_button = ctk.CTkButton(
            button_container,
            text="取消",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 15, "bold"),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy
        )
        cancel_button.pack(side="left", padx=15)
        
        # 绑定回车键
        confirm_entry.bind("<Return>", lambda e: do_reset())
        
        # 聚焦到确认输入框
        confirm_entry.focus()
    
    def show_elective_bidding_dialog(self):
        """查看选修课竞价对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("选修课竞价情况")
        dialog.geometry("900x700")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"900x700+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color="#4CAF50", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="选修课竞价情况",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 查询所有有竞价的选修课（包括所有状态的竞价）
        sql = """
            SELECT 
                co.offering_id,
                c.course_name,
                c.course_type,
                co.class_time,
                co.classroom,
                co.max_students,
                co.current_students,
                co.bidding_deadline,
                co.bidding_status,
                COUNT(cb.bidding_id) as bid_count,
                MAX(cb.points_bid) as max_points,
                MIN(cb.points_bid) as min_points,
                AVG(cb.points_bid) as avg_points,
                SUM(CASE WHEN cb.status='pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN cb.status='accepted' THEN 1 ELSE 0 END) as accepted_count,
                SUM(CASE WHEN cb.status='rejected' THEN 1 ELSE 0 END) as rejected_count
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            LEFT JOIN course_biddings cb ON co.offering_id = cb.offering_id
            WHERE c.course_type LIKE '%选修%'
            GROUP BY co.offering_id
            HAVING bid_count > 0
            ORDER BY bid_count DESC, co.offering_id
        """
        
        offerings = self.db.execute_query(sql)
        
        if not offerings:
            no_data_label = ctk.CTkLabel(
                content_frame,
                text="暂无选修课竞价数据",
                font=("Microsoft YaHei UI", 18),
                text_color="#666666"
            )
            no_data_label.pack(pady=100)
            return
        
        # 创建表格
        style = ttk.Style()
        style.configure("Bidding.Treeview", 
                       font=("Microsoft YaHei UI", 12), 
                       rowheight=35,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Bidding.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 13, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        
        columns = ("id", "course", "type", "time", "classroom", "capacity", "bids", "pending", "accepted", "rejected", "max_p", "min_p", "avg_p")
        tree = ttk.Treeview(
            content_frame,
            columns=columns,
            show="headings",
            height=18,
            style="Bidding.Treeview"
        )
        
        tree.heading("id", text="ID")
        tree.heading("course", text="课程名称")
        tree.heading("type", text="类型")
        tree.heading("time", text="上课时间")
        tree.heading("classroom", text="教室")
        tree.heading("capacity", text="容量/已选")
        tree.heading("bids", text="总投入")
        tree.heading("pending", text="待处理")
        tree.heading("accepted", text="已接受")
        tree.heading("rejected", text="已拒绝")
        tree.heading("max_p", text="最高分")
        tree.heading("min_p", text="最低分")
        tree.heading("avg_p", text="平均分")
        
        tree.column("id", width=40)
        tree.column("course", width=120)
        tree.column("type", width=80)
        tree.column("time", width=90)
        tree.column("classroom", width=70)
        tree.column("capacity", width=70)
        tree.column("bids", width=60)
        tree.column("pending", width=60)
        tree.column("accepted", width=60)
        tree.column("rejected", width=60)
        tree.column("max_p", width=60)
        tree.column("min_p", width=60)
        tree.column("avg_p", width=60)
        
        for offering in offerings:
            bid_count = offering.get('bid_count', 0) or 0
            max_points = offering.get('max_points', 0) or 0
            min_points = offering.get('min_points', 0) or 0
            avg_points = offering.get('avg_points', 0) or 0
            pending_count = offering.get('pending_count', 0) or 0
            accepted_count = offering.get('accepted_count', 0) or 0
            rejected_count = offering.get('rejected_count', 0) or 0
            
            capacity_text = f"{offering['max_students']}/{offering.get('current_students', 0) or 0}"
            
            tree.insert("", "end", values=(
                offering['offering_id'],
                offering['course_name'],
                offering.get('course_type', ''),
                offering.get('class_time', ''),
                offering.get('classroom', ''),
                capacity_text,
                bid_count,
                pending_count,
                accepted_count,
                rejected_count,
                f"{max_points:.0f}",
                f"{min_points:.0f}",
                f"{avg_points:.1f}"
            ), tags=(offering['offering_id'],))
        
        # 双击查看详细排名
        def on_double_click(event):
            try:
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    offering_id = item['values'][0]
                    course_name = item['values'][1]
                    class_time = item['values'][2]
                    classroom = item['values'][3]
                    self.show_bidding_ranking_dialog(dialog, offering_id, course_name, class_time, classroom)
            except Exception as e:
                Logger.error(f"打开竞价排名对话框失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"打开对话框失败：{str(e)}", parent=dialog)
        
        tree.bind("<Double-1>", on_double_click)
        
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 提示信息
        tip_label = ctk.CTkLabel(
            main_frame,
            text="💡 双击课程可查看详细竞价排名",
            font=("Microsoft YaHei UI", 12),
            text_color="#666666"
        )
        tip_label.pack(pady=10)
        
        # 关闭按钮
        close_button = ctk.CTkButton(
            main_frame,
            text="关闭",
            width=150,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy
        )
        close_button.pack(pady=(0, 20))
    
    def show_bidding_ranking_dialog(self, parent_window, offering_id, course_name, class_time, classroom):
        """显示课程的详细竞价排名"""
        dialog = ctk.CTkToplevel(parent_window)
        dialog.title(f"竞价排名 - {course_name}")
        dialog.geometry("700x600")
        dialog.resizable(True, True)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"700x600+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"{course_name}\n{class_time} | {classroom}",
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color="white",
            justify="center"
        )
        title_label.pack(expand=True)
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 获取竞价排名
        ranking = self.bidding_manager.get_bidding_ranking(offering_id)
        
        if not ranking:
            no_data_label = ctk.CTkLabel(
                content_frame,
                text="暂无竞价数据",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=100)
        else:
            # 创建表格
            style = ttk.Style()
            style.configure("Ranking.Treeview", 
                           font=("Microsoft YaHei UI", 13), 
                           rowheight=35,
                           background="white",
                           foreground="black",
                           fieldbackground="white")
            style.configure("Ranking.Treeview.Heading", 
                           font=("Microsoft YaHei UI", 14, "bold"),
                           background="#E8F4F8",
                           foreground=self.BUPT_BLUE,
                           relief="flat")
            
            columns = ("rank", "student_id", "name", "points", "time", "status")
            tree = ttk.Treeview(
                content_frame,
                columns=columns,
                show="headings",
                height=15,
                style="Ranking.Treeview"
            )
            
            tree.heading("rank", text="排名")
            tree.heading("student_id", text="学号")
            tree.heading("name", text="姓名")
            tree.heading("points", text="投入积分")
            tree.heading("time", text="投入时间")
            tree.heading("status", text="状态")
            
            tree.column("rank", width=50)
            tree.column("student_id", width=100)
            tree.column("name", width=80)
            tree.column("points", width=80)
            tree.column("time", width=140)
            tree.column("status", width=80)
            
            # 状态映射
            status_map = {
                'pending': '⏳ 待处理',
                'accepted': '✓ 已接受',
                'rejected': '✗ 已拒绝'
            }
            
            for bid in ranking:
                status_text = status_map.get(bid.get('status', 'pending'), '未知')
                status_tag = bid.get('status', 'pending')
                
                tree.insert("", "end", values=(
                    bid['rank'],
                    bid['student_id'],
                    bid['student_name'],
                    bid['points_bid'],
                    bid['bid_time'],
                    status_text
                ), tags=(status_tag,))
            
            # 设置标签颜色
            tree.tag_configure("pending", foreground="#E67E22")   # 橙色 - 待处理
            tree.tag_configure("accepted", foreground="#27AE60")  # 绿色 - 已接受
            tree.tag_configure("rejected", foreground="#E74C3C")  # 红色 - 已拒绝
            
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        # 关闭按钮
        close_button = ctk.CTkButton(
            main_frame,
            text="关闭",
            width=150,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            command=dialog.destroy
        )
        close_button.pack(pady=(0, 20))
    
    def refresh_user_list(self):
        """刷新用户列表"""
        # 清空列表
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        
        user_type = self.user_type_var.get()
        
        # 查询用户
        if user_type == 'student':
            sql = "SELECT student_id, name, major, grade, class_name, email, status FROM students ORDER BY student_id"
            table_name = 'students'
            id_column = 'student_id'
        elif user_type == 'teacher':
            sql = "SELECT teacher_id, name, title, department, email, status FROM teachers ORDER BY teacher_id"
            table_name = 'teachers'
            id_column = 'teacher_id'
        else:  # admin
            sql = "SELECT admin_id, name, role, department, email, status FROM admins ORDER BY admin_id"
            table_name = 'admins'
            id_column = 'admin_id'
        
        users = self.db.execute_query(sql)
        
        # 如果是管理员类型，显示数量限制提示
        if user_type == 'admin':
            admin_count = len([u for u in users if u.get('status') == 'active'])
            limit_info = ctk.CTkLabel(
                self.user_list_frame,
                text=f"当前管理员数量: {admin_count}/2（最多2个）",
                font=("Microsoft YaHei UI", 12),
                text_color="#666666"
            )
            limit_info.pack(pady=(0, 10), anchor="w", padx=20)
        
        if not users:
            no_data_label = ctk.CTkLabel(
                self.user_list_frame,
                text=f"暂无{self.user_type_var.get()}数据",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建表格
        style = ttk.Style()
        style.configure("User.Treeview", 
                       font=("Microsoft YaHei UI", 14), 
                       rowheight=40,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("User.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 15, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        
        # 根据用户类型设置列
        if user_type == 'student':
            columns = ("id", "name", "major", "grade", "class", "email", "status", "action")
            tree = ttk.Treeview(
                self.user_list_frame,
                columns=columns,
                show="headings",
                height=20,
                style="User.Treeview"
            )
            tree.heading("id", text="学号")
            tree.heading("name", text="姓名")
            tree.heading("major", text="专业")
            tree.heading("grade", text="年级")
            tree.heading("class", text="班级")
            tree.heading("email", text="邮箱")
            tree.heading("status", text="状态")
            tree.heading("action", text="操作")
            
            tree.column("id", width=120)
            tree.column("name", width=100)
            tree.column("major", width=180)
            tree.column("grade", width=80)
            tree.column("class", width=100)
            tree.column("email", width=200)
            tree.column("status", width=80)
            tree.column("action", width=100)
            
            for user in users:
                tree.insert("", "end", values=(
                    user['student_id'],
                    user['name'],
                    user.get('major', ''),
                    user.get('grade', ''),
                    user.get('class_name', ''),
                    user.get('email', ''),
                    user.get('status', 'active'),
                    "编辑/删除"
                ), tags=(user['student_id'],))
        
        elif user_type == 'teacher':
            columns = ("id", "name", "title", "department", "email", "status", "action")
            tree = ttk.Treeview(
                self.user_list_frame,
                columns=columns,
                show="headings",
                height=20,
                style="User.Treeview"
            )
            tree.heading("id", text="工号")
            tree.heading("name", text="姓名")
            tree.heading("title", text="职称")
            tree.heading("department", text="院系")
            tree.heading("email", text="邮箱")
            tree.heading("status", text="状态")
            tree.heading("action", text="操作")
            
            tree.column("id", width=120)
            tree.column("name", width=100)
            tree.column("title", width=100)
            tree.column("department", width=150)
            tree.column("email", width=200)
            tree.column("status", width=80)
            tree.column("action", width=100)
            
            for user in users:
                tree.insert("", "end", values=(
                    user['teacher_id'],
                    user['name'],
                    user.get('title', ''),
                    user.get('department', ''),
                    user.get('email', ''),
                    user.get('status', 'active'),
                    "编辑/删除"
                ), tags=(user['teacher_id'],))
        
        else:  # admin
            columns = ("id", "name", "role", "department", "email", "status", "action")
            tree = ttk.Treeview(
                self.user_list_frame,
                columns=columns,
                show="headings",
                height=20,
                style="User.Treeview"
            )
            tree.heading("id", text="管理员ID")
            tree.heading("name", text="姓名")
            tree.heading("role", text="角色")
            tree.heading("department", text="部门")
            tree.heading("email", text="邮箱")
            tree.heading("status", text="状态")
            tree.heading("action", text="操作")
            
            tree.column("id", width=120)
            tree.column("name", width=100)
            tree.column("role", width=100)
            tree.column("department", width=150)
            tree.column("email", width=200)
            tree.column("status", width=80)
            tree.column("action", width=100)
            
            for user in users:
                tree.insert("", "end", values=(
                    user['admin_id'],
                    user['name'],
                    user.get('role', 'admin'),
                    user.get('department', ''),
                    user.get('email', ''),
                    user.get('status', 'active'),
                    "编辑/删除"
                ), tags=(user['admin_id'],))
        
        # 双击编辑（修复闭包问题）
        def on_double_click(event):
            try:
                self.edit_user_dialog(tree, user_type, id_column)
            except Exception as e:
                Logger.error(f"编辑用户对话框打开失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"打开编辑对话框失败：{str(e)}")
        
        tree.bind("<Double-1>", on_double_click)
        
        scrollbar = ttk.Scrollbar(self.user_list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 保存引用
        self.user_tree = tree
        self.user_table_name = table_name
        self.user_id_column = id_column
    
    def add_user_dialog(self):
        """添加用户对话框"""
        user_type = self.user_type_var.get()
        
        if user_type == 'student':
            self.add_student_dialog()
        elif user_type == 'teacher':
            self.add_teacher_dialog()
        else:  # admin
            self.add_admin_dialog()
    
    def add_student_dialog(self):
        """添加学生对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("添加学生")
        dialog.geometry("600x700")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (700 // 2)
        dialog.geometry(f"600x700+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="添加学生",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域（可滚动）
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 启用鼠标滚轮滚动
        self.enable_mousewheel_scroll(content_frame)
        
        # 表单字段
        fields = []
        
        # 学号
        student_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        student_id_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(student_id_frame, text="学号 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        student_id_entry = ctk.CTkEntry(student_id_frame, width=400, height=40, 
                                        font=("Microsoft YaHei UI", 14), placeholder_text="请输入10位学号")
        student_id_entry.pack(side="left", fill="x", expand=True)
        fields.append(("student_id", student_id_entry))
        
        # 姓名
        name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="姓名 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="请输入姓名")
        name_entry.pack(side="left", fill="x", expand=True)
        fields.append(("name", name_entry))
        
        # 密码
        password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(password_frame, text="密码 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        password_entry = ctk.CTkEntry(password_frame, width=400, height=40, 
                                     font=("Microsoft YaHei UI", 14), placeholder_text="默认: student123", show="●")
        password_entry.insert(0, "student123")
        password_entry.pack(side="left", fill="x", expand=True)
        fields.append(("password", password_entry))
        
        # 性别
        gender_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        gender_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(gender_frame, text="性别", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        gender_var = ctk.StringVar(value="男")
        gender_radio_frame = ctk.CTkFrame(gender_frame, fg_color="transparent")
        gender_radio_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkRadioButton(gender_radio_frame, text="男", variable=gender_var, value="男",
                          font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(gender_radio_frame, text="女", variable=gender_var, value="女",
                          font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left")
        fields.append(("gender", gender_var))
        
        # 专业
        major_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        major_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(major_frame, text="专业", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        major_entry = ctk.CTkEntry(major_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="如：计算机科学与技术")
        major_entry.pack(side="left", fill="x", expand=True)
        fields.append(("major", major_entry))
        
        # 年级
        grade_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        grade_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(grade_frame, text="年级", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        grade_entry = ctk.CTkEntry(grade_frame, width=400, height=40, 
                                   font=("Microsoft YaHei UI", 14), placeholder_text="如：2021")
        grade_entry.pack(side="left", fill="x", expand=True)
        fields.append(("grade", grade_entry))
        
        # 班级
        class_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        class_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(class_frame, text="班级", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        class_entry = ctk.CTkEntry(class_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="如：2021211")
        class_entry.pack(side="left", fill="x", expand=True)
        fields.append(("class_name", class_entry))
        
        # 邮箱
        email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        email_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(email_frame, text="邮箱", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        email_entry = ctk.CTkEntry(email_frame, width=400, height=40, 
                                   font=("Microsoft YaHei UI", 14), placeholder_text="如：2021211001@bupt.edu.cn")
        email_entry.pack(side="left", fill="x", expand=True)
        fields.append(("email", email_entry))
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        def confirm_add():
            # 验证必填字段
            student_id = student_id_entry.get().strip()
            name = name_entry.get().strip()
            password = password_entry.get().strip()
            
            if not student_id:
                messagebox.showwarning("提示", "请输入学号")
                return
            
            if not name:
                messagebox.showwarning("提示", "请输入姓名")
                return
            
            if not password:
                messagebox.showwarning("提示", "请输入密码")
                return
            
            # 验证学号格式（10位数字）
            if not student_id.isdigit() or len(student_id) != 10:
                messagebox.showwarning("提示", "学号必须是10位数字")
                return
            
            # 检查学号是否已存在
            existing = self.db.execute_query("SELECT * FROM students WHERE student_id=?", (student_id,))
            if existing:
                messagebox.showerror("错误", f"学号 {student_id} 已存在")
                return
            
            # 准备学生数据
            from utils.crypto import CryptoUtil
            student_data = {
                'student_id': student_id,
                'name': name,
                'password': CryptoUtil.hash_password(password),
                'gender': gender_var.get(),
                'major': major_entry.get().strip() or None,
                'grade': int(grade_entry.get().strip()) if grade_entry.get().strip().isdigit() else None,
                'class_name': class_entry.get().strip() or None,
                'email': email_entry.get().strip() or None,
                'status': 'active'
            }
            
            # 插入数据库
            try:
                self.db.insert_data('students', student_data)
                Logger.info(f"管理员添加学生: {student_id} - {name}")
                messagebox.showinfo("成功", f"学生 {name} ({student_id}) 添加成功！")
                dialog.destroy()
                # 刷新用户列表
                self.refresh_user_list()
            except Exception as e:
                Logger.error(f"添加学生失败: {e}")
                messagebox.showerror("错误", f"添加学生失败：{str(e)}")
        
        def cancel_add():
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认添加",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_add
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
            command=cancel_add
        )
        cancel_btn.pack(side="right")
        
        # 绑定回车键
        student_id_entry.bind('<Return>', lambda e: name_entry.focus())
        name_entry.bind('<Return>', lambda e: password_entry.focus())
        password_entry.bind('<Return>', lambda e: confirm_add())
        
        # 对话框关闭事件
        dialog.protocol("WM_DELETE_WINDOW", cancel_add)
        
        # 聚焦到学号输入框
        student_id_entry.focus()
    
    def add_teacher_dialog(self):
        """添加教师对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("添加教师")
        dialog.geometry("600x750")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"600x750+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="添加教师",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域（可滚动）
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 启用鼠标滚轮滚动
        self.enable_mousewheel_scroll(content_frame)
        
        # 工号
        teacher_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        teacher_id_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(teacher_id_frame, text="工号 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        teacher_id_entry = ctk.CTkEntry(teacher_id_frame, width=400, height=40, 
                                        font=("Microsoft YaHei UI", 14), placeholder_text="如：teacher001")
        teacher_id_entry.pack(side="left", fill="x", expand=True)
        
        # 姓名
        name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="姓名 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="请输入姓名")
        name_entry.pack(side="left", fill="x", expand=True)
        
        # 密码
        password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(password_frame, text="密码 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        password_entry = ctk.CTkEntry(password_frame, width=400, height=40, 
                                     font=("Microsoft YaHei UI", 14), placeholder_text="默认: teacher123", show="●")
        password_entry.insert(0, "teacher123")
        password_entry.pack(side="left", fill="x", expand=True)
        
        # 性别
        gender_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        gender_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(gender_frame, text="性别", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        gender_var = ctk.StringVar(value="男")
        gender_radio_frame = ctk.CTkFrame(gender_frame, fg_color="transparent")
        gender_radio_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkRadioButton(gender_radio_frame, text="男", variable=gender_var, value="男",
                          font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(gender_radio_frame, text="女", variable=gender_var, value="女",
                          font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left")
        
        # 职称
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(title_frame, text="职称", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        title_var = ctk.StringVar(value="讲师")
        title_combo = ctk.CTkComboBox(title_frame, values=["教授", "副教授", "讲师", "助教"],
                                      variable=title_var, width=400, height=40,
                                      font=("Microsoft YaHei UI", 14))
        title_combo.pack(side="left", fill="x", expand=True)
        
        # 所属院系
        department_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        department_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(department_frame, text="所属院系", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        department_entry = ctk.CTkEntry(department_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14), placeholder_text="如：计算机学院")
        department_entry.pack(side="left", fill="x", expand=True)
        
        # 邮箱
        email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        email_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(email_frame, text="邮箱", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        email_entry = ctk.CTkEntry(email_frame, width=400, height=40, 
                                   font=("Microsoft YaHei UI", 14), placeholder_text="如：teacher001@bupt.edu.cn")
        email_entry.pack(side="left", fill="x", expand=True)
        
        # 电话
        phone_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        phone_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(phone_frame, text="电话", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        phone_entry = ctk.CTkEntry(phone_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="如：010-12345678")
        phone_entry.pack(side="left", fill="x", expand=True)
        
        # 入职日期
        hire_date_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        hire_date_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(hire_date_frame, text="入职日期", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        hire_date_entry = ctk.CTkEntry(hire_date_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14), placeholder_text="如：2020-09-01")
        hire_date_entry.pack(side="left", fill="x", expand=True)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        def confirm_add():
            # 验证必填字段
            teacher_id = teacher_id_entry.get().strip()
            name = name_entry.get().strip()
            password = password_entry.get().strip()
            
            if not teacher_id:
                messagebox.showwarning("提示", "请输入工号")
                return
            
            if not name:
                messagebox.showwarning("提示", "请输入姓名")
                return
            
            if not password:
                messagebox.showwarning("提示", "请输入密码")
                return
            
            # 检查工号是否已存在
            existing = self.db.execute_query("SELECT * FROM teachers WHERE teacher_id=?", (teacher_id,))
            if existing:
                messagebox.showerror("错误", f"工号 {teacher_id} 已存在")
                return
            
            # 准备教师数据
            from utils.crypto import CryptoUtil
            teacher_data = {
                'teacher_id': teacher_id,
                'name': name,
                'password': CryptoUtil.hash_password(password),
                'gender': gender_var.get(),
                'title': title_var.get() or None,
                'department': department_entry.get().strip() or None,
                'email': email_entry.get().strip() or None,
                'phone': phone_entry.get().strip() or None,
                'hire_date': hire_date_entry.get().strip() or None,
                'status': 'active'
            }
            
            # 插入数据库
            try:
                self.db.insert_data('teachers', teacher_data)
                Logger.info(f"管理员添加教师: {teacher_id} - {name}")
                messagebox.showinfo("成功", f"教师 {name} ({teacher_id}) 添加成功！")
                dialog.destroy()
                # 刷新用户列表
                self.refresh_user_list()
            except Exception as e:
                Logger.error(f"添加教师失败: {e}")
                messagebox.showerror("错误", f"添加教师失败：{str(e)}")
        
        def cancel_add():
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认添加",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_add
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
            command=cancel_add
        )
        cancel_btn.pack(side="right")
        
        # 绑定回车键
        teacher_id_entry.bind('<Return>', lambda e: name_entry.focus())
        name_entry.bind('<Return>', lambda e: password_entry.focus())
        password_entry.bind('<Return>', lambda e: department_entry.focus())
        department_entry.bind('<Return>', lambda e: confirm_add())
        
        # 对话框关闭事件
        dialog.protocol("WM_DELETE_WINDOW", cancel_add)
        
        # 聚焦到工号输入框
        teacher_id_entry.focus()
    
    def add_admin_dialog(self):
        """添加管理员对话框"""
        # 检查管理员数量限制（最多2个）
        admin_count = len(self.db.execute_query("SELECT * FROM admins WHERE status='active'"))
        if admin_count >= 2:
            messagebox.showwarning("限制", "管理员账号最多只能有两个，当前已有2个管理员，无法继续添加。")
            return
        
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("添加管理员")
        dialog.geometry("600x650")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f"600x650+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="添加管理员",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域（可滚动）
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 启用鼠标滚轮滚动
        self.enable_mousewheel_scroll(content_frame)
        
        # 管理员ID
        admin_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        admin_id_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(admin_id_frame, text="管理员ID *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        admin_id_entry = ctk.CTkEntry(admin_id_frame, width=400, height=40, 
                                     font=("Microsoft YaHei UI", 14), placeholder_text="如：admin002")
        admin_id_entry.pack(side="left", fill="x", expand=True)
        
        # 姓名
        name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="姓名 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="请输入姓名")
        name_entry.pack(side="left", fill="x", expand=True)
        
        # 密码
        password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(password_frame, text="密码 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        password_entry = ctk.CTkEntry(password_frame, width=400, height=40, 
                                     font=("Microsoft YaHei UI", 14), placeholder_text="默认: admin123", show="●")
        password_entry.insert(0, "admin123")
        password_entry.pack(side="left", fill="x", expand=True)
        
        # 角色
        role_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        role_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(role_frame, text="角色", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        role_var = ctk.StringVar(value="admin")
        role_combo = ctk.CTkComboBox(role_frame, values=["admin", "super_admin"],
                                    variable=role_var, width=400, height=40,
                                    font=("Microsoft YaHei UI", 14))
        role_combo.pack(side="left", fill="x", expand=True)
        
        # 所属部门
        department_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        department_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(department_frame, text="所属部门", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        department_entry = ctk.CTkEntry(department_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14), placeholder_text="如：教务处")
        department_entry.pack(side="left", fill="x", expand=True)
        
        # 邮箱
        email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        email_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(email_frame, text="邮箱", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        email_entry = ctk.CTkEntry(email_frame, width=400, height=40, 
                                   font=("Microsoft YaHei UI", 14), placeholder_text="如：admin002@bupt.edu.cn")
        email_entry.pack(side="left", fill="x", expand=True)
        
        # 电话
        phone_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        phone_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(phone_frame, text="电话", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        phone_entry = ctk.CTkEntry(phone_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="如：010-12345000")
        phone_entry.pack(side="left", fill="x", expand=True)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        def confirm_add():
            # 再次检查管理员数量（防止并发）
            current_count = len(self.db.execute_query("SELECT * FROM admins WHERE status='active'"))
            if current_count >= 2:
                messagebox.showwarning("限制", "管理员账号已达到上限（2个），无法继续添加。")
                dialog.destroy()
                self.refresh_user_list()
                return
            
            # 验证必填字段
            admin_id = admin_id_entry.get().strip()
            name = name_entry.get().strip()
            password = password_entry.get().strip()
            
            if not admin_id:
                messagebox.showwarning("提示", "请输入管理员ID")
                return
            
            if not name:
                messagebox.showwarning("提示", "请输入姓名")
                return
            
            if not password:
                messagebox.showwarning("提示", "请输入密码")
                return
            
            # 检查管理员ID是否已存在
            existing = self.db.execute_query("SELECT * FROM admins WHERE admin_id=?", (admin_id,))
            if existing:
                messagebox.showerror("错误", f"管理员ID {admin_id} 已存在")
                return
            
            # 准备管理员数据
            from utils.crypto import CryptoUtil
            admin_data = {
                'admin_id': admin_id,
                'name': name,
                'password': CryptoUtil.hash_password(password),
                'role': role_var.get(),
                'department': department_entry.get().strip() or None,
                'email': email_entry.get().strip() or None,
                'phone': phone_entry.get().strip() or None,
                'status': 'active'
            }
            
            # 插入数据库
            try:
                self.db.insert_data('admins', admin_data)
                Logger.info(f"管理员添加管理员: {admin_id} - {name}")
                messagebox.showinfo("成功", f"管理员 {name} ({admin_id}) 添加成功！")
                dialog.destroy()
                # 刷新用户列表
                self.refresh_user_list()
            except Exception as e:
                Logger.error(f"添加管理员失败: {e}")
                messagebox.showerror("错误", f"添加管理员失败：{str(e)}")
        
        def cancel_add():
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认添加",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_add
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
            command=cancel_add
        )
        cancel_btn.pack(side="right")
        
        # 绑定回车键
        admin_id_entry.bind('<Return>', lambda e: name_entry.focus())
        name_entry.bind('<Return>', lambda e: password_entry.focus())
        password_entry.bind('<Return>', lambda e: department_entry.focus())
        department_entry.bind('<Return>', lambda e: confirm_add())
        
        # 对话框关闭事件
        dialog.protocol("WM_DELETE_WINDOW", cancel_add)
        
        # 聚焦到管理员ID输入框
        admin_id_entry.focus()
    
    def edit_user_dialog(self, tree, user_type, id_column):
        """编辑用户对话框"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        user_id = item['tags'][0]
        
        if user_type == 'student':
            self.edit_student_dialog(user_id)
        elif user_type == 'teacher':
            self.edit_teacher_dialog(user_id)
        else:  # admin
            self.edit_admin_dialog(user_id)
    
    def edit_student_dialog(self, student_id):
        """编辑学生对话框"""
        try:
            # 从数据库加载学生信息
            student_data = self.db.execute_query("SELECT * FROM students WHERE student_id=?", (student_id,))
            if not student_data:
                messagebox.showerror("错误", "学生不存在")
                return
            
            student = student_data[0]
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("编辑学生")
            dialog.geometry("600x750")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (750 // 2)
            dialog.geometry(f"600x750+{x}+{y}")
            
            # 延迟设置grab_set，避免阻塞
            dialog.after(100, lambda: dialog.grab_set())
            
            # 主容器
            main_frame = ctk.CTkFrame(dialog, fg_color="white")
            main_frame.pack(fill="both", expand=True)
            
            # 标题区域
            header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            
            title_label = ctk.CTkLabel(
                header_frame,
                text="编辑学生",
                font=("Microsoft YaHei UI", 24, "bold"),
                text_color="white"
            )
            title_label.pack(expand=True)
            
            # 内容区域（可滚动）
            content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # 启用鼠标滚轮滚动
            self.enable_mousewheel_scroll(content_frame)
            
            # 学号（只读）
            student_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            student_id_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(student_id_frame, text="学号", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            student_id_label = ctk.CTkLabel(student_id_frame, text=student_id, 
                                           font=("Microsoft YaHei UI", 14), 
                                           text_color="gray", width=400, anchor="w")
            student_id_label.pack(side="left", fill="x", expand=True)
            
            # 姓名
            name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            name_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(name_frame, text="姓名 *", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            name_entry.insert(0, student.get('name', ''))
            name_entry.pack(side="left", fill="x", expand=True)
            
            # 密码（可选修改）
            password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            password_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(password_frame, text="密码", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            password_entry = ctk.CTkEntry(password_frame, width=400, height=40, 
                                         font=("Microsoft YaHei UI", 14), 
                                         placeholder_text="留空则不修改密码", show="●")
            password_entry.pack(side="left", fill="x", expand=True)
            
            # 性别
            gender_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            gender_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(gender_frame, text="性别", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            gender_var = ctk.StringVar(value=student.get('gender', '男'))
            gender_radio_frame = ctk.CTkFrame(gender_frame, fg_color="transparent")
            gender_radio_frame.pack(side="left", fill="x", expand=True)
            ctk.CTkRadioButton(gender_radio_frame, text="男", variable=gender_var, value="男",
                              font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left", padx=(0, 20))
            ctk.CTkRadioButton(gender_radio_frame, text="女", variable=gender_var, value="女",
                              font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left")
            
            # 专业
            major_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            major_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(major_frame, text="专业", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            major_entry = ctk.CTkEntry(major_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            major_entry.insert(0, student.get('major', '') or '')
            major_entry.pack(side="left", fill="x", expand=True)
            
            # 年级
            grade_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            grade_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(grade_frame, text="年级", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            grade_entry = ctk.CTkEntry(grade_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14))
            grade_entry.insert(0, str(student.get('grade', '')) if student.get('grade') else '')
            grade_entry.pack(side="left", fill="x", expand=True)
            
            # 班级
            class_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            class_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(class_frame, text="班级", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            class_entry = ctk.CTkEntry(class_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            class_entry.insert(0, student.get('class_name', '') or '')
            class_entry.pack(side="left", fill="x", expand=True)
            
            # 邮箱
            email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            email_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(email_frame, text="邮箱", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            email_entry = ctk.CTkEntry(email_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14))
            email_entry.insert(0, student.get('email', '') or '')
            email_entry.pack(side="left", fill="x", expand=True)
            
            # 状态
            status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            status_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(status_frame, text="状态", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            status_var = ctk.StringVar(value=student.get('status', 'active'))
            status_combo = ctk.CTkComboBox(status_frame, values=["active", "suspended", "graduated"],
                                          variable=status_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            status_combo.pack(side="left", fill="x", expand=True)
            
            # 按钮区域
            button_frame = ctk.CTkFrame(main_frame, fg_color="white")
            button_frame.pack(fill="x", padx=30, pady=20)
            
            def confirm_edit():
                # 验证必填字段
                name = name_entry.get().strip()
                
                if not name:
                    messagebox.showwarning("提示", "请输入姓名")
                    return
                
                # 准备更新数据
                from utils.crypto import CryptoUtil
                update_data = {
                    'name': name,
                    'gender': gender_var.get(),
                    'major': major_entry.get().strip() or None,
                    'grade': int(grade_entry.get().strip()) if grade_entry.get().strip().isdigit() else None,
                    'class_name': class_entry.get().strip() or None,
                    'email': email_entry.get().strip() or None,
                    'status': status_var.get()
                }
                
                # 如果密码不为空，则更新密码
                password = password_entry.get().strip()
                if password:
                    update_data['password'] = CryptoUtil.hash_password(password)
                
                # 更新数据库
                try:
                    rows_affected = self.db.update_data('students', update_data, {'student_id': student_id})
                    if rows_affected > 0:
                        Logger.info(f"管理员编辑学生: {student_id} - {name}")
                        messagebox.showinfo("成功", f"学生信息更新成功！")
                        dialog.destroy()
                        # 刷新用户列表
                        self.refresh_user_list()
                    else:
                        messagebox.showerror("错误", "更新失败，请检查数据")
                except Exception as e:
                    Logger.error(f"编辑学生失败: {e}")
                    messagebox.showerror("错误", f"更新学生信息失败：{str(e)}")
            
            def cancel_edit():
                dialog.destroy()
            
            # 确定按钮
            confirm_btn = ctk.CTkButton(
                button_frame,
                text="确认修改",
                width=180,
                height=45,
                font=("Microsoft YaHei UI", 16, "bold"),
                fg_color=self.BUPT_BLUE,
                hover_color=self.BUPT_LIGHT_BLUE,
                command=confirm_edit
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
                command=cancel_edit
            )
            cancel_btn.pack(side="right")
            
            # 删除按钮
            delete_btn = ctk.CTkButton(
                button_frame,
                text="删除学生",
                width=120,
                height=45,
                font=("Microsoft YaHei UI", 16),
                fg_color="#DC3545",
                hover_color="#C82333",
                command=lambda: self.delete_student_confirm(dialog, student_id, student.get('name', ''))
            )
            delete_btn.pack(side="left")
            
            # 绑定回车键
            name_entry.bind('<Return>', lambda e: major_entry.focus())
            major_entry.bind('<Return>', lambda e: grade_entry.focus())
            grade_entry.bind('<Return>', lambda e: confirm_edit())
            
            # 对话框关闭事件
            dialog.protocol("WM_DELETE_WINDOW", cancel_edit)
            
            # 聚焦到姓名输入框
            name_entry.focus()
            name_entry.select_range(0, 'end')
            
        except Exception as e:
            Logger.error(f"编辑学生对话框创建失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"创建编辑对话框失败：{str(e)}")
    
    def delete_student_confirm(self, parent_dialog, student_id, student_name):
        """确认删除学生"""
        if messagebox.askyesno("确认删除", f"确定要删除学生 {student_name} ({student_id}) 吗？\n\n此操作不可恢复！"):
            try:
                # 检查是否有选课记录
                enrollments = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM enrollments WHERE student_id=?", (student_id,)
                )
                if enrollments and enrollments[0]['count'] > 0:
                    if not messagebox.askyesno("警告", 
                        f"该学生有 {enrollments[0]['count']} 条选课记录，\n"
                        "删除学生将同时删除所有相关记录。\n\n"
                        "确定要继续吗？"):
                        return
                
                # 删除学生（级联删除会处理相关记录）
                rows_affected = self.db.delete_data('students', {'student_id': student_id})
                if rows_affected > 0:
                    Logger.info(f"管理员删除学生: {student_id} - {student_name}")
                    messagebox.showinfo("成功", "学生删除成功！")
                    parent_dialog.destroy()
                    # 刷新用户列表
                    self.refresh_user_list()
                else:
                    messagebox.showerror("错误", "删除失败")
            except Exception as e:
                Logger.error(f"删除学生失败: {e}")
                messagebox.showerror("错误", f"删除学生失败：{str(e)}")
    
    def edit_teacher_dialog(self, teacher_id):
        """编辑教师对话框"""
        try:
            # 从数据库加载教师信息
            teacher_data = self.db.execute_query("SELECT * FROM teachers WHERE teacher_id=?", (teacher_id,))
            if not teacher_data:
                messagebox.showerror("错误", "教师不存在")
                return
            
            teacher = teacher_data[0]
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("编辑教师")
            dialog.geometry("600x800")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (800 // 2)
            dialog.geometry(f"600x800+{x}+{y}")
            
            # 延迟设置grab_set，避免阻塞
            dialog.after(100, lambda: dialog.grab_set())
            
            # 主容器
            main_frame = ctk.CTkFrame(dialog, fg_color="white")
            main_frame.pack(fill="both", expand=True)
            
            # 标题区域
            header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            
            title_label = ctk.CTkLabel(
                header_frame,
                text="编辑教师",
                font=("Microsoft YaHei UI", 24, "bold"),
                text_color="white"
            )
            title_label.pack(expand=True)
            
            # 内容区域（可滚动）
            content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # 启用鼠标滚轮滚动
            self.enable_mousewheel_scroll(content_frame)
            
            # 工号（只读）
            teacher_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            teacher_id_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(teacher_id_frame, text="工号", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            teacher_id_label = ctk.CTkLabel(teacher_id_frame, text=teacher_id, 
                                           font=("Microsoft YaHei UI", 14), 
                                           text_color="gray", width=400, anchor="w")
            teacher_id_label.pack(side="left", fill="x", expand=True)
            
            # 姓名
            name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            name_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(name_frame, text="姓名 *", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            name_entry.insert(0, teacher.get('name', ''))
            name_entry.pack(side="left", fill="x", expand=True)
            
            # 密码（可选修改）
            password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            password_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(password_frame, text="密码", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            password_entry = ctk.CTkEntry(password_frame, width=400, height=40, 
                                         font=("Microsoft YaHei UI", 14), 
                                         placeholder_text="留空则不修改密码", show="●")
            password_entry.pack(side="left", fill="x", expand=True)
            
            # 性别
            gender_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            gender_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(gender_frame, text="性别", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            gender_var = ctk.StringVar(value=teacher.get('gender', '男'))
            gender_radio_frame = ctk.CTkFrame(gender_frame, fg_color="transparent")
            gender_radio_frame.pack(side="left", fill="x", expand=True)
            ctk.CTkRadioButton(gender_radio_frame, text="男", variable=gender_var, value="男",
                              font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left", padx=(0, 20))
            ctk.CTkRadioButton(gender_radio_frame, text="女", variable=gender_var, value="女",
                              font=("Microsoft YaHei UI", 14), fg_color=self.BUPT_BLUE).pack(side="left")
            
            # 职称
            title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            title_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(title_frame, text="职称", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            title_var = ctk.StringVar(value=teacher.get('title', '讲师'))
            title_combo = ctk.CTkComboBox(title_frame, values=["教授", "副教授", "讲师", "助教"],
                                          variable=title_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            title_combo.pack(side="left", fill="x", expand=True)
            
            # 所属院系
            department_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            department_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(department_frame, text="所属院系", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            department_entry = ctk.CTkEntry(department_frame, width=400, height=40, 
                                           font=("Microsoft YaHei UI", 14))
            department_entry.insert(0, teacher.get('department', '') or '')
            department_entry.pack(side="left", fill="x", expand=True)
            
            # 邮箱
            email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            email_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(email_frame, text="邮箱", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            email_entry = ctk.CTkEntry(email_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14))
            email_entry.insert(0, teacher.get('email', '') or '')
            email_entry.pack(side="left", fill="x", expand=True)
            
            # 电话
            phone_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            phone_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(phone_frame, text="电话", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            phone_entry = ctk.CTkEntry(phone_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            phone_entry.insert(0, teacher.get('phone', '') or '')
            phone_entry.pack(side="left", fill="x", expand=True)
            
            # 入职日期
            hire_date_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            hire_date_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(hire_date_frame, text="入职日期", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            hire_date_entry = ctk.CTkEntry(hire_date_frame, width=400, height=40, 
                                           font=("Microsoft YaHei UI", 14))
            hire_date_entry.insert(0, teacher.get('hire_date', '') or '')
            hire_date_entry.pack(side="left", fill="x", expand=True)
            
            # 状态
            status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            status_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(status_frame, text="状态", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            status_var = ctk.StringVar(value=teacher.get('status', 'active'))
            status_combo = ctk.CTkComboBox(status_frame, values=["active", "inactive"],
                                          variable=status_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            status_combo.pack(side="left", fill="x", expand=True)
            
            # 按钮区域
            button_frame = ctk.CTkFrame(main_frame, fg_color="white")
            button_frame.pack(fill="x", padx=30, pady=20)
            
            def confirm_edit():
                # 验证必填字段
                name = name_entry.get().strip()
                
                if not name:
                    messagebox.showwarning("提示", "请输入姓名")
                    return
                
                # 准备更新数据
                from utils.crypto import CryptoUtil
                update_data = {
                    'name': name,
                    'gender': gender_var.get(),
                    'title': title_var.get() or None,
                    'department': department_entry.get().strip() or None,
                    'email': email_entry.get().strip() or None,
                    'phone': phone_entry.get().strip() or None,
                    'hire_date': hire_date_entry.get().strip() or None,
                    'status': status_var.get()
                }
                
                # 如果密码不为空，则更新密码
                password = password_entry.get().strip()
                if password:
                    update_data['password'] = CryptoUtil.hash_password(password)
                
                # 更新数据库
                try:
                    rows_affected = self.db.update_data('teachers', update_data, {'teacher_id': teacher_id})
                    if rows_affected > 0:
                        Logger.info(f"管理员编辑教师: {teacher_id} - {name}")
                        messagebox.showinfo("成功", f"教师信息更新成功！")
                        dialog.destroy()
                        # 刷新用户列表
                        self.refresh_user_list()
                    else:
                        messagebox.showerror("错误", "更新失败，请检查数据")
                except Exception as e:
                    Logger.error(f"编辑教师失败: {e}")
                    messagebox.showerror("错误", f"更新教师信息失败：{str(e)}")
            
            def cancel_edit():
                dialog.destroy()
            
            # 确定按钮
            confirm_btn = ctk.CTkButton(
                button_frame,
                text="确认修改",
                width=180,
                height=45,
                font=("Microsoft YaHei UI", 16, "bold"),
                fg_color=self.BUPT_BLUE,
                hover_color=self.BUPT_LIGHT_BLUE,
                command=confirm_edit
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
                command=cancel_edit
            )
            cancel_btn.pack(side="right")
            
            # 删除按钮
            delete_btn = ctk.CTkButton(
                button_frame,
                text="删除教师",
                width=120,
                height=45,
                font=("Microsoft YaHei UI", 16),
                fg_color="#DC3545",
                hover_color="#C82333",
                command=lambda: self.delete_teacher_confirm(dialog, teacher_id, teacher.get('name', ''))
            )
            delete_btn.pack(side="left")
            
            # 绑定回车键
            name_entry.bind('<Return>', lambda e: department_entry.focus())
            department_entry.bind('<Return>', lambda e: email_entry.focus())
            email_entry.bind('<Return>', lambda e: confirm_edit())
            
            # 对话框关闭事件
            dialog.protocol("WM_DELETE_WINDOW", cancel_edit)
            
            # 聚焦到姓名输入框
            name_entry.focus()
            name_entry.select_range(0, 'end')
            
        except Exception as e:
            Logger.error(f"编辑教师对话框创建失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"创建编辑对话框失败：{str(e)}")
    
    def delete_teacher_confirm(self, parent_dialog, teacher_id, teacher_name):
        """确认删除教师"""
        if messagebox.askyesno("确认删除", f"确定要删除教师 {teacher_name} ({teacher_id}) 吗？\n\n此操作不可恢复！"):
            try:
                # 检查是否有授课记录
                courses = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM course_offerings WHERE teacher_id=?", (teacher_id,)
                )
                if courses and courses[0]['count'] > 0:
                    if not messagebox.askyesno("警告", 
                        f"该教师有 {courses[0]['count']} 条授课记录，\n"
                        "删除教师将影响相关课程。\n\n"
                        "确定要继续吗？"):
                        return
                
                # 删除教师
                rows_affected = self.db.delete_data('teachers', {'teacher_id': teacher_id})
                if rows_affected > 0:
                    Logger.info(f"管理员删除教师: {teacher_id} - {teacher_name}")
                    messagebox.showinfo("成功", "教师删除成功！")
                    parent_dialog.destroy()
                    # 刷新用户列表
                    self.refresh_user_list()
                else:
                    messagebox.showerror("错误", "删除失败")
            except Exception as e:
                Logger.error(f"删除教师失败: {e}")
                messagebox.showerror("错误", f"删除教师失败：{str(e)}")
    
    def edit_admin_dialog(self, admin_id):
        """编辑管理员对话框"""
        try:
            # 从数据库加载管理员信息
            admin_data = self.db.execute_query("SELECT * FROM admins WHERE admin_id=?", (admin_id,))
            if not admin_data:
                messagebox.showerror("错误", "管理员不存在")
                return
            
            admin = admin_data[0]
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("编辑管理员")
            dialog.geometry("600x700")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (700 // 2)
            dialog.geometry(f"600x700+{x}+{y}")
            
            # 延迟设置grab_set，避免阻塞
            dialog.after(100, lambda: dialog.grab_set())
            
            # 主容器
            main_frame = ctk.CTkFrame(dialog, fg_color="white")
            main_frame.pack(fill="both", expand=True)
            
            # 标题区域
            header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            
            title_label = ctk.CTkLabel(
                header_frame,
                text="编辑管理员",
                font=("Microsoft YaHei UI", 24, "bold"),
                text_color="white"
            )
            title_label.pack(expand=True)
            
            # 内容区域（可滚动）
            content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # 启用鼠标滚轮滚动
            self.enable_mousewheel_scroll(content_frame)
            
            # 管理员ID（只读）
            admin_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            admin_id_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(admin_id_frame, text="管理员ID", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            admin_id_label = ctk.CTkLabel(admin_id_frame, text=admin_id, 
                                         font=("Microsoft YaHei UI", 14), 
                                         text_color="gray", width=400, anchor="w")
            admin_id_label.pack(side="left", fill="x", expand=True)
            
            # 姓名
            name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            name_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(name_frame, text="姓名 *", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            name_entry.insert(0, admin.get('name', ''))
            name_entry.pack(side="left", fill="x", expand=True)
            
            # 密码（管理员密码不允许修改）
            password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            password_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(password_frame, text="密码", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            password_entry = ctk.CTkEntry(password_frame, width=400, height=40, 
                                         font=("Microsoft YaHei UI", 14), 
                                         placeholder_text="管理员密码不允许修改",
                                         state="disabled",
                                         fg_color="#F0F0F0")
            password_entry.pack(side="left", fill="x", expand=True)
            
            # 密码提示
            password_hint_label = ctk.CTkLabel(
                content_frame,
                text="⚠️ 管理员密码不允许修改，如需重置请联系系统管理员",
                font=("Microsoft YaHei UI", 11),
                text_color="#FF6B6B",
                anchor="w"
            )
            password_hint_label.pack(fill="x", pady=(0, 10))
            
            # 角色
            role_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            role_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(role_frame, text="角色", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            role_var = ctk.StringVar(value=admin.get('role', 'admin'))
            role_combo = ctk.CTkComboBox(role_frame, values=["admin", "super_admin"],
                                         variable=role_var, width=400, height=40,
                                         font=("Microsoft YaHei UI", 14))
            role_combo.pack(side="left", fill="x", expand=True)
            
            # 所属部门
            department_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            department_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(department_frame, text="所属部门", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            department_entry = ctk.CTkEntry(department_frame, width=400, height=40, 
                                           font=("Microsoft YaHei UI", 14))
            department_entry.insert(0, admin.get('department', '') or '')
            department_entry.pack(side="left", fill="x", expand=True)
            
            # 邮箱
            email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            email_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(email_frame, text="邮箱", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            email_entry = ctk.CTkEntry(email_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14))
            email_entry.insert(0, admin.get('email', '') or '')
            email_entry.pack(side="left", fill="x", expand=True)
            
            # 电话
            phone_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            phone_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(phone_frame, text="电话", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            phone_entry = ctk.CTkEntry(phone_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            phone_entry.insert(0, admin.get('phone', '') or '')
            phone_entry.pack(side="left", fill="x", expand=True)
            
            # 状态
            status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            status_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(status_frame, text="状态", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            status_var = ctk.StringVar(value=admin.get('status', 'active'))
            status_combo = ctk.CTkComboBox(status_frame, values=["active", "inactive"],
                                          variable=status_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            status_combo.pack(side="left", fill="x", expand=True)
            
            # 按钮区域
            button_frame = ctk.CTkFrame(main_frame, fg_color="white")
            button_frame.pack(fill="x", padx=30, pady=20)
            
            def confirm_edit():
                # 验证必填字段
                name = name_entry.get().strip()
                
                if not name:
                    messagebox.showwarning("提示", "请输入姓名")
                    return
                
                # 准备更新数据（管理员密码不允许修改）
                update_data = {
                    'name': name,
                    'role': role_var.get(),
                    'department': department_entry.get().strip() or None,
                    'email': email_entry.get().strip() or None,
                    'phone': phone_entry.get().strip() or None,
                    'status': status_var.get()
                }
                
                # 管理员密码不允许修改，不处理密码字段
                
                # 更新数据库
                try:
                    rows_affected = self.db.update_data('admins', update_data, {'admin_id': admin_id})
                    if rows_affected > 0:
                        Logger.info(f"管理员编辑管理员: {admin_id} - {name}")
                        messagebox.showinfo("成功", f"管理员信息更新成功！")
                        dialog.destroy()
                        # 刷新用户列表
                        self.refresh_user_list()
                    else:
                        messagebox.showerror("错误", "更新失败，请检查数据")
                except Exception as e:
                    Logger.error(f"编辑管理员失败: {e}")
                    messagebox.showerror("错误", f"更新管理员信息失败：{str(e)}")
            
            def cancel_edit():
                dialog.destroy()
            
            # 确定按钮
            confirm_btn = ctk.CTkButton(
                button_frame,
                text="确认修改",
                width=180,
                height=45,
                font=("Microsoft YaHei UI", 16, "bold"),
                fg_color=self.BUPT_BLUE,
                hover_color=self.BUPT_LIGHT_BLUE,
                command=confirm_edit
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
                command=cancel_edit
            )
            cancel_btn.pack(side="right")
            
            # 删除按钮（如果当前管理员不是自己，且至少保留一个管理员）
            admin_count = len(self.db.execute_query("SELECT * FROM admins WHERE status='active'"))
            if admin_id != self.user.id and admin_count > 1:
                delete_btn = ctk.CTkButton(
                    button_frame,
                    text="删除管理员",
                    width=120,
                    height=45,
                    font=("Microsoft YaHei UI", 16),
                    fg_color="#DC3545",
                    hover_color="#C82333",
                    command=lambda: self.delete_admin_confirm(dialog, admin_id, admin.get('name', ''))
                )
                delete_btn.pack(side="left")
            
            # 绑定回车键
            name_entry.bind('<Return>', lambda e: department_entry.focus())
            department_entry.bind('<Return>', lambda e: email_entry.focus())
            email_entry.bind('<Return>', lambda e: confirm_edit())
            
            # 对话框关闭事件
            dialog.protocol("WM_DELETE_WINDOW", cancel_edit)
            
            # 聚焦到姓名输入框
            name_entry.focus()
            name_entry.select_range(0, 'end')
            
        except Exception as e:
            Logger.error(f"编辑管理员对话框创建失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"创建编辑对话框失败：{str(e)}")
    
    def delete_admin_confirm(self, parent_dialog, admin_id, admin_name):
        """确认删除管理员"""
        # 检查管理员数量，至少保留一个
        admin_count = len(self.db.execute_query("SELECT * FROM admins WHERE status='active'"))
        if admin_count <= 1:
            messagebox.showwarning("限制", "系统至少需要保留一个管理员账号，无法删除最后一个管理员。")
            return
        
        # 不能删除自己
        if admin_id == self.user.id:
            messagebox.showwarning("限制", "不能删除当前登录的管理员账号。")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除管理员 {admin_name} ({admin_id}) 吗？\n\n此操作不可恢复！"):
            try:
                # 删除管理员
                rows_affected = self.db.delete_data('admins', {'admin_id': admin_id})
                if rows_affected > 0:
                    Logger.info(f"管理员删除管理员: {admin_id} - {admin_name}")
                    messagebox.showinfo("成功", "管理员删除成功！")
                    parent_dialog.destroy()
                    # 刷新用户列表
                    self.refresh_user_list()
                else:
                    messagebox.showerror("错误", "删除失败")
            except Exception as e:
                Logger.error(f"删除管理员失败: {e}")
                messagebox.showerror("错误", f"删除管理员失败：{str(e)}")
    
    def show_course_management(self):
        """显示课程管理"""
        self.set_active_menu(1)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="课程管理",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 操作按钮
        button_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        add_button = ctk.CTkButton(
            button_frame,
            text="添加课程",
            width=120,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=self.add_course_dialog
        )
        add_button.pack(side="left", padx=(0, 10))
        
        refresh_button = ctk.CTkButton(
            button_frame,
            text="刷新",
            width=100,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_LIGHT_BLUE,
            command=self.refresh_course_list
        )
        refresh_button.pack(side="left")
        
        # 添加"管理开课计划"按钮（当选中课程时可用）
        self.manage_offerings_btn = ctk.CTkButton(
            button_frame,
            text="管理开课计划",
            width=140,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color="#28a745",
            hover_color="#218838",
            command=self.on_manage_offerings_click
        )
        self.manage_offerings_btn.pack(side="left", padx=(10, 0))
        
        # 课程列表容器
        self.course_list_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        self.course_list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 初始显示课程列表
        self.refresh_course_list()
    
    def refresh_course_list(self):
        """刷新课程列表"""
        # 检查 course_list_frame 是否存在
        if not hasattr(self, 'course_list_frame'):
            return
        
        # 清空列表
        for widget in self.course_list_frame.winfo_children():
            widget.destroy()
        
        # 查询课程
        courses = self.db.execute_query("SELECT * FROM courses ORDER BY course_id")
        
        if not courses:
            no_data_label = ctk.CTkLabel(
                self.course_list_frame,
                text="暂无课程数据",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建表格样式
        style = ttk.Style()
        style.configure("Course.Treeview", 
                       font=("Microsoft YaHei UI", 14), 
                       rowheight=40,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Course.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 15, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        
        # 创建表格
        columns = ("id", "name", "credits", "hours", "type", "department", "max_students", "action")
        tree = ttk.Treeview(
            self.course_list_frame,
            columns=columns,
            show="headings",
            height=20,
            style="Course.Treeview"
        )
        
        # 设置列标题
        tree.heading("id", text="课程代码")
        tree.heading("name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("hours", text="学时")
        tree.heading("type", text="课程类型")
        tree.heading("department", text="开课院系")
        tree.heading("max_students", text="最大人数")
        tree.heading("action", text="操作")
        
        # 设置列宽
        tree.column("id", width=120)
        tree.column("name", width=200)
        tree.column("credits", width=80)
        tree.column("hours", width=80)
        tree.column("type", width=100)
        tree.column("department", width=150)
        tree.column("max_students", width=100)
        tree.column("action", width=100)
        
        # 插入数据
        for course in courses:
            tree.insert("", "end", values=(
                course['course_id'],
                course['course_name'],
                course.get('credits', 0),
                course.get('hours', 0) or '',
                course.get('course_type', '') or '',
                course.get('department', '') or '',
                course.get('max_students', 60) or 60,
                "编辑/删除"
            ), tags=(course['course_id'],))
        
        # 双击编辑
        def on_double_click(event):
            try:
                selection = tree.selection()
                if not selection:
                    return
                item = tree.item(selection[0])
                course_id = item['tags'][0]
                self.edit_course_dialog(course_id)
            except Exception as e:
                Logger.error(f"编辑课程对话框打开失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"打开编辑对话框失败：{str(e)}")
        
        tree.bind("<Double-1>", on_double_click)
        
        # 右键菜单：管理开课计划
        def show_offerings_menu(event):
            try:
                selection = tree.selection()
                if not selection:
                    return
                item = tree.item(selection[0])
                course_id = item['tags'][0]
                course_name = item['values'][1]  # 课程名称
                self.manage_course_offerings(course_id, course_name)
            except Exception as e:
                Logger.error(f"打开开课计划管理失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"打开开课计划管理失败：{str(e)}")
        
        scrollbar = ttk.Scrollbar(self.course_list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 保存引用
        self.course_tree = tree
    
    def on_manage_offerings_click(self):
        """点击管理开课计划按钮"""
        try:
            if not hasattr(self, 'course_tree'):
                messagebox.showwarning("提示", "请先选择要管理的课程")
                return
            
            selection = self.course_tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请先选择要管理的课程（单击选中）")
                return
            
            item = self.course_tree.item(selection[0])
            course_id = item['tags'][0]
            course_name = item['values'][1]  # 课程名称
            self.manage_course_offerings(course_id, course_name)
        except Exception as e:
            Logger.error(f"打开开课计划管理失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"打开开课计划管理失败：{str(e)}")
    
    def add_course_dialog(self):
        """添加课程对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("添加课程")
        dialog.geometry("600x750")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (750 // 2)
        dialog.geometry(f"600x750+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="添加课程",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域（可滚动）
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 启用鼠标滚轮滚动
        self.enable_mousewheel_scroll(content_frame)
        
        # 课程代码
        course_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        course_id_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(course_id_frame, text="课程代码 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        course_id_entry = ctk.CTkEntry(course_id_frame, width=400, height=40, 
                                     font=("Microsoft YaHei UI", 14), placeholder_text="如：CS101")
        course_id_entry.pack(side="left", fill="x", expand=True)
        
        # 课程名称
        name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        name_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(name_frame, text="课程名称 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="如：Python程序设计")
        name_entry.pack(side="left", fill="x", expand=True)
        
        # 学分
        credits_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        credits_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(credits_frame, text="学分 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        credits_entry = ctk.CTkEntry(credits_frame, width=400, height=40, 
                                    font=("Microsoft YaHei UI", 14), placeholder_text="如：3.0")
        credits_entry.pack(side="left", fill="x", expand=True)
        
        # 学时
        hours_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        hours_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(hours_frame, text="学时", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        hours_entry = ctk.CTkEntry(hours_frame, width=400, height=40, 
                                  font=("Microsoft YaHei UI", 14), placeholder_text="如：48")
        hours_entry.pack(side="left", fill="x", expand=True)
        
        # 课程类型
        type_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        type_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(type_frame, text="课程类型", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        type_var = ctk.StringVar(value="必修")
        type_combo = ctk.CTkComboBox(type_frame, values=["必修", "选修", "通识"],
                                    variable=type_var, width=400, height=40,
                                    font=("Microsoft YaHei UI", 14))
        type_combo.pack(side="left", fill="x", expand=True)
        
        # 开课院系
        department_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        department_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(department_frame, text="开课院系", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        department_entry = ctk.CTkEntry(department_frame, width=400, height=40, 
                                       font=("Microsoft YaHei UI", 14), placeholder_text="如：计算机学院")
        department_entry.pack(side="left", fill="x", expand=True)
        
        # 课程描述
        description_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        description_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(description_frame, text="课程描述", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        description_entry = ctk.CTkTextbox(description_frame, width=400, height=80,
                                          font=("Microsoft YaHei UI", 14))
        description_entry.pack(side="left", fill="x", expand=True)
        
        # 先修课程
        prerequisite_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        prerequisite_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(prerequisite_frame, text="先修课程", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        prerequisite_entry = ctk.CTkEntry(prerequisite_frame, width=400, height=40, 
                                         font=("Microsoft YaHei UI", 14), placeholder_text="如：CS100")
        prerequisite_entry.pack(side="left", fill="x", expand=True)
        
        # 最大选课人数
        max_students_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        max_students_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(max_students_frame, text="最大人数", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        max_students_entry = ctk.CTkEntry(max_students_frame, width=400, height=40, 
                                         font=("Microsoft YaHei UI", 14), placeholder_text="如：60")
        max_students_entry.insert(0, "60")
        max_students_entry.pack(side="left", fill="x", expand=True)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        def confirm_add():
            # 验证必填字段
            course_id = course_id_entry.get().strip()
            course_name = name_entry.get().strip()
            credits_str = credits_entry.get().strip()
            
            if not course_id:
                messagebox.showwarning("提示", "请输入课程代码")
                return
            
            if not course_name:
                messagebox.showwarning("提示", "请输入课程名称")
                return
            
            if not credits_str:
                messagebox.showwarning("提示", "请输入学分")
                return
            
            # 验证学分格式
            try:
                credits = float(credits_str)
                if credits <= 0:
                    raise ValueError("学分必须大于0")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的学分（正数）")
                return
            
            # 检查课程代码是否已存在
            existing = self.db.execute_query("SELECT * FROM courses WHERE course_id=?", (course_id,))
            if existing:
                messagebox.showerror("错误", f"课程代码 {course_id} 已存在")
                return
            
            # 准备课程数据
            course_data = {
                'course_id': course_id,
                'course_name': course_name,
                'credits': credits,
                'hours': int(hours_entry.get().strip()) if hours_entry.get().strip().isdigit() else None,
                'course_type': type_var.get() or None,
                'department': department_entry.get().strip() or None,
                'description': description_entry.get("1.0", "end-1c").strip() or None,
                'prerequisite': prerequisite_entry.get().strip() or None,
                'max_students': int(max_students_entry.get().strip()) if max_students_entry.get().strip().isdigit() else 60
            }
            
            # 插入数据库
            try:
                self.db.insert_data('courses', course_data)
                Logger.info(f"管理员添加课程: {course_id} - {course_name}")
                messagebox.showinfo("成功", f"课程 {course_name} ({course_id}) 添加成功！")
                dialog.destroy()
                # 刷新课程列表
                self.refresh_course_list()
            except Exception as e:
                Logger.error(f"添加课程失败: {e}")
                messagebox.showerror("错误", f"添加课程失败：{str(e)}")
        
        def cancel_add():
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认添加",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_add
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
            command=cancel_add
        )
        cancel_btn.pack(side="right")
        
        # 绑定回车键
        course_id_entry.bind('<Return>', lambda e: name_entry.focus())
        name_entry.bind('<Return>', lambda e: credits_entry.focus())
        credits_entry.bind('<Return>', lambda e: hours_entry.focus())
        hours_entry.bind('<Return>', lambda e: confirm_add())
        
        # 对话框关闭事件
        dialog.protocol("WM_DELETE_WINDOW", cancel_add)
        
        # 聚焦到课程代码输入框
        course_id_entry.focus()
    
    def edit_course_dialog(self, course_id):
        """编辑课程对话框"""
        try:
            # 从数据库加载课程信息
            course_data = self.db.execute_query("SELECT * FROM courses WHERE course_id=?", (course_id,))
            if not course_data:
                messagebox.showerror("错误", "课程不存在")
                return
            
            course = course_data[0]
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("编辑课程")
            dialog.geometry("600x750")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (750 // 2)
            dialog.geometry(f"600x750+{x}+{y}")
            
            # 延迟设置grab_set，避免阻塞
            dialog.after(100, lambda: dialog.grab_set())
            
            # 主容器
            main_frame = ctk.CTkFrame(dialog, fg_color="white")
            main_frame.pack(fill="both", expand=True)
            
            # 标题区域
            header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            
            title_label = ctk.CTkLabel(
                header_frame,
                text="编辑课程",
                font=("Microsoft YaHei UI", 24, "bold"),
                text_color="white"
            )
            title_label.pack(expand=True)
            
            # 内容区域（可滚动）
            content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # 启用鼠标滚轮滚动
            self.enable_mousewheel_scroll(content_frame)
            
            # 课程代码（只读）
            course_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            course_id_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(course_id_frame, text="课程代码", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            course_id_label = ctk.CTkLabel(course_id_frame, text=course_id, 
                                         font=("Microsoft YaHei UI", 14), 
                                         text_color="gray", width=400, anchor="w")
            course_id_label.pack(side="left", fill="x", expand=True)
            
            # 课程名称
            name_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            name_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(name_frame, text="课程名称 *", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            name_entry = ctk.CTkEntry(name_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            name_entry.insert(0, course.get('course_name', ''))
            name_entry.pack(side="left", fill="x", expand=True)
            
            # 学分
            credits_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            credits_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(credits_frame, text="学分 *", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            credits_entry = ctk.CTkEntry(credits_frame, width=400, height=40, 
                                        font=("Microsoft YaHei UI", 14))
            credits_entry.insert(0, str(course.get('credits', 0)))
            credits_entry.pack(side="left", fill="x", expand=True)
            
            # 学时
            hours_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            hours_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(hours_frame, text="学时", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            hours_entry = ctk.CTkEntry(hours_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14))
            hours_entry.insert(0, str(course.get('hours', '')) if course.get('hours') else '')
            hours_entry.pack(side="left", fill="x", expand=True)
            
            # 课程类型
            type_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            type_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(type_frame, text="课程类型", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            type_var = ctk.StringVar(value=course.get('course_type', '必修'))
            type_combo = ctk.CTkComboBox(type_frame, values=["必修", "选修", "通识"],
                                         variable=type_var, width=400, height=40,
                                         font=("Microsoft YaHei UI", 14))
            type_combo.pack(side="left", fill="x", expand=True)
            
            # 开课院系
            department_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            department_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(department_frame, text="开课院系", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            department_entry = ctk.CTkEntry(department_frame, width=400, height=40, 
                                           font=("Microsoft YaHei UI", 14))
            department_entry.insert(0, course.get('department', '') or '')
            department_entry.pack(side="left", fill="x", expand=True)
            
            # 课程描述
            description_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            description_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(description_frame, text="课程描述", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            description_entry = ctk.CTkTextbox(description_frame, width=400, height=80,
                                               font=("Microsoft YaHei UI", 14))
            description_entry.insert("1.0", course.get('description', '') or '')
            description_entry.pack(side="left", fill="x", expand=True)
            
            # 先修课程
            prerequisite_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            prerequisite_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(prerequisite_frame, text="先修课程", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            prerequisite_entry = ctk.CTkEntry(prerequisite_frame, width=400, height=40, 
                                             font=("Microsoft YaHei UI", 14))
            prerequisite_entry.insert(0, course.get('prerequisite', '') or '')
            prerequisite_entry.pack(side="left", fill="x", expand=True)
            
            # 最大选课人数
            max_students_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            max_students_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(max_students_frame, text="最大人数", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            max_students_entry = ctk.CTkEntry(max_students_frame, width=400, height=40, 
                                             font=("Microsoft YaHei UI", 14))
            max_students_entry.insert(0, str(course.get('max_students', 60)))
            max_students_entry.pack(side="left", fill="x", expand=True)
            
            # 按钮区域
            button_frame = ctk.CTkFrame(main_frame, fg_color="white")
            button_frame.pack(fill="x", padx=30, pady=20)
            
            def confirm_edit():
                # 验证必填字段
                course_name = name_entry.get().strip()
                credits_str = credits_entry.get().strip()
                
                if not course_name:
                    messagebox.showwarning("提示", "请输入课程名称")
                    return
                
                if not credits_str:
                    messagebox.showwarning("提示", "请输入学分")
                    return
                
                # 验证学分格式
                try:
                    credits = float(credits_str)
                    if credits <= 0:
                        raise ValueError("学分必须大于0")
                except ValueError:
                    messagebox.showerror("错误", "请输入有效的学分（正数）")
                    return
                
                # 准备更新数据
                update_data = {
                    'course_name': course_name,
                    'credits': credits,
                    'hours': int(hours_entry.get().strip()) if hours_entry.get().strip().isdigit() else None,
                    'course_type': type_var.get() or None,
                    'department': department_entry.get().strip() or None,
                    'description': description_entry.get("1.0", "end-1c").strip() or None,
                    'prerequisite': prerequisite_entry.get().strip() or None,
                    'max_students': int(max_students_entry.get().strip()) if max_students_entry.get().strip().isdigit() else 60
                }
                
                # 更新数据库
                try:
                    rows_affected = self.db.update_data('courses', update_data, {'course_id': course_id})
                    if rows_affected > 0:
                        Logger.info(f"管理员编辑课程: {course_id} - {course_name}")
                        messagebox.showinfo("成功", f"课程信息更新成功！")
                        dialog.destroy()
                        # 刷新课程列表
                        self.refresh_course_list()
                    else:
                        messagebox.showerror("错误", "更新失败，请检查数据")
                except Exception as e:
                    Logger.error(f"编辑课程失败: {e}")
                    messagebox.showerror("错误", f"更新课程信息失败：{str(e)}")
            
            def cancel_edit():
                dialog.destroy()
            
            # 确定按钮
            confirm_btn = ctk.CTkButton(
                button_frame,
                text="确认修改",
                width=180,
                height=45,
                font=("Microsoft YaHei UI", 16, "bold"),
                fg_color=self.BUPT_BLUE,
                hover_color=self.BUPT_LIGHT_BLUE,
                command=confirm_edit
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
                command=cancel_edit
            )
            cancel_btn.pack(side="right")
            
            # 删除按钮
            delete_btn = ctk.CTkButton(
                button_frame,
                text="删除课程",
                width=120,
                height=45,
                font=("Microsoft YaHei UI", 16),
                fg_color="#DC3545",
                hover_color="#C82333",
                command=lambda: self.delete_course_confirm(dialog, course_id, course.get('course_name', ''))
            )
            delete_btn.pack(side="left")
            
            # 绑定回车键
            name_entry.bind('<Return>', lambda e: credits_entry.focus())
            credits_entry.bind('<Return>', lambda e: hours_entry.focus())
            hours_entry.bind('<Return>', lambda e: confirm_edit())
            
            # 对话框关闭事件
            dialog.protocol("WM_DELETE_WINDOW", cancel_edit)
            
            # 聚焦到课程名称输入框
            name_entry.focus()
            name_entry.select_range(0, 'end')
            
        except Exception as e:
            Logger.error(f"编辑课程对话框创建失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"创建编辑对话框失败：{str(e)}")
    
    def delete_course_confirm(self, parent_dialog, course_id, course_name):
        """确认删除课程"""
        if messagebox.askyesno("确认删除", f"确定要删除课程 {course_name} ({course_id}) 吗？\n\n此操作不可恢复！"):
            try:
                # 检查是否有开课计划
                offerings = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM course_offerings WHERE course_id=?", (course_id,)
                )
                if offerings and offerings[0]['count'] > 0:
                    if not messagebox.askyesno("警告", 
                        f"该课程有 {offerings[0]['count']} 条开课计划，\n"
                        "删除课程将影响相关开课计划。\n\n"
                        "确定要继续吗？"):
                        return
                
                # 删除课程
                rows_affected = self.db.delete_data('courses', {'course_id': course_id})
                if rows_affected > 0:
                    Logger.info(f"管理员删除课程: {course_id} - {course_name}")
                    messagebox.showinfo("成功", "课程删除成功！")
                    parent_dialog.destroy()
                    # 刷新课程列表
                    self.refresh_course_list()
                else:
                    messagebox.showerror("错误", "删除失败")
            except Exception as e:
                Logger.error(f"删除课程失败: {e}")
                messagebox.showerror("错误", f"删除课程失败：{str(e)}")
    
    def manage_course_offerings(self, course_id, course_name):
        """管理课程的开课计划"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"开课计划管理 - {course_name}")
        dialog.geometry("900x600")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"900x600+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"开课计划管理 - {course_name} ({course_id})",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        add_offering_btn = ctk.CTkButton(
            button_frame,
            text="添加开课计划",
            width=140,
            height=35,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=lambda: self.add_offering_dialog(dialog, course_id, course_name)
        )
        add_offering_btn.pack(side="left", padx=(0, 10))
        
        refresh_btn = ctk.CTkButton(
            button_frame,
            text="刷新",
            width=100,
            height=35,
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_LIGHT_BLUE,
            command=lambda: self.refresh_offerings_list(offerings_frame, course_id)
        )
        refresh_btn.pack(side="left")
        
        # 开课计划列表
        offerings_frame = ctk.CTkFrame(main_frame, fg_color="white")
        offerings_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 初始加载列表
        self.refresh_offerings_list(offerings_frame, course_id)
    
    def refresh_offerings_list(self, parent_frame, course_id):
        """刷新开课计划列表"""
        # 清空列表
        for widget in parent_frame.winfo_children():
            widget.destroy()
        
        # 查询该课程的所有开课计划
        sql = """
            SELECT 
                co.offering_id,
                co.teacher_id,
                t.name as teacher_name,
                co.class_time,
                co.classroom,
                co.current_students,
                co.max_students,
                co.status
            FROM course_offerings co
            LEFT JOIN teachers t ON co.teacher_id = t.teacher_id
            WHERE co.course_id=?
            ORDER BY co.offering_id DESC
        """
        offerings = self.db.execute_query(sql, (course_id,))
        
        if not offerings:
            no_data_label = ctk.CTkLabel(
                parent_frame,
                text="暂无开课计划，请点击\"添加开课计划\"添加",
                font=("Microsoft YaHei UI", 14),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建表格
        style = ttk.Style()
        style.configure("Offering.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=35,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Offering.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        
        columns = ("teacher", "time", "classroom", "students", "status", "action")
        tree = ttk.Treeview(
            parent_frame,
            columns=columns,
            show="headings",
            height=12,
            style="Offering.Treeview"
        )
        
        tree.heading("teacher", text="授课教师")
        tree.heading("time", text="上课时间")
        tree.heading("classroom", text="教室")
        tree.heading("students", text="选课人数")
        tree.heading("status", text="状态")
        tree.heading("action", text="操作")
        
        tree.column("teacher", width=150)
        tree.column("time", width=180)
        tree.column("classroom", width=120)
        tree.column("students", width=120)
        tree.column("status", width=80)
        tree.column("action", width=100)
        
        # 插入数据
        for offering in offerings:
            current_count = offering.get('current_students', 0)
            max_count = offering.get('max_students', 60)
            # 将选课人数显示为可点击的格式
            students_info = f"{current_count}/{max_count} (点击查看)"
            status_text = {"open": "开放", "closed": "关闭", "full": "已满"}.get(offering.get('status', 'open'), "开放")
            
            tree.insert("", "end", values=(
                offering.get('teacher_name', '') or f"({offering.get('teacher_id', '')})",
                offering.get('class_time', '') or '',
                offering.get('classroom', '') or '',
                students_info,
                status_text,
                "编辑/删除"
            ), tags=(offering['offering_id'],))
        
        # 单击"选课人数"列查看学生名单
        def on_click(event):
            try:
                # 获取点击的行和列
                item = tree.identify_row(event.y)
                column = tree.identify_column(event.x)
                
                # 检查是否点击了"选课人数"列（第4列，索引为'#4'）
                # columns顺序: teacher(#1), time(#2), classroom(#3), students(#4), status(#5), action(#6)
                if not item or column != '#4':
                    return
                
                # 获取offering_id
                item_tags = tree.item(item)['tags']
                if not item_tags:
                    return
                
                offering_id = item_tags[0]
                
                # 获取课程信息用于显示
                offering_info = None
                for o in offerings:
                    if o['offering_id'] == offering_id:
                        offering_info = o
                        break
                
                if offering_info:
                    # 获取课程名称
                    course_info = self.course_manager.get_offering_by_id(offering_id)
                    course_name = course_info.get('course_name', '') if course_info else ''
                    
                    # 显示学生名单窗口
                    self.show_offering_students_dialog(
                        parent_frame.winfo_toplevel(),
                        offering_id,
                        course_name,
                        offering_info.get('class_time', ''),
                        offering_info.get('classroom', '')
                    )
            except Exception as e:
                Logger.error(f"查看学生名单失败: {e}", exc_info=True)
        
        # 双击编辑
        def on_double_click(event):
            try:
                # 如果点击的是"选课人数"列，不执行编辑操作
                column = tree.identify_column(event.x)
                if column == '#4':  # #4 是"选课人数"列
                    return
                
                selection = tree.selection()
                if not selection:
                    return
                item = tree.item(selection[0])
                offering_id = item['tags'][0]
                self.edit_offering_dialog(parent_frame, offering_id, course_id)
            except Exception as e:
                Logger.error(f"编辑开课计划对话框打开失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"打开编辑对话框失败：{str(e)}")
        
        tree.bind("<Button-1>", on_click)
        tree.bind("<Double-1>", on_double_click)
        
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_offering_students_dialog(self, parent_window, offering_id, course_name, class_time, classroom):
        """显示开课计划的学生名单窗口"""
        dialog = ctk.CTkToplevel(parent_window)
        dialog.title("学生名单")
        dialog.geometry("900x600")
        dialog.resizable(True, True)
        dialog.transient(parent_window)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"900x600+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x", pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # 课程信息
        title_text = f"学生名单 - {course_name}"
        if class_time or classroom:
            details = []
            if class_time:
                details.append(class_time)
            if classroom:
                details.append(classroom)
            if details:
                title_text += f" ({' | '.join(details)})"
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title_text,
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 获取学生名单
        students = self.enrollment_manager.get_course_students(offering_id)
        
        # 学生列表容器
        list_frame = ctk.CTkFrame(main_frame, fg_color="white")
        list_frame.pack(fill="both", expand=True)
        
        # 统计信息
        stats_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=f"共 {len(students)} 名学生",
            font=("Microsoft YaHei UI", 14),
            text_color="#666666"
        )
        stats_label.pack(side="left")
        
        # 创建表格
        table_frame = ctk.CTkFrame(list_frame, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        style = ttk.Style()
        style.configure("Student.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=35,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Student.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        
        columns = ("student_id", "name", "major", "class_name", "enrollment_date", "status")
        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            style="Student.Treeview"
        )
        
        tree.heading("student_id", text="学号")
        tree.heading("name", text="姓名")
        tree.heading("major", text="专业")
        tree.heading("class_name", text="班级")
        tree.heading("enrollment_date", text="选课时间")
        tree.heading("status", text="状态")
        
        tree.column("student_id", width=120)
        tree.column("name", width=100)
        tree.column("major", width=200)
        tree.column("class_name", width=120)
        tree.column("enrollment_date", width=150)
        tree.column("status", width=80)
        
        # 插入学生数据
        if students:
            for student in students:
                status_text = {"enrolled": "已选", "completed": "已完成", "dropped": "已退课"}.get(
                    student.get('status', 'enrolled'), "已选"
                )
                enrollment_date = student.get('enrollment_date', '')
                if enrollment_date:
                    # 格式化日期
                    try:
                        from datetime import datetime
                        if isinstance(enrollment_date, str):
                            dt = datetime.fromisoformat(enrollment_date.replace('Z', '+00:00'))
                            enrollment_date = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        pass
                
                tree.insert("", "end", values=(
                    student.get('student_id', ''),
                    student.get('student_name', ''),
                    student.get('major', ''),
                    student.get('class_name', ''),
                    enrollment_date or '',
                    status_text
                ))
        else:
            # 如果没有学生，显示提示
            no_data_label = ctk.CTkLabel(
                table_frame,
                text="该课程暂无学生选课",
                font=("Microsoft YaHei UI", 16),
                text_color="#999999"
            )
            no_data_label.pack(expand=True)
            return
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 关闭按钮
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        close_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            width=100,
            height=35,
            font=("Microsoft YaHei UI", 14),
            fg_color=self.BUPT_BLUE,
            command=dialog.destroy
        )
        close_btn.pack(side="right")
    
    def add_offering_dialog(self, parent_dialog, course_id, course_name):
        """添加开课计划对话框"""
        dialog = ctk.CTkToplevel(parent_dialog)
        dialog.title("添加开课计划")
        dialog.geometry("600x550")
        dialog.resizable(False, False)
        dialog.transient(parent_dialog)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"600x550+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=f"添加开课计划 - {course_name}",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域（可滚动）
        content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        # 启用鼠标滚轮滚动
        self.enable_mousewheel_scroll(content_frame)
        
        # 课程代码（只读）
        course_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        course_id_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(course_id_frame, text="课程代码", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        course_id_label = ctk.CTkLabel(course_id_frame, text=course_id, 
                                      font=("Microsoft YaHei UI", 14), 
                                      text_color="gray", width=400, anchor="w")
        course_id_label.pack(side="left", fill="x", expand=True)
        
        # 授课教师
        teacher_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        teacher_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(teacher_frame, text="授课教师 *", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        
        # 获取所有教师列表
        teachers = self.db.execute_query("SELECT teacher_id, name FROM teachers WHERE status='active' ORDER BY teacher_id")
        teacher_options = [f"{t['teacher_id']} - {t['name']}" for t in teachers]
        teacher_id_var = ctk.StringVar()
        
        if teacher_options:
            teacher_combo = ctk.CTkComboBox(teacher_frame, values=teacher_options,
                                          variable=teacher_id_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            teacher_combo.pack(side="left", fill="x", expand=True)
        else:
            teacher_combo = ctk.CTkLabel(teacher_frame, text="暂无可用教师", 
                                        font=("Microsoft YaHei UI", 14), 
                                        text_color="gray", width=400, anchor="w")
            teacher_combo.pack(side="left", fill="x", expand=True)
        
        # 上课时间
        time_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        time_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(time_frame, text="上课时间", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        time_entry = ctk.CTkEntry(time_frame, width=400, height=40, 
                                 font=("Microsoft YaHei UI", 14), placeholder_text="如：周一1-2节，周三3-4节")
        time_entry.pack(side="left", fill="x", expand=True)
        
        # 教室
        classroom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        classroom_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(classroom_frame, text="教室", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        classroom_entry = ctk.CTkEntry(classroom_frame, width=400, height=40, 
                                      font=("Microsoft YaHei UI", 14), placeholder_text="如：教三201")
        classroom_entry.pack(side="left", fill="x", expand=True)
        
        # 最大选课人数
        max_students_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        max_students_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(max_students_frame, text="最大人数", font=("Microsoft YaHei UI", 14, "bold"), 
                    text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
        max_students_entry = ctk.CTkEntry(max_students_frame, width=400, height=40, 
                                         font=("Microsoft YaHei UI", 14), placeholder_text="如：60")
        max_students_entry.insert(0, "60")
        max_students_entry.pack(side="left", fill="x", expand=True)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame, fg_color="white")
        button_frame.pack(fill="x", padx=30, pady=20)
        
        def confirm_add():
            # 验证必填字段
            if not teacher_options:
                messagebox.showwarning("提示", "没有可用的教师，请先添加教师")
                return
            
            teacher_selected = teacher_id_var.get()
            if not teacher_selected:
                messagebox.showwarning("提示", "请选择授课教师")
                return
            
            # 提取教师ID
            teacher_id = teacher_selected.split(" - ")[0]
            
            # 准备开课计划数据
            offering_data = {
                'course_id': course_id,
                'teacher_id': teacher_id,
                'class_time': time_entry.get().strip() or None,
                'classroom': classroom_entry.get().strip() or None,
                'max_students': int(max_students_entry.get().strip()) if max_students_entry.get().strip().isdigit() else 60,
                'current_students': 0,
                'status': 'open'
            }
            
            # 插入数据库
            try:
                from core.course_manager import CourseManager
                course_manager = CourseManager(self.db)
                offering_id = course_manager.add_course_offering(offering_data)
                if offering_id:
                    Logger.info(f"管理员添加开课计划: {course_id} - {teacher_id}")
                    messagebox.showinfo("成功", "开课计划添加成功！")
                    dialog.destroy()
                    # 刷新开课计划列表
                    parent_dialog.destroy()
                    self.manage_course_offerings(course_id, course_name)
                else:
                    messagebox.showerror("错误", "添加开课计划失败")
            except ValueError as e:
                # 教室冲突等验证错误
                Logger.warning(f"添加开课计划验证失败: {e}")
                error_msg = str(e)
                if "教室冲突" in error_msg:
                    messagebox.showerror("错误", 
                        f"{error_msg}\n\n请选择不同的教室或调整上课时间")
                else:
                    messagebox.showerror("错误", error_msg)
            except Exception as e:
                Logger.error(f"添加开课计划失败: {e}")
                messagebox.showerror("错误", f"添加开课计划失败：{str(e)}")
        
        def cancel_add():
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认添加",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_add
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
            command=cancel_add
        )
        cancel_btn.pack(side="right")
        
        # 对话框关闭事件
        dialog.protocol("WM_DELETE_WINDOW", cancel_add)
        
        # 聚焦到教师选择框
        if not teacher_options:
            dialog.destroy()
            messagebox.showwarning("提示", "没有可用的教师，请先添加教师")
    
    def edit_offering_dialog(self, parent_frame, offering_id, course_id):
        """编辑开课计划对话框"""
        try:
            # 从数据库加载开课计划信息
            sql = """
                SELECT 
                    co.*,
                    c.course_name,
                    t.name as teacher_name
                FROM course_offerings co
                JOIN courses c ON co.course_id = c.course_id
                LEFT JOIN teachers t ON co.teacher_id = t.teacher_id
                WHERE co.offering_id=?
            """
            offering_data = self.db.execute_query(sql, (offering_id,))
            if not offering_data:
                messagebox.showerror("错误", "开课计划不存在")
                return
            
            offering = offering_data[0]
            course_name = offering.get('course_name', '')
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("编辑开课计划")
            dialog.geometry("600x600")
            dialog.resizable(False, False)
            dialog.transient(self.root)
            
            # 居中显示
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
            y = (dialog.winfo_screenheight() // 2) - (600 // 2)
            dialog.geometry(f"600x600+{x}+{y}")
            
            # 延迟设置grab_set，避免阻塞
            dialog.after(100, lambda: dialog.grab_set())
            
            # 主容器
            main_frame = ctk.CTkFrame(dialog, fg_color="white")
            main_frame.pack(fill="both", expand=True)
            
            # 标题区域
            header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
            header_frame.pack(fill="x")
            header_frame.pack_propagate(False)
            
            title_label = ctk.CTkLabel(
                header_frame,
                text=f"编辑开课计划 - {course_name}",
                font=("Microsoft YaHei UI", 20, "bold"),
                text_color="white"
            )
            title_label.pack(expand=True)
            
            # 内容区域（可滚动）
            content_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white")
            content_frame.pack(fill="both", expand=True, padx=30, pady=20)
            
            # 启用鼠标滚轮滚动
            self.enable_mousewheel_scroll(content_frame)
            
            # 课程代码（只读）
            course_id_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            course_id_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(course_id_frame, text="课程代码", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            course_id_label = ctk.CTkLabel(course_id_frame, text=course_id, 
                                         font=("Microsoft YaHei UI", 14), 
                                         text_color="gray", width=400, anchor="w")
            course_id_label.pack(side="left", fill="x", expand=True)
            
            # 授课教师
            teacher_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            teacher_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(teacher_frame, text="授课教师 *", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            
            # 获取所有教师列表
            teachers = self.db.execute_query("SELECT teacher_id, name FROM teachers WHERE status='active' ORDER BY teacher_id")
            teacher_options = [f"{t['teacher_id']} - {t['name']}" for t in teachers]
            current_teacher = f"{offering.get('teacher_id', '')} - {offering.get('teacher_name', '')}"
            teacher_id_var = ctk.StringVar(value=current_teacher if current_teacher in teacher_options else (teacher_options[0] if teacher_options else ""))
            
            teacher_combo = ctk.CTkComboBox(teacher_frame, values=teacher_options,
                                          variable=teacher_id_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            teacher_combo.pack(side="left", fill="x", expand=True)
            
            # 上课时间
            time_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            time_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(time_frame, text="上课时间", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            time_entry = ctk.CTkEntry(time_frame, width=400, height=40, 
                                     font=("Microsoft YaHei UI", 14))
            time_entry.insert(0, offering.get('class_time', '') or '')
            time_entry.pack(side="left", fill="x", expand=True)
            
            # 教室
            classroom_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            classroom_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(classroom_frame, text="教室", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            classroom_entry = ctk.CTkEntry(classroom_frame, width=400, height=40, 
                                          font=("Microsoft YaHei UI", 14))
            classroom_entry.insert(0, offering.get('classroom', '') or '')
            classroom_entry.pack(side="left", fill="x", expand=True)
            
            # 最大选课人数
            max_students_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            max_students_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(max_students_frame, text="最大人数", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            max_students_entry = ctk.CTkEntry(max_students_frame, width=400, height=40, 
                                             font=("Microsoft YaHei UI", 14))
            max_students_entry.insert(0, str(offering.get('max_students', 60)))
            max_students_entry.pack(side="left", fill="x", expand=True)
            
            # 状态
            status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            status_frame.pack(fill="x", pady=10)
            ctk.CTkLabel(status_frame, text="状态", font=("Microsoft YaHei UI", 14, "bold"), 
                        text_color=self.BUPT_BLUE, width=100, anchor="w").pack(side="left", padx=(0, 10))
            status_var = ctk.StringVar(value=offering.get('status', 'open'))
            status_combo = ctk.CTkComboBox(status_frame, values=["open", "closed", "full"],
                                          variable=status_var, width=400, height=40,
                                          font=("Microsoft YaHei UI", 14))
            status_combo.pack(side="left", fill="x", expand=True)
            
            # 按钮区域
            button_frame = ctk.CTkFrame(main_frame, fg_color="white")
            button_frame.pack(fill="x", padx=30, pady=20)
            
            def confirm_edit():
                # 验证必填字段
                teacher_selected = teacher_id_var.get()
                if not teacher_selected:
                    messagebox.showwarning("提示", "请选择授课教师")
                    return
                
                # 提取教师ID
                teacher_id = teacher_selected.split(" - ")[0]
                
                # 获取教室和时间信息
                class_time = time_entry.get().strip() or None
                classroom = classroom_entry.get().strip() or None
                
                # 检查教室冲突（如果有教室和时间信息）
                if class_time and classroom:
                    try:
                        from core.course_manager import CourseManager
                        course_manager = CourseManager(self.db)
                        conflict = course_manager.check_classroom_conflict(
                            class_time, classroom, exclude_offering_id=offering_id
                        )
                        if conflict:
                            messagebox.showerror("错误", 
                                f"教室冲突：{classroom} 在相同时间段已被 {conflict} 使用\n\n"
                                "请选择不同的教室或调整上课时间")
                            return
                    except Exception as e:
                        Logger.error(f"检查教室冲突失败: {e}")
                        messagebox.showerror("错误", f"检查教室冲突失败：{str(e)}")
                        return
                
                # 准备更新数据
                update_data = {
                    'teacher_id': teacher_id,
                    'class_time': class_time,
                    'classroom': classroom,
                    'max_students': int(max_students_entry.get().strip()) if max_students_entry.get().strip().isdigit() else 60,
                    'status': status_var.get()
                }
                
                # 更新数据库
                try:
                    rows_affected = self.db.update_data('course_offerings', update_data, {'offering_id': offering_id})
                    if rows_affected > 0:
                        Logger.info(f"管理员编辑开课计划: {offering_id} - {teacher_id}")
                        messagebox.showinfo("成功", "开课计划更新成功！")
                        dialog.destroy()
                        # 刷新开课计划列表
                        self.refresh_offerings_list(parent_frame, course_id)
                    else:
                        messagebox.showerror("错误", "更新失败，请检查数据")
                except Exception as e:
                    Logger.error(f"编辑开课计划失败: {e}")
                    messagebox.showerror("错误", f"更新开课计划失败：{str(e)}")
            
            def cancel_edit():
                dialog.destroy()
            
            # 确定按钮
            confirm_btn = ctk.CTkButton(
                button_frame,
                text="确认修改",
                width=180,
                height=45,
                font=("Microsoft YaHei UI", 16, "bold"),
                fg_color=self.BUPT_BLUE,
                hover_color=self.BUPT_LIGHT_BLUE,
                command=confirm_edit
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
                command=cancel_edit
            )
            cancel_btn.pack(side="right")
            
            # 删除按钮
            delete_btn = ctk.CTkButton(
                button_frame,
                text="删除计划",
                width=120,
                height=45,
                font=("Microsoft YaHei UI", 16),
                fg_color="#DC3545",
                hover_color="#C82333",
                command=lambda: self.delete_offering_confirm(dialog, parent_frame, offering_id, course_id, course_name)
            )
            delete_btn.pack(side="left")
            
            # 对话框关闭事件
            dialog.protocol("WM_DELETE_WINDOW", cancel_edit)
            
            # 聚焦到教师选择框
            if teacher_options:
                teacher_combo.focus()
            
        except Exception as e:
            Logger.error(f"编辑开课计划对话框创建失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"创建编辑对话框失败：{str(e)}")
    
    def delete_offering_confirm(self, parent_dialog, parent_frame, offering_id, course_id, course_name):
        """确认删除开课计划"""
        if messagebox.askyesno("确认删除", f"确定要删除该开课计划吗？\n\n课程：{course_name}\n\n此操作不可恢复！"):
            try:
                # 检查是否有选课记录
                enrollments = self.db.execute_query(
                    "SELECT COUNT(*) as count FROM enrollments WHERE offering_id=?", (offering_id,)
                )
                if enrollments and enrollments[0]['count'] > 0:
                    if not messagebox.askyesno("警告", 
                        f"该开课计划有 {enrollments[0]['count']} 条选课记录，\n"
                        "删除开课计划将影响相关选课记录。\n\n"
                        "确定要继续吗？"):
                        return
                
                # 删除开课计划
                rows_affected = self.db.delete_data('course_offerings', {'offering_id': offering_id})
                if rows_affected > 0:
                    Logger.info(f"管理员删除开课计划: {offering_id}")
                    messagebox.showinfo("成功", "开课计划删除成功！")
                    parent_dialog.destroy()
                    # 刷新开课计划列表
                    self.refresh_offerings_list(parent_frame, course_id)
                else:
                    messagebox.showerror("错误", "删除失败")
            except Exception as e:
                Logger.error(f"删除开课计划失败: {e}")
                messagebox.showerror("错误", f"删除开课计划失败：{str(e)}")
    
    def show_statistics(self):
        """显示数据统计"""
        self.set_active_menu(2)
        self.clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="数据统计",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取统计数据
        stats_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        stats_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 学生统计
        student_count = len(self.db.execute_query("SELECT * FROM students"))
        teacher_count = len(self.db.execute_query("SELECT * FROM teachers"))
        admin_count = len(self.db.execute_query("SELECT * FROM admins"))
        course_count = len(self.db.execute_query("SELECT * FROM courses"))
        
        # 定义跳转函数
        def jump_to_students():
            """跳转到学生列表"""
            self.show_user_management()
            self.user_type_var.set("student")
            self.refresh_user_list()
        
        def jump_to_teachers():
            """跳转到教师列表"""
            self.show_user_management()
            self.user_type_var.set("teacher")
            self.refresh_user_list()
        
        def jump_to_admins():
            """跳转到管理员列表"""
            self.show_user_management()
            self.user_type_var.set("admin")
            self.refresh_user_list()
        
        def jump_to_courses():
            """跳转到课程管理"""
            self.show_course_management()
        
        stats_cards = [
            ("学生总数", student_count, "#007bff", "查看学生列表", jump_to_students),
            ("教师总数", teacher_count, "#28a745", "查看教师列表", jump_to_teachers),
            ("管理员总数", admin_count, "#ffc107", "查看管理员列表", jump_to_admins),
            ("课程总数", course_count, "#17a2b8", "查看课程列表", jump_to_courses)
        ]
        
        for i, (label, value, color, button_text, jump_func) in enumerate(stats_cards):
            card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
            card.pack(side="left", fill="both", expand=True, padx=10)
            
            value_label = ctk.CTkLabel(
                card,
                text=str(value),
                font=("Microsoft YaHei UI", 32, "bold"),
                text_color="white"
            )
            value_label.pack(pady=(20, 5))
            
            label_label = ctk.CTkLabel(
                card,
                text=label,
                font=("Microsoft YaHei UI", 16),
                text_color="white"
            )
            label_label.pack(pady=(0, 10))
            
            # 添加跳转按钮
            jump_button = ctk.CTkButton(
                card,
                text=button_text,
                width=140,
                height=35,
                font=("Microsoft YaHei UI", 13, "bold"),
                fg_color="white",
                text_color=color,
                hover_color="#f0f0f0",
                corner_radius=6,
                command=jump_func
            )
            jump_button.pack(pady=(0, 20))
    
    def show_system_logs(self):
        """显示系统日志"""
        self.set_active_menu(3)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="系统日志",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 工具栏
        toolbar_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0F8FF", corner_radius=10)
        toolbar_frame.pack(fill="x", padx=20, pady=10)
        
        toolbar_inner = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        toolbar_inner.pack(pady=10, padx=15, fill="x")
        
        # 日志级别过滤
        level_label = ctk.CTkLabel(
            toolbar_inner,
            text="日志级别：",
            font=("Microsoft YaHei UI", 12, "bold"),
            text_color=self.BUPT_BLUE
        )
        level_label.pack(side="left", padx=(0, 10))
        
        self.log_level_var = ctk.StringVar(value="ALL")
        levels = [("全部", "ALL"), ("DEBUG", "DEBUG"), ("INFO", "INFO"), 
                  ("WARNING", "WARNING"), ("ERROR", "ERROR"), ("CRITICAL", "CRITICAL")]
        
        for text, value in levels:
            radio = ctk.CTkRadioButton(
                toolbar_inner,
                text=text,
                variable=self.log_level_var,
                value=value,
                font=("Microsoft YaHei UI", 11),
                fg_color=self.BUPT_BLUE,
                command=self.refresh_logs
            )
            radio.pack(side="left", padx=(0, 15))
        
        # 搜索框
        search_label = ctk.CTkLabel(
            toolbar_inner,
            text="搜索：",
            font=("Microsoft YaHei UI", 12, "bold"),
            text_color=self.BUPT_BLUE
        )
        search_label.pack(side="left", padx=(20, 10))
        
        self.log_search_var = ctk.StringVar()
        # 使用 trace_add 替代 trace（Python 3.13+ 兼容）
        self.log_search_var.trace_add("write", lambda *args: self.refresh_logs())
        search_entry = ctk.CTkEntry(
            toolbar_inner,
            width=200,
            height=30,
            font=("Microsoft YaHei UI", 11),
            textvariable=self.log_search_var,
            placeholder_text="输入关键词搜索..."
        )
        search_entry.pack(side="left", padx=(0, 15))
        
        # 按钮
        refresh_btn = ctk.CTkButton(
            toolbar_inner,
            text="刷新",
            width=80,
            height=30,
            font=("Microsoft YaHei UI", 11),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=self.refresh_logs
        )
        refresh_btn.pack(side="left", padx=(0, 10))
        
        clear_btn = ctk.CTkButton(
            toolbar_inner,
            text="清空日志",
            width=100,
            height=30,
            font=("Microsoft YaHei UI", 11),
            fg_color="#DC3545",
            hover_color="#C82333",
            command=self.clear_logs_confirm
        )
        clear_btn.pack(side="left", padx=(0, 10))
        
        auto_scroll_var = ctk.BooleanVar(value=True)
        auto_scroll_check = ctk.CTkCheckBox(
            toolbar_inner,
            text="自动滚动到底部",
            variable=auto_scroll_var,
            font=("Microsoft YaHei UI", 11),
            fg_color=self.BUPT_BLUE,
            command=lambda: setattr(self, 'log_auto_scroll', auto_scroll_var.get())
        )
        auto_scroll_check.pack(side="left")
        self.log_auto_scroll = True
        
        # 日志显示区域
        log_container = ctk.CTkFrame(self.content_frame, corner_radius=10)
        log_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 使用Text组件显示日志（支持颜色标记）
        log_text_frame = ctk.CTkFrame(log_container, fg_color="white")
        log_text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 创建Text组件和滚动条
        text_frame = tk.Frame(log_text_frame, bg="white")
        text_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg="#1E1E1E",
            fg="#D4D4D4",
            insertbackground="#FFFFFF",
            selectbackground="#264F78",
            borderwidth=0,
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 配置文本标签颜色
        self.log_text.tag_config("DEBUG", foreground="#9CDCFE")
        self.log_text.tag_config("INFO", foreground="#4EC9B0")
        self.log_text.tag_config("WARNING", foreground="#DCDCAA")
        self.log_text.tag_config("ERROR", foreground="#F48771")
        self.log_text.tag_config("CRITICAL", foreground="#F48771", background="#3F0000")
        self.log_text.tag_config("TIMESTAMP", foreground="#808080")
        self.log_text.tag_config("FILE_INFO", foreground="#569CD6")
        
        # 启用鼠标滚轮
        self.enable_text_mousewheel(self.log_text)
        
        # 初始加载日志
        self.refresh_logs()
    
    def enable_text_mousewheel(self, text_widget):
        """为Text组件启用鼠标滚轮"""
        def on_mousewheel(event):
            try:
                if hasattr(event, 'delta'):
                    # Windows/Mac
                    scroll_amount = int(-event.delta / 120)
                elif event.num == 4:
                    scroll_amount = -1
                elif event.num == 5:
                    scroll_amount = 1
                else:
                    return
                text_widget.yview_scroll(scroll_amount, "units")
            except Exception:
                pass
        
        text_widget.bind("<MouseWheel>", on_mousewheel)
        text_widget.bind("<Button-4>", on_mousewheel)
        text_widget.bind("<Button-5>", on_mousewheel)
    
    def refresh_logs(self):
        """刷新日志显示"""
        try:
            # 检查日志文本组件是否存在
            if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
                return
            
            # 清空当前内容
            self.log_text.delete(1.0, tk.END)
            
            # 读取日志文件
            log_file = Path("logs/app.log")
            if not log_file.exists():
                self.log_text.insert(tk.END, "日志文件不存在：logs/app.log\n", "ERROR")
                return
            
            # 读取日志内容
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except Exception as e:
                self.log_text.insert(tk.END, f"读取日志文件失败：{str(e)}\n", "ERROR")
                return
            
            # 获取过滤条件
            level_filter = self.log_level_var.get()
            search_text = self.log_search_var.get().strip().lower()
            
            # 解析并显示日志
            displayed_count = 0
            for line in lines:
                line = line.rstrip('\n\r')
                if not line:
                    continue
                
                # 解析日志行
                # 格式: 2025-11-08 00:35:16 [INFO] [logger.py:81] 消息内容
                match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] \[([^\]]+)\] (.+)', line)
                
                if match:
                    timestamp, level, file_info, message = match.groups()
                    
                    # 级别过滤
                    if level_filter != "ALL" and level != level_filter:
                        continue
                    
                    # 搜索过滤
                    if search_text and search_text not in line.lower():
                        continue
                    
                    # 插入时间戳
                    self.log_text.insert(tk.END, f"{timestamp} ", "TIMESTAMP")
                    
                    # 插入级别（带颜色）
                    self.log_text.insert(tk.END, f"[{level}] ", level)
                    
                    # 插入文件信息
                    self.log_text.insert(tk.END, f"[{file_info}] ", "FILE_INFO")
                    
                    # 插入消息内容
                    self.log_text.insert(tk.END, f"{message}\n")
                    
                    displayed_count += 1
                else:
                    # 不匹配格式的行（可能是多行消息的一部分）
                    if search_text and search_text not in line.lower():
                        continue
                    if level_filter == "ALL" or not search_text:
                        self.log_text.insert(tk.END, f"{line}\n")
                        displayed_count += 1
            
            # 显示统计信息
            if displayed_count == 0:
                self.log_text.insert(tk.END, "\n没有匹配的日志记录\n", "WARNING")
            else:
                self.log_text.insert(tk.END, f"\n共显示 {displayed_count} 条日志记录\n", "INFO")
            
            # 自动滚动到底部
            if self.log_auto_scroll:
                self.log_text.see(tk.END)
                
        except Exception as e:
            Logger.error(f"刷新日志失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"刷新日志失败：{str(e)}")
    
    def clear_logs_confirm(self):
        """确认清空日志"""
        result = messagebox.askyesno(
            "确认清空",
            "确定要清空所有日志吗？此操作不可恢复！",
            icon="warning"
        )
        if result:
            try:
                log_file = Path("logs/app.log")
                if log_file.exists():
                    # 备份当前日志
                    backup_file = Path(f"logs/app.log.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    log_file.rename(backup_file)
                    
                    # 创建新的空日志文件
                    log_file.touch()
                    
                    Logger.info("日志文件已清空")
                    messagebox.showinfo("成功", "日志已清空，原日志已备份")
                    self.refresh_logs()
                else:
                    messagebox.showwarning("提示", "日志文件不存在")
            except Exception as e:
                Logger.error(f"清空日志失败: {e}", exc_info=True)
                messagebox.showerror("错误", f"清空日志失败：{str(e)}")
    
    def show_system_settings(self):
        """显示系统设置"""
        self.set_active_menu(4)
        self.clear_content()
        
        # 加载配置
        try:
            Config.load('config/config.yaml')
        except Exception as e:
            Logger.error(f"加载配置文件失败: {e}")
            messagebox.showerror("错误", f"加载配置文件失败：{str(e)}")
            return
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="系统设置",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 创建可滚动的内容区域
        scrollable_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="white")
        scrollable_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 启用鼠标滚轮
        self.enable_mousewheel_scroll(scrollable_frame)
        
        # 初始化设置条目字典（必须在创建设置区域之前）
        self.settings_entries = {}
        
        # 应用配置区域
        app_frame = self._create_settings_section(
            scrollable_frame, 
            "应用配置", 
            [
                ("应用名称", "app.name", "text"),
                ("版本", "app.version", "text"),
                ("调试模式", "app.debug", "bool")
            ]
        )
        app_frame.pack(fill="x", padx=20, pady=10)
        
        # 数据库配置区域
        db_frame = self._create_settings_section(
            scrollable_frame,
            "数据库配置",
            [
                ("数据库类型", "database.type", "text"),
                ("数据库路径", "database.path", "text")
            ]
        )
        db_frame.pack(fill="x", padx=20, pady=10)
        
        # 日志配置区域
        log_frame = self._create_settings_section(
            scrollable_frame,
            "日志配置",
            [
                ("日志级别", "logging.level", "select", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
                ("日志文件", "logging.file", "text"),
                ("最大文件大小(MB)", "logging.max_size", "number"),
                ("备份文件数量", "logging.backup_count", "number")
            ]
        )
        log_frame.pack(fill="x", padx=20, pady=10)
        
        # GUI配置区域
        gui_frame = self._create_settings_section(
            scrollable_frame,
            "界面配置",
            [
                ("主题", "gui.theme", "select", ["dark-blue", "green", "dark-green"]),
                ("窗口大小", "gui.window_size", "text"),
                ("字体大小", "gui.font_size", "number")
            ]
        )
        gui_frame.pack(fill="x", padx=20, pady=10)
        
        # 网络配置区域
        network_frame = self._create_settings_section(
            scrollable_frame,
            "网络配置",
            [
                ("服务器地址", "network.server.host", "text"),
                ("服务器端口", "network.server.port", "number"),
                ("最大连接数", "network.server.max_connections", "number"),
                ("客户端超时(秒)", "network.client.timeout", "number"),
                ("重试次数", "network.client.retry_times", "number")
            ]
        )
        network_frame.pack(fill="x", padx=20, pady=10)
        
        # 缓存配置区域
        cache_frame = self._create_settings_section(
            scrollable_frame,
            "缓存配置",
            [
                ("启用缓存", "cache.enabled", "bool"),
                ("最大缓存条目", "cache.max_size", "number"),
                ("缓存过期时间(秒)", "cache.expire_time", "number")
            ]
        )
        cache_frame.pack(fill="x", padx=20, pady=10)
        
        # 数据分析配置区域
        analysis_frame = self._create_settings_section(
            scrollable_frame,
            "数据分析配置",
            [
                ("图表风格", "analysis.chart_style", "text"),
                ("图表分辨率(DPI)", "analysis.dpi", "number")
            ]
        )
        analysis_frame.pack(fill="x", padx=20, pady=10)
        
        # 操作按钮
        button_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="保存设置",
            width=150,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=self.save_system_settings
        )
        save_btn.pack(side="left", padx=(0, 15))
        
        reset_btn = ctk.CTkButton(
            button_frame,
            text="重置为默认",
            width=150,
            height=45,
            font=("Microsoft YaHei UI", 16),
            fg_color="#6C757D",
            hover_color="#5A6268",
            command=self.reset_system_settings
        )
        reset_btn.pack(side="left", padx=(0, 15))
        
        reload_btn = ctk.CTkButton(
            button_frame,
            text="重新加载",
            width=120,
            height=45,
            font=("Microsoft YaHei UI", 16),
            fg_color=self.BUPT_LIGHT_BLUE,
            command=lambda: self.show_system_settings()
        )
        reload_btn.pack(side="left")
        
        # 注意：settings_entries 已在上面初始化
    
    def _create_settings_section(self, parent, title, fields):
        """创建设置区域"""
        section_frame = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color=self.BUPT_BLUE
        )
        title_label.pack(pady=(15, 10), padx=20, anchor="w")
        
        # 内容区域
        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        # 创建字段
        for field_info in fields:
            if len(field_info) == 3:
                label, key, field_type = field_info
                options = None
            else:
                label, key, field_type, options = field_info
            
            field_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=8)
            
            # 标签
            label_widget = ctk.CTkLabel(
                field_frame,
                text=label + "：",
                font=("Microsoft YaHei UI", 14),
                text_color="#333333",
                width=180,
                anchor="w"
            )
            label_widget.pack(side="left", padx=(0, 15))
            
            # 获取当前值
            current_value = Config.get(key, "")
            
            # 特殊处理：日志文件大小需要从字节转换为MB显示
            if key == "logging.max_size":
                current_value = int(current_value) // (1024 * 1024) if current_value else 10
            
            # 根据类型创建输入控件
            if field_type == "text":
                entry = ctk.CTkEntry(
                    field_frame,
                    width=400,
                    height=35,
                    font=("Microsoft YaHei UI", 13)
                )
                entry.insert(0, str(current_value) if current_value else "")
                entry.pack(side="left", fill="x", expand=True)
                self.settings_entries[key] = entry
                
            elif field_type == "number":
                entry = ctk.CTkEntry(
                    field_frame,
                    width=400,
                    height=35,
                    font=("Microsoft YaHei UI", 13)
                )
                entry.insert(0, str(current_value) if current_value else "0")
                entry.pack(side="left", fill="x", expand=True)
                self.settings_entries[key] = entry
                
            elif field_type == "bool":
                var = ctk.BooleanVar(value=bool(current_value) if current_value is not None else False)
                checkbox = ctk.CTkCheckBox(
                    field_frame,
                    text="启用" if current_value else "禁用",
                    variable=var,
                    font=("Microsoft YaHei UI", 13),
                    fg_color=self.BUPT_BLUE,
                    command=lambda v=var, k=key: self._update_bool_label(v, k)
                )
                checkbox.pack(side="left")
                self.settings_entries[key] = var
                
            elif field_type == "select":
                combo = ctk.CTkComboBox(
                    field_frame,
                    width=400,
                    height=35,
                    font=("Microsoft YaHei UI", 13),
                    values=options
                )
                combo.set(str(current_value) if current_value else options[0])
                combo.pack(side="left", fill="x", expand=True)
                self.settings_entries[key] = combo
        
        return section_frame
    
    def _update_bool_label(self, var, key):
        """更新布尔值标签"""
        # 这个方法可以用于更新复选框的文本，但CTkCheckBox不支持动态文本
        pass
    
    def save_system_settings(self):
        """保存系统设置"""
        try:
            # 保存所有设置
            for key, widget in self.settings_entries.items():
                if isinstance(widget, ctk.CTkEntry):
                    value = widget.get().strip()
                    # 特殊处理：日志文件大小需要从MB转换为字节
                    if key == "logging.max_size":
                        try:
                            value = int(value) * 1024 * 1024  # MB转字节
                        except ValueError:
                            messagebox.showerror("错误", f"{key} 必须是数字")
                            return
                    # 尝试转换为数字
                    elif key.endswith(('.port', '.timeout', '.retry_times', 
                                   '.backup_count', '.max_connections', '.font_size', 
                                   '.max_size', '.expire_time', '.dpi')):
                        try:
                            value = int(value)
                        except ValueError:
                            messagebox.showerror("错误", f"{key} 必须是数字")
                            return
                    Config.set(key, value)
                    
                elif isinstance(widget, ctk.CTkComboBox):
                    value = widget.get()
                    Config.set(key, value)
                    
                elif isinstance(widget, ctk.BooleanVar):
                    value = widget.get()
                    Config.set(key, value)
            
            # 保存到文件
            Config.save()
            
            Logger.info(f"管理员保存系统设置: {self.user.name} ({self.user.id})")
            messagebox.showinfo("成功", "设置已保存！\n部分设置需要重启应用程序才能生效。")
            
        except Exception as e:
            Logger.error(f"保存系统设置失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"保存设置失败：{str(e)}")
    
    def reset_system_settings(self):
        """重置为默认设置"""
        result = messagebox.askyesno(
            "确认重置",
            "确定要重置所有设置为默认值吗？\n此操作将覆盖当前所有设置！",
            icon="warning"
        )
        if not result:
            return
        
        try:
            # 默认配置
            default_config = {
                'app': {
                    'name': '北京邮电大学教学管理系统',
                    'version': '1.0.0',
                    'debug': False
                },
                'database': {
                    'type': 'sqlite',
                    'path': 'data/bupt_teaching.db'
                },
                'logging': {
                    'level': 'INFO',
                    'file': 'logs/app.log',
                    'max_size': 10485760,
                    'backup_count': 5
                },
                'gui': {
                    'theme': 'dark-blue',
                    'window_size': '1400x800',
                    'font_size': 14
                },
                'network': {
                    'server': {
                        'host': 'localhost',
                        'port': 8888,
                        'max_connections': 10
                    },
                    'client': {
                        'timeout': 30,
                        'retry_times': 3
                    }
                },
                'cache': {
                    'enabled': True,
                    'max_size': 100,
                    'expire_time': 3600
                },
                'analysis': {
                    'chart_style': 'seaborn',
                    'figure_size': [10, 6],
                    'dpi': 100
                }
            }
            
            # 保存默认配置
            config_path = Path('config/config.yaml')
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False)
            
            Logger.info(f"管理员重置系统设置为默认值: {self.user.name} ({self.user.id})")
            messagebox.showinfo("成功", "设置已重置为默认值！\n请重新加载页面查看。")
            
            # 重新加载配置并刷新页面
            Config.load('config/config.yaml')
            self.show_system_settings()
            
        except Exception as e:
            Logger.error(f"重置系统设置失败: {e}", exc_info=True)
            messagebox.showerror("错误", f"重置设置失败：{str(e)}")
    
    def show_personal_info(self):
        """显示个人信息"""
        self.set_active_menu(5)
        self.clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="个人信息",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 信息卡片
        info_frame = ctk.CTkFrame(self.content_frame, fg_color="#F8F9FA")
        info_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        infos = [
            ("管理员ID", self.user.id),
            ("姓名", self.user.name),
            ("角色", self.user.extra_info.get('role', 'admin')),
            ("部门", self.user.extra_info.get('department', '')),
            ("邮箱", self.user.email or '')
        ]
        
        for label_text, value in infos:
            row_frame = ctk.CTkFrame(info_frame, fg_color="white", corner_radius=8)
            row_frame.pack(fill="x", padx=30, pady=12)
            
            label = ctk.CTkLabel(
                row_frame,
                text=f"{label_text}：",
                font=("Microsoft YaHei UI", 18, "bold"),
                text_color=self.BUPT_BLUE,
                width=120,
                anchor="e"
            )
            label.pack(side="left", padx=20, pady=15)
            
            value_label = ctk.CTkLabel(
                row_frame,
                text=str(value),
                font=("Microsoft YaHei UI", 18),
                text_color="black"
            )
            value_label.pack(side="left", padx=20, pady=15)
    
    def do_logout(self):
        """注销登录"""
        if messagebox.askyesno("确认", "确定要退出登录吗？"):
            self.root.destroy()
            self.logout_callback()
    
    def on_close(self):
        """关闭窗口"""
        self.do_logout()

