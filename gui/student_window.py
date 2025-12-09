"""
学生端主窗口 - 北京邮电大学教学管理系统
提供选课、查成绩、查课表等功能
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
import re
from typing import Optional, Dict
from pathlib import Path
from PIL import Image
from utils.logger import Logger
from core.course_manager import CourseManager
from core.enrollment_manager import EnrollmentManager
from core.grade_manager import GradeManager
from core.points_manager import PointsManager
from core.bidding_manager import BiddingManager


class StudentWindow:
    """学生端主窗口类"""
    
    # 北邮蓝色主题
    BUPT_BLUE = "#003087"
    BUPT_LIGHT_BLUE = "#0066CC"
    
    def __init__(self, root, user, db, logout_callback):
        """
        初始化学生端窗口
        
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
        self.enrollment_manager = EnrollmentManager(db)
        self.grade_manager = GradeManager(db)
        self.points_manager = PointsManager(db)
        self.bidding_manager = BiddingManager(db, self.points_manager)
        
        # 设置窗口
        self.root.title(f"北京邮电大学教学管理系统 - 学生端 - {user.name}")
        
        window_width = 1200
        window_height = 700
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 创建界面
        self.create_widgets()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        Logger.info(f"学生端窗口打开: {user.name}")
    
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
            text="北京邮电大学教学管理系统",
            font=("Microsoft YaHei UI", 22, "bold"),
            text_color="white"
        )
        title_label.pack(side="left")
        
        # 用户信息
        user_info_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        user_info_frame.pack(side="right", padx=20)
        
        user_label = ctk.CTkLabel(
            user_info_frame,
            text=f"欢迎，{self.user.name} ({self.user.id})",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color="white"
        )
        user_label.pack(side="left", padx=(0, 15))
        
        logout_button = ctk.CTkButton(
            user_info_frame,
            text="退出登录",
            width=100,
            height=40,
            font=("Microsoft YaHei UI", 16, "bold"),
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
        left_menu = ctk.CTkFrame(main_container, width=200, fg_color="#F0F0F0")
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
            ("📚 我的选课", self.show_my_courses),
            ("🔍 课程选课", self.show_course_selection),
            ("📋 培养方案", self.show_curriculum),
            ("📊 我的成绩", self.show_my_grades),
            ("📅 我的课表", self.show_my_schedule),
            ("👤 个人信息", self.show_personal_info)
        ]
        
        for text, command in menus:
            btn = ctk.CTkButton(
                left_menu,
                text=text,
                width=190,
                height=50,
                font=("Microsoft YaHei UI", 17),
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
        
        # 默认显示我的选课
        self.show_my_courses()
    
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
    
    def show_my_courses(self):
        """显示我的选课 - 包含必修课和选修课状态"""
        self.set_active_menu(0)
        self.clear_content()
        
        # 标题区域
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=20, padx=20)
        
        title = ctk.CTkLabel(
            title_frame,
            text="我的选课",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(side="left")
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            title_frame,
            text="🔄 刷新",
            width=100,
            height=35,
            font=("Microsoft YaHei UI", 14),
            fg_color="#4CAF50",
            hover_color="#45a049",
            command=self.show_my_courses
        )
        refresh_btn.pack(side="right")
        
        # 获取选课记录（包括所有状态的选课，以便显示选修课进度）
        all_enrollments = self.enrollment_manager.get_student_enrollments(
            self.user.id, status=None  # 获取所有状态的选课
        )
        
        # 获取已选中的课程（enrolled状态）
        enrolled_courses = [e for e in all_enrollments if e.get('status') == 'enrolled']
        
        # 获取所有pending/accepted/rejected状态的竞价记录（选修课投入但可能未确认）
        # 排除已经enrolled的课程
        enrolled_offering_ids = [e['offering_id'] for e in enrolled_courses]
        
        if enrolled_offering_ids:
            enrolled_ids_str = ','.join(map(str, enrolled_offering_ids))
            pending_bids = self.db.execute_query("""
                SELECT 
                    cb.offering_id,
                    cb.points_bid,
                    cb.status,
                    co.course_id,
                    c.course_name,
                    c.credits,
                    c.course_type,
                    co.teacher_id,
                    t.name as teacher_name,
                    co.class_time,
                    co.classroom
                FROM course_biddings cb
                JOIN course_offerings co ON cb.offering_id = co.offering_id
                JOIN courses c ON co.course_id = c.course_id
                JOIN teachers t ON co.teacher_id = t.teacher_id
                WHERE cb.student_id = ? 
                  AND cb.status IN ('pending', 'accepted', 'rejected')
                  AND cb.offering_id NOT IN ({})
            """.format(enrolled_ids_str), (self.user.id,))
        else:
            pending_bids = self.db.execute_query("""
                SELECT 
                    cb.offering_id,
                    cb.points_bid,
                    cb.status,
                    co.course_id,
                    c.course_name,
                    c.credits,
                    c.course_type,
                    co.teacher_id,
                    t.name as teacher_name,
                    co.class_time,
                    co.classroom
                FROM course_biddings cb
                JOIN course_offerings co ON cb.offering_id = co.offering_id
                JOIN courses c ON co.course_id = c.course_id
                JOIN teachers t ON co.teacher_id = t.teacher_id
                WHERE cb.student_id = ? 
                  AND cb.status IN ('pending', 'accepted', 'rejected')
            """, (self.user.id,))
        
        if not enrolled_courses and not pending_bids:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无选课记录",
                font=("Microsoft YaHei UI", 18),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建表格框架
        table_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 创建Treeview
        style = ttk.Style()
        style.configure("MyCourses.Treeview", 
                       font=("Microsoft YaHei UI", 14), 
                       rowheight=50,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("MyCourses.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 15, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("MyCourses.Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        tree = ttk.Treeview(
            table_frame,
            columns=("course_id", "course_name", "type", "credits", "teacher", "time", "classroom", "status", "action"),
            show="headings",
            style="MyCourses.Treeview",
            height=15
        )
        
        # 列标题
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("type", text="类型")
        tree.heading("credits", text="学分")
        tree.heading("teacher", text="授课教师")
        tree.heading("time", text="上课时间")
        tree.heading("classroom", text="教室")
        tree.heading("status", text="选课状态")
        tree.heading("action", text="操作")
        
        # 列宽（优化为更紧凑的布局，确保一屏内显示所有列）
        tree.column("course_id", width=80)
        tree.column("course_name", width=140)
        tree.column("type", width=70)
        tree.column("credits", width=50)
        tree.column("teacher", width=80)
        tree.column("time", width=120)
        tree.column("classroom", width=80)
        tree.column("status", width=120)
        tree.column("action", width=70)
        
        # 用于跟踪已显示的课程，避免重复
        displayed_offerings = set()
        
        # 1. 显示已选中的课程（必修课和已确认的选修课）
        for enrollment in enrolled_courses:
            offering_id = enrollment['offering_id']
            displayed_offerings.add(offering_id)
            
            course_type = enrollment.get('course_type', '')
            # 判断是必修还是选修
            if '必修' in course_type or '基础' in course_type:
                course_type_display = course_type
                status_text = "✓ 选课成功"
                status_tag = "success"
            else:
                # 选修课：检查竞价状态
                course_type_display = course_type
                bid_info = self.bidding_manager.get_bid_info(self.user.id, offering_id)
                if bid_info:
                    bid_status = bid_info.get('status', '')
                    points_bid = bid_info.get('points_bid', 0)
                    if bid_status == 'accepted':
                        status_text = f"✓ 选课成功（投入{points_bid}分）"
                    elif bid_status == 'pending':
                        status_text = f"✓ 选课成功（已投入{points_bid}分）"
                    else:
                        status_text = "✓ 选课成功"
                else:
                    status_text = "✓ 选课成功"
                status_tag = "success"
            
            tree.insert("", "end", values=(
                enrollment['course_id'],
                enrollment['course_name'],
                course_type_display,
                f"{enrollment['credits']}学分",
                enrollment['teacher_name'],
                enrollment['class_time'] or '',
                enrollment['classroom'] or '',
                status_text,
                "可退课"
            ), tags=(offering_id, status_tag))
        
        # 2. 显示pending/accepted/rejected状态的选修课（已投入但可能未确认或已确认/拒绝）
        for bid in pending_bids:
            offering_id = bid['offering_id']
            displayed_offerings.add(offering_id)
            
            bid_status = bid.get('status', 'pending')
            points_bid = bid.get('points_bid', 0)
            
            # 根据竞价状态显示不同的状态文本
            if bid_status == 'pending':
                status_text = f"⏳ 已投入{points_bid}分，等待确认"
                status_tag = "pending"
            elif bid_status == 'accepted':
                status_text = "✓ 选课成功"
                status_tag = "success"
            elif bid_status == 'rejected':
                status_text = "✗ 未选上"
                status_tag = "rejected"
            else:
                status_text = "待处理"
                status_tag = "pending"
            
            tree.insert("", "end", values=(
                bid['course_id'],
                bid['course_name'],
                bid.get('course_type', '选修'),
                f"{bid['credits']}学分",
                bid['teacher_name'],
                bid.get('class_time') or '',
                bid.get('classroom') or '',
                status_text,
                "查看详情"
            ), tags=(offering_id, status_tag))
        
        # 设置标签颜色
        tree.tag_configure("success", foreground="#27AE60")  # 绿色 - 选课成功
        tree.tag_configure("pending", foreground="#E67E22")   # 橙色 - 等待确认
        tree.tag_configure("rejected", foreground="#E74C3C")  # 红色 - 未选上
        
        # 双击退课（仅对已选中的课程）
        tree.bind("<Double-1>", lambda e: self.drop_course_dialog(tree))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 统计信息
        total_enrolled = len(enrolled_courses)
        total_pending = len([b for b in pending_bids if b.get('status') == 'pending'])
        total_credits = sum(e['credits'] for e in enrolled_courses)
        
        info_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0F8FF", corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=15)
        
        info_text = f"已选课程：{total_enrolled} 门"
        if total_pending > 0:
            info_text += f"    待确认：{total_pending} 门"
        info_text += f"    总学分：{total_credits} 分"
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Microsoft YaHei UI", 17, "bold"),
            text_color=self.BUPT_BLUE
        )
        info_label.pack(pady=12, padx=20)
        
        # 提示和图例
        legend_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        legend_frame.pack(pady=5, padx=20, anchor="w")
        
        hint_label = ctk.CTkLabel(
            legend_frame,
            text="提示：双击已选课程可退课，双击等待确认的课程可取消竞价  |  🟢选课成功  🟠等待确认  🔴未选上",
            font=("Microsoft YaHei UI", 13),
            text_color="#666666"
        )
        hint_label.pack(side="left")
    
    def drop_course_dialog(self, tree):
        """退课/取消竞价对话框"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        values = item['values']
        tags = item['tags']
        offering_id = int(tags[0])
        status_tag = tags[1] if len(tags) > 1 else ''
        course_name = values[1]
        
        # 根据状态标签决定操作类型
        if status_tag == 'pending':
            # 等待确认的竞价 -> 取消竞价
            if messagebox.askyesno("确认取消竞价", 
                                   f"确定要取消【{course_name}】的竞价吗？\n已投入的积分将返还到您的账户。"):
                success, message = self.bidding_manager.cancel_bid(self.user.id, offering_id)
                if success:
                    Logger.info(f"学生取消竞价: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
                    messagebox.showinfo("成功", message)
                    self.show_my_courses()  # 刷新
                else:
                    Logger.warning(f"学生取消竞价失败: {self.user.name} ({self.user.id}) - {message}")
                    messagebox.showerror("失败", message)
        
        elif status_tag == 'rejected':
            # 已拒绝的竞价 -> 取消竞价（清理记录）
            if messagebox.askyesno("确认取消竞价", 
                                   f"确定要取消【{course_name}】的竞价吗？\n已投入的积分将返还到您的账户。"):
                success, message = self.bidding_manager.cancel_bid(self.user.id, offering_id)
                if success:
                    Logger.info(f"学生取消竞价: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
                    messagebox.showinfo("成功", message)
                    self.show_my_courses()  # 刷新
                else:
                    Logger.warning(f"学生取消竞价失败: {self.user.name} ({self.user.id}) - {message}")
                    messagebox.showerror("失败", message)
        
        else:
            # 已选课程 -> 退课
            if messagebox.askyesno("确认退课", f"确定要退选【{course_name}】吗？"):
                success, message = self.enrollment_manager.drop_course(self.user.id, offering_id)
                if success:
                    # 获取课程信息用于日志
                    offering_info = self.course_manager.get_offering_by_id(offering_id)
                    course_name_log = offering_info['course_name'] if offering_info else course_name
                    Logger.info(f"学生退课: {self.user.name} ({self.user.id}) - 课程: {course_name_log} (开课ID: {offering_id})")
                    messagebox.showinfo("成功", message)
                    self.show_my_courses()  # 刷新
                else:
                    Logger.warning(f"学生退课失败: {self.user.name} ({self.user.id}) - {message}")
                    messagebox.showerror("失败", message)
    
    def show_course_selection(self):
        """显示课程选课"""
        self.set_active_menu(1)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="课程选课",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 搜索框
        search_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0F8FF", corner_radius=10)
        search_frame.pack(fill="x", padx=20, pady=15)
        
        search_inner_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_inner_frame.pack(pady=15, padx=20)
        
        search_entry = ctk.CTkEntry(
            search_inner_frame,
            placeholder_text="搜索课程名称或代码...",
            width=350,
            height=45,
            font=("Microsoft YaHei UI", 16),
            corner_radius=8
        )
        search_entry.pack(side="left", padx=(0, 10))
        
        # 保存搜索框引用
        self.course_search_entry = search_entry
        
        # 绑定回车键搜索
        search_entry.bind("<Return>", lambda e: self.search_courses(search_entry.get()))
        
        search_button = ctk.CTkButton(
            search_inner_frame,
            text="搜索",
            width=100,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            corner_radius=8,
            command=lambda: self.search_courses(search_entry.get())
        )
        search_button.pack(side="left")
        
        refresh_button = ctk.CTkButton(
            search_inner_frame,
            text="刷新",
            width=100,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_LIGHT_BLUE,
            corner_radius=8,
            command=self.show_course_selection
        )
        refresh_button.pack(side="left", padx=10)
        
        # 获取可选课程
        # 传入当前用户的ID
        courses = self.course_manager.get_available_courses(
            self.user.id
        )
        
        if not courses:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="当前没有可选课程",
                font=("Microsoft YaHei UI", 18),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建表格
        table_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 表格样式
        style = ttk.Style()
        style.configure("Treeview", 
                        font=("Microsoft YaHei UI", 15), 
                        rowheight=45,
                        background="white",
                        foreground="black",
                        fieldbackground="white")
        style.configure("Treeview.Heading", 
                        font=("Microsoft YaHei UI", 16, "bold"),
                        background="#E8F4F8",
                        foreground=self.BUPT_BLUE,
                        relief="flat")
        style.map("Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        tree = ttk.Treeview(
            table_frame,
            columns=("course_id", "course_name", "type", "credits", "teacher", "time", "students", "bidding", "action"),
            show="headings",
            height=15
        )
        
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("type", text="类型")
        tree.heading("credits", text="学分")
        tree.heading("teacher", text="教师")
        tree.heading("time", text="上课时间")
        tree.heading("students", text="选课人数")
        tree.heading("bidding", text="竞价信息")
        tree.heading("action", text="操作")
        
        tree.column("course_id", width=100)
        tree.column("course_name", width=160)
        tree.column("type", width=70)
        tree.column("credits", width=50)
        tree.column("teacher", width=90)
        tree.column("time", width=140)
        tree.column("students", width=90)
        tree.column("bidding", width=100)
        tree.column("action", width=70)
        
        # --- 修复核心逻辑：双重循环遍历 offerings ---
        for course in courses:
            # 遍历该课程下的所有开课班级
            for offering in course.get('offerings', []):
                # 获取原始课程类型
                raw_course_type = course.get('course_type', '')
                offering_id = offering['offering_id']
                
                # 映射课程类型：公共必修/专业必修/学科基础 -> 必修，其他选修类 -> 选修
                if '必修' in raw_course_type or '基础' in raw_course_type:
                    course_type = '必修'
                    display_type = raw_course_type  # 显示原始类型
                elif '选修' in raw_course_type:
                    course_type = '选修'
                    display_type = raw_course_type  # 显示原始类型
                else:
                    course_type = raw_course_type
                    display_type = raw_course_type
                
                # 获取竞价信息（仅选修课）
                bidding_info = ""
                if course_type == '选修':
                    status = self.bidding_manager.get_course_bidding_status(offering_id)
                    if status.get('exists'):
                        pending_bids = status.get('pending_bids', 0)
                        max_students = status.get('max_students', 0)
                        bidding_info = f"{pending_bids}人投入"
                
                tree.insert("", "end", values=(
                    course.get('course_id', ''),
                    course.get('course_name', ''),
                    display_type,
                    f"{course.get('credits', 0)}",
                    offering.get('teacher_name', '未知'),
                    offering.get('class_time', ''),
                    f"{offering.get('current_students', 0)}/{offering.get('max_students', 0)}",
                    bidding_info,
                    "选课"
                ), tags=(offering_id, course_type))
        # ----------------------------------------
        
        tree.bind("<Double-1>", lambda e: self.enroll_course_dialog(tree))
        
        # 保存表格引用，用于搜索功能
        self.course_selection_tree = tree
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        hint_label = ctk.CTkLabel(
            self.content_frame,
            text="提示：双击课程可选课",
            font=("Microsoft YaHei UI", 14),
            text_color="#666666"
        )
        hint_label.pack(pady=5, anchor="w", padx=20)
    
    def enroll_course_dialog(self, tree):
        """选课对话框 - 区分必修课和选修课"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        values = item['values']
        tags = item['tags']
        
        if len(tags) < 2:
            messagebox.showerror("错误", "无法获取课程类型信息")
            return
        
        offering_id = int(tags[0])
        course_type = tags[1]
        course_name = values[1]
        
        # 如果是必修课，直接选课（不需要投标）
        # 支持多种必修类型判断：'必修' 或包含'必修'或'基础'的类型
        if course_type == '必修' or '必修' in course_type or '基础' in course_type:
            if messagebox.askyesno("确认选课", f"确定要选择【{course_name}】吗？"):
                success, message = self.enrollment_manager.enroll_course(
                    self.user.id, offering_id
                )
                if success:
                    Logger.info(f"学生选课(必修): {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
                    messagebox.showinfo("成功", message)
                    self.show_course_selection()  # 刷新
                else:
                    Logger.warning(f"学生选课失败: {self.user.name} ({self.user.id}) - {message}")
                    messagebox.showerror("失败", message)
        
        # 如果是选修课，显示积分投入对话框
        else:
            self.show_bidding_dialog(offering_id, course_name, course_type)
    
    def show_bidding_dialog(self, offering_id: int, course_name: str, course_type: str = '选修'):
        """
        显示积分投入对话框（仅用于选修课）
        
        Args:
            offering_id: 开课ID
            course_name: 课程名称
            course_type: 课程类型（选修）
        """
        # 创建对话框窗口
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"积分投入 - {course_name}")
        dialog.geometry("500x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"500x550+{x}+{y}")
        
        # 创建内容区域和按钮区域的容器
        content_container = ctk.CTkFrame(dialog, fg_color="transparent")
        content_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # 获取学生当前积分
        current_points = self.points_manager.get_student_points(self.user.id)
        
        # 计算已投入的积分总和
        pending_bids = self.db.execute_query("""
            SELECT SUM(points_bid) as total
            FROM course_biddings
            WHERE student_id=? AND status='pending'
        """, (self.user.id,))
        
        total_pending = pending_bids[0].get('total', 0) if pending_bids else 0
        total_pending = total_pending if total_pending is not None else 0
        
        available_points = current_points - total_pending
        
        # 检查是否已经投入过
        existing_bid = self.bidding_manager.get_bid_info(self.user.id, offering_id)
        
        # 获取课程竞价状态
        bidding_status = self.bidding_manager.get_course_bidding_status(offering_id)
        
        # 标题
        title_label = ctk.CTkLabel(
            content_container,
            text="选修课积分投入",
            font=("Microsoft YaHei UI", 22, "bold"),
            text_color=self.BUPT_BLUE
        )
        title_label.pack(pady=15)
        
        # 课程信息框
        info_frame = ctk.CTkFrame(content_container, fg_color="#F0F8FF", corner_radius=10)
        info_frame.pack(fill="x", padx=30, pady=8)
        
        course_label = ctk.CTkLabel(
            info_frame,
            text=f"课程：{course_name}",
            font=("Microsoft YaHei UI", 16),
            text_color="black"
        )
        course_label.pack(pady=10, padx=20, anchor="w")
        
        # 竞价信息
        if bidding_status.get('exists'):
            pending_count = bidding_status.get('pending_bids', 0)
            max_students = bidding_status.get('max_students', 0)
            
            bidding_info_label = ctk.CTkLabel(
                info_frame,
                text=f"已投入人数：{pending_count}  |  课程容量：{max_students}",
                font=("Microsoft YaHei UI", 14),
                text_color="#666666"
            )
            bidding_info_label.pack(pady=5, padx=20, anchor="w")
        
        # 积分信息框
        points_frame = ctk.CTkFrame(content_container, fg_color="#FFF8DC", corner_radius=10)
        points_frame.pack(fill="x", padx=30, pady=8)
        
        total_points_label = ctk.CTkLabel(
            points_frame,
            text=f"总积分：{current_points} 分",
            font=("Microsoft YaHei UI", 15, "bold"),
            text_color=self.BUPT_BLUE
        )
        total_points_label.pack(pady=8, padx=20, anchor="w")
        
        available_points_label = ctk.CTkLabel(
            points_frame,
            text=f"可用积分：{available_points} 分",
            font=("Microsoft YaHei UI", 15, "bold"),
            text_color="#27AE60"
        )
        available_points_label.pack(pady=8, padx=20, anchor="w")
        
        # 如果已投入，显示当前投入信息
        if existing_bid:
            current_bid_points = existing_bid['points_bid']
            current_bid_label = ctk.CTkLabel(
                points_frame,
                text=f"当前投入：{current_bid_points} 分",
                font=("Microsoft YaHei UI", 15, "bold"),
                text_color="#E67E22"
            )
            current_bid_label.pack(pady=8, padx=20, anchor="w")
        
        # 输入框
        input_frame = ctk.CTkFrame(content_container, fg_color="transparent")
        input_frame.pack(pady=15)
        
        input_label = ctk.CTkLabel(
            input_frame,
            text="投入积分：",
            font=("Microsoft YaHei UI", 16),
            text_color="black"
        )
        input_label.pack(side="left", padx=10)
        
        points_entry = ctk.CTkEntry(
            input_frame,
            width=150,
            height=40,
            font=("Microsoft YaHei UI", 16),
            placeholder_text="1-100"
        )
        points_entry.pack(side="left", padx=10)
        
        # 如果已投入，预填充当前积分
        if existing_bid:
            points_entry.insert(0, str(existing_bid['points_bid']))
        
        # 提示信息
        hint_label = ctk.CTkLabel(
            content_container,
            text="提示：选修课必须投入1-100分，不超过剩余积分",
            font=("Microsoft YaHei UI", 13),
            text_color="#666666"
        )
        hint_label.pack(pady=5)
        
        # 按钮框 - 固定在对话框底部
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(side="bottom", pady=15, fill="x")
        
        def on_confirm():
            """确认投入"""
            try:
                points_str = points_entry.get().strip()
                if not points_str:
                    messagebox.showerror("错误", "请输入投入积分", parent=dialog)
                    return
                
                points = int(points_str)
                
                # 选修课必须投入1-100分
                if points < 1 or points > 100:
                    messagebox.showerror("错误", "投入积分必须在1-100之间", parent=dialog)
                    return
                
                if points > available_points:
                    messagebox.showerror("错误", f"积分不足，当前可用{available_points}分", parent=dialog)
                    return
                
                # 如果已投入，调用修改方法
                if existing_bid:
                    success, message = self.bidding_manager.modify_bid(
                        self.user.id, offering_id, points
                    )
                else:
                    # 否则调用投入方法
                    success, message = self.bidding_manager.place_bid(
                        self.user.id, offering_id, points
                    )
                
                if success:
                    Logger.info(f"学生投入积分: {self.user.name} ({self.user.id}) - 课程: {course_name}, 积分: {points}")
                    messagebox.showinfo("成功", message, parent=dialog)
                    dialog.destroy()
                    self.show_course_selection()  # 刷新选课页面
                else:
                    Logger.warning(f"学生投入积分失败: {self.user.name} ({self.user.id}) - {message}")
                    messagebox.showerror("失败", message, parent=dialog)
                    
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字", parent=dialog)
        
        def on_cancel():
            """取消"""
            dialog.destroy()
        
        # 取消按钮（左边，灰色）
        cancel_button = ctk.CTkButton(
            button_frame,
            text="取消",
            width=150,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color="#95A5A6",
            hover_color="#7F8C8D",
            corner_radius=8,
            command=on_cancel
        )
        cancel_button.pack(side="left", padx=10)
        
        # 确认按钮（右边，蓝色）
        confirm_button = ctk.CTkButton(
            button_frame,
            text="确认投入" if not existing_bid else "修改投入",
            width=150,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            corner_radius=8,
            command=on_confirm
        )
        confirm_button.pack(side="left", padx=10)
        
        # 绑定回车键
        points_entry.bind("<Return>", lambda e: on_confirm())
        
        # 聚焦到输入框
        points_entry.focus()
    
    def search_courses(self, keyword):
        """搜索课程"""
        if not hasattr(self, 'course_selection_tree'):
            # 如果表格不存在，先显示选课页面
            self.show_course_selection()
            return
        
        # 清空表格
        for item in self.course_selection_tree.get_children():
            self.course_selection_tree.delete(item)
        
        # 获取所有可选课程 (修复：补全参数)
        all_courses = self.course_manager.get_available_courses(self.user.id)
        
        keyword_lower = keyword.strip().lower() if keyword else ""
        found_any = False

        # 遍历课程
        for course in all_courses:
            # 遍历该课程下的所有开课班级（offering）
            for offering in course.get('offerings', []):
                # 获取匹配所需的字段
                c_name = course.get('course_name', '').lower()
                c_id = course.get('course_id', '').lower()
                t_name = offering.get('teacher_name', '').lower()
                
                # 如果没有关键词，或关键词匹配成功
                if (not keyword_lower) or (keyword_lower in c_name or 
                                           keyword_lower in c_id or 
                                           keyword_lower in t_name):
                    
                    found_any = True
                    
                    # 获取原始课程类型并进行映射
                    raw_course_type = course.get('course_type', '')
                    offering_id = offering['offering_id']
                    
                    # 映射课程类型：公共必修/专业必修/学科基础 -> 必修，其他选修类 -> 选修
                    if '必修' in raw_course_type or '基础' in raw_course_type:
                        course_type = '必修'
                        display_type = raw_course_type  # 显示原始类型
                    elif '选修' in raw_course_type:
                        course_type = '选修'
                        display_type = raw_course_type  # 显示原始类型
                    else:
                        course_type = raw_course_type
                        display_type = raw_course_type
                    
                    # 获取竞价信息（仅选修课）
                    bidding_info = ""
                    if course_type == '选修':
                        status = self.bidding_manager.get_course_bidding_status(offering_id)
                        if status.get('exists'):
                            pending_bids = status.get('pending_bids', 0)
                            bidding_info = f"{pending_bids}人投入"
                    
                    self.course_selection_tree.insert("", "end", values=(
                        course.get('course_id', ''),
                        course.get('course_name', ''),
                        display_type,
                        f"{course.get('credits', 0)}",
                        offering.get('teacher_name', '未知'),
                        offering.get('class_time', ''),
                        f"{offering.get('current_students', 0)}/{offering.get('max_students', 0)}",
                        bidding_info,
                        "选课"
                    ), tags=(offering_id, course_type))

        # 如果没有结果，显示提示
        if not found_any:
            self.course_selection_tree.insert("", "end", values=(
                "", "未找到匹配的课程", "", "", "", "", "", "", ""
            ))
    
    def show_my_grades(self):
        """显示我的成绩"""
        self.set_active_menu(3)
        self.clear_content()
        
        Logger.info(f"学生查看成绩: {self.user.name} ({self.user.id})")
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="我的成绩",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取成绩
        grades = self.grade_manager.get_student_grades(self.user.id)
        
        if not grades:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无成绩记录",
                font=("Microsoft YaHei UI", 18),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # GPA显示
        gpa = self.grade_manager.calculate_student_gpa(self.user.id)
        gpa_frame = ctk.CTkFrame(self.content_frame, fg_color=self.BUPT_BLUE, height=80)
        gpa_frame.pack(fill="x", padx=20, pady=10)
        gpa_frame.pack_propagate(False)
        
        gpa_label = ctk.CTkLabel(
            gpa_frame,
            text=f"总GPA: {gpa}",
            font=("Microsoft YaHei UI", 22, "bold"),
            text_color="white"
        )
        gpa_label.pack(expand=True)
        
        # 创建表格
        table_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 表格样式
        style = ttk.Style()
        style.configure("Treeview", 
                       font=("Microsoft YaHei UI", 15), 
                       rowheight=45,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Treeview.Heading", 
                       font=("Microsoft YaHei UI", 16, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        tree = ttk.Treeview(
            table_frame,
            columns=("course_id", "course_name", "credits", "score", "grade", "gpa", "teacher"),
            show="headings",
            height=12
        )
        
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("score", text="成绩")
        tree.heading("grade", text="等级")
        tree.heading("gpa", text="绩点")
        tree.heading("teacher", text="教师")
        
        tree.column("course_id", width=100)
        tree.column("course_name", width=200)
        tree.column("credits", width=80)
        tree.column("score", width=80)
        tree.column("grade", width=80)
        tree.column("gpa", width=80)
        tree.column("teacher", width=100)
        
        for grade in grades:
            tree.insert("", "end", values=(
                grade['course_id'],
                grade['course_name'],
                grade['credits'],
                grade['score'] if grade['score'] else '未录入',
                grade['grade_level'] or '',
                grade['gpa'] or '',
                grade['teacher_name']
            ))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def show_my_schedule(self):
        """显示我的课表"""
        self.set_active_menu(4)
        self.clear_content()
        
        Logger.info(f"学生查看课表: {self.user.name} ({self.user.id})")
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="我的课表",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取选课记录
        enrollments = self.enrollment_manager.get_student_enrollments(
            self.user.id, status='enrolled'
        )
        
        if not enrollments:
            # 没有选课记录
            no_schedule_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无选课记录\n请前往「课程选课」进行选课",
                font=("Microsoft YaHei UI", 18),
                text_color="#666666",
                justify="center"
            )
            no_schedule_label.pack(pady=100)
            return
        
        # 创建课表框架
        schedule_frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        schedule_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 解析课程时间并构建课表数据
        schedule_data = self._parse_schedule(enrollments)
        
        # 创建课表表格
        self._create_schedule_table(schedule_frame, schedule_data)
        
        # 图例
        legend_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        legend_frame.pack(pady=10, padx=20, anchor="w")
        
        legend_label = ctk.CTkLabel(
            legend_frame,
            text="提示：点击课程可查看详细信息",
            font=("Microsoft YaHei UI", 14),
            text_color="#666666"
        )
        legend_label.pack(side="left", padx=10)
    
    def _parse_schedule(self, enrollments):
        """
        解析选课记录，构建课表数据
        
        Returns:
            dict: {weekday: {period: [course_info, ...]}}
            weekday: 1-5 (周一到周五)
            period: 单节次，如 '1', '2', '3' 等 (1-12)
        """
        schedule_data = {}
        
        # 初始化5天，每天12节课
        for day in range(1, 6):
            schedule_data[day] = {}
            for period in range(1, 13):
                schedule_data[day][str(period)] = []
        
        for enrollment in enrollments:
            class_time = enrollment.get('class_time', '')
            if not class_time:
                continue
            
            course_info = {
                'course_name': enrollment['course_name'],
                'course_id': enrollment['course_id'],
                'teacher_name': enrollment.get('teacher_name', ''),
                'classroom': enrollment.get('classroom', ''),
                'offering_id': enrollment.get('offering_id')
            }
            
            # 解析时间字符串，如 "周一1-2节，周三3-4节" 或 "周一1-3节"
            # 支持中文逗号、英文逗号、顿号等多种分隔符
            time_blocks = re.split(r'[，,、]', class_time)
            
            for block in time_blocks:
                block = block.strip()
                if not block:
                    continue
                
                # 匹配星期和节次，支持多种格式：
                # 1. 周一1-2节、周一1-3节、周一 1-2节、周1第1-2节等（起止节次）
                # 2. 周一12节、周一 12节（单节课）
                pattern_range = r'(周[一二三四五]|周[1-5])\s*(\d+)\s*[-~至]\s*(\d+)\s*[节堂]'
                pattern_single = r'(周[一二三四五]|周[1-5])\s*(\d+)\s*[节堂]'
                
                match = re.search(pattern_range, block)
                if match:
                    # 起止节次格式
                    weekday_str = match.group(1)
                    start_period = int(match.group(2))
                    end_period = int(match.group(3))
                    
                    # 确保节次在合理范围内（1-12节）
                    if start_period < 1 or end_period > 12 or start_period > end_period:
                        continue
                    
                    # 转换星期（支持中文和数字）
                    weekday_map = {
                        '周一': 1, '周二': 2, '周三': 3, '周四': 4, '周五': 5,
                        '周1': 1, '周2': 2, '周3': 3, '周4': 4, '周5': 5
                    }
                    weekday = weekday_map.get(weekday_str)
                    
                    if weekday:
                        # 将连续节次都标记为该课程
                        for period in range(start_period, end_period + 1):
                            period_key = str(period)
                            schedule_data[weekday][period_key].append(course_info)
                
                else:
                    # 尝试匹配单节课格式
                    match = re.search(pattern_single, block)
                    if match:
                        weekday_str = match.group(1)
                        period_num = int(match.group(2))
                        
                        # 确保节次在合理范围内（1-12节）
                        if period_num < 1 or period_num > 12:
                            continue
                        
                        # 转换星期
                        weekday_map = {
                            '周一': 1, '周二': 2, '周三': 3, '周四': 4, '周五': 5,
                            '周1': 1, '周2': 2, '周3': 3, '周4': 4, '周5': 5
                        }
                        weekday = weekday_map.get(weekday_str)
                        
                        if weekday:
                            period_key = str(period_num)
                            schedule_data[weekday][period_key].append(course_info)
        
        return schedule_data
    
    def _create_schedule_table(self, parent_frame, schedule_data):
        """创建课表表格（优化性能版本）"""
        # 定义12个单节次：上午5节（1-5），下午7节（6-12）
        periods = [str(i) for i in range(1, 13)]
        period_names = [f"第{i}节" for i in range(1, 13)]
        weekdays = ['周一', '周二', '周三', '周四', '周五']
        
        # 外层容器
        outer_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        outer_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 表头固定（不滚动）
        header_frame = ctk.CTkFrame(outer_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 2))
        
        # 左上角空白
        empty_label = ctk.CTkLabel(
            header_frame,
            text="",
            width=80,
            height=35,
            fg_color="transparent"
        )
        empty_label.pack(side="left", padx=2)
        
        # 星期列头
        for day in weekdays:
            day_label = ctk.CTkLabel(
                header_frame,
                text=day,
                width=140,
                height=40,
                font=("Microsoft YaHei UI", 15, "bold"),
                fg_color=self.BUPT_BLUE,
                text_color="white",
                corner_radius=8
            )
            day_label.pack(side="left", padx=2)
        
        # 使用原生Canvas实现高性能滚动
        canvas_container = ctk.CTkFrame(outer_frame, fg_color="transparent")
        canvas_container.pack(fill="both", expand=True)
        
        # 创建Canvas和滚动条
        canvas = tk.Canvas(
            canvas_container,
            bg="#F8F9FA",
            highlightthickness=0,
            borderwidth=0
        )
        
        scrollbar = ctk.CTkScrollbar(
            canvas_container,
            orientation="vertical",
            command=canvas.yview
        )
        
        # 内容框架（放在Canvas上）
        content_frame = ctk.CTkFrame(canvas, fg_color="#F8F9FA")
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # 配置滚动
        def configure_scroll_region(event=None):
            canvas.update_idletasks()
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_canvas_width(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind('<Configure>', configure_canvas_width)
        content_frame.bind('<Configure>', configure_scroll_region)
        
        # 鼠标滚轮支持
        def on_mousewheel(event):
            try:
                # 检查 Canvas 是否还存在
                if canvas.winfo_exists():
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                # Canvas 已被销毁，忽略错误
                pass
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 创建12行（每行代表一节课）
        cell_height = 65  # 增加高度以容纳更大的文字
        for i, (period, period_name) in enumerate(zip(periods, period_names)):
            row_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # 时间段标签（左侧）- 优化样式
            period_label_bg = "#E8E8E8" if i < 5 else "#D8E8F0"
            
            period_label = ctk.CTkLabel(
                row_frame,
                text=period_name,
                width=80,
                height=cell_height,
                font=("Microsoft YaHei UI", 13, "bold"),
                fg_color=period_label_bg,
                text_color="black",
                corner_radius=6
            )
            period_label.pack(side="left", padx=2)
            
            # 每天的课程格子
            for day in range(1, 6):
                cell_frame = ctk.CTkFrame(
                    row_frame,
                    width=140,
                    height=cell_height,
                    fg_color="white",
                    border_width=1,
                    border_color="#DDDDDD",
                    corner_radius=6
                )
                cell_frame.pack(side="left", padx=2)
                cell_frame.pack_propagate(False)
                
                # 填充课程内容
                courses = schedule_data.get(day, {}).get(period, [])
                if courses:
                    course = courses[0]  # 通常只有一门课
                    # 处理课程名称显示（限制长度）
                    course_name = course['course_name']
                    if len(course_name) > 10:
                        course_name = course_name[:8] + ".."
                    
                    classroom = course.get('classroom', '')
                    display_text = course_name
                    if classroom:
                        if len(classroom) > 6:
                            classroom = classroom[:4] + ".."
                        display_text = f"{course_name}\n{classroom}"
                    
                    # 创建可点击的课程按钮（优化样式）
                    course_btn = ctk.CTkButton(
                        cell_frame,
                        text=display_text,
                        font=("Microsoft YaHei UI", 11, "bold"),
                        fg_color=self.BUPT_LIGHT_BLUE,
                        hover_color=self.BUPT_BLUE,
                        text_color="white",
                        corner_radius=5,
                        height=cell_height-6,
                        width=136,
                        command=lambda c=course: self._show_course_detail(c)
                    )
                    course_btn.pack(fill="both", expand=True, padx=3, pady=3)
        
        # 初始化滚动区域
        configure_scroll_region()
    
    def _show_course_detail(self, course_info):
        """显示课程详细信息"""
        detail_text = f"课程名称：{course_info['course_name']}\n"
        detail_text += f"课程代码：{course_info['course_id']}\n"
        if course_info.get('teacher_name'):
            detail_text += f"授课教师：{course_info['teacher_name']}\n"
        if course_info.get('classroom'):
            detail_text += f"教室：{course_info['classroom']}"
        
        messagebox.showinfo("课程信息", detail_text)
    
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
        
        # 获取学生当前积分
        current_points = self.points_manager.get_student_points(self.user.id)
        
        infos = [
            ("学号", self.user.id),
            ("姓名", self.user.name),
            ("学院", self.user.extra_info.get('college', '')),
            ("专业", self.user.extra_info.get('major', '')),
            ("年级", self.user.extra_info.get('grade', '')),
            ("班级", self.user.extra_info.get('class_name', '')),
            ("邮箱", self.user.email or ''),
            ("选课积分", f"{current_points} 分")
        ]
        
        for i, (label_text, value) in enumerate(infos):
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
        
        # 添加"查看积分历史"按钮
        button_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        history_button = ctk.CTkButton(
            button_frame,
            text="查看积分历史",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            corner_radius=8,
            command=self.show_points_history
        )
        history_button.pack()
    
    def show_points_history(self):
        """显示积分交易历史记录"""
        # 创建对话框窗口
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("积分历史记录")
        dialog.geometry("900x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f"900x600+{x}+{y}")
        
        # 标题
        title_label = ctk.CTkLabel(
            dialog,
            text="积分交易历史",
            font=("Microsoft YaHei UI", 22, "bold"),
            text_color=self.BUPT_BLUE
        )
        title_label.pack(pady=20)
        
        # 获取积分历史
        history = self.points_manager.get_points_history(self.user.id)
        
        if not history:
            no_data_label = ctk.CTkLabel(
                dialog,
                text="暂无积分交易记录",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建表格框架
        table_frame = ctk.CTkFrame(dialog, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 表格样式
        style = ttk.Style()
        style.configure("History.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=40,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("History.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("History.Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        # 创建Treeview
        tree = ttk.Treeview(
            table_frame,
            columns=("time", "type", "change", "balance", "reason"),
            show="headings",
            style="History.Treeview",
            height=15
        )
        
        # 列标题
        tree.heading("time", text="时间")
        tree.heading("type", text="类型")
        tree.heading("change", text="变化")
        tree.heading("balance", text="余额")
        tree.heading("reason", text="原因")
        
        # 列宽
        tree.column("time", width=150, anchor="center")
        tree.column("type", width=100, anchor="center")
        tree.column("change", width=100, anchor="center")
        tree.column("balance", width=100, anchor="center")
        tree.column("reason", width=350, anchor="w")
        
        # 类型映射
        type_map = {
            'init': '初始化',
            'bid': '投入积分',
            'refund': '退还积分',
            'deduct': '扣除积分',
            'admin_adjust': '管理员调整'
        }
        
        # 插入数据
        for record in history:
            transaction_type = record.get('transaction_type', '')
            type_text = type_map.get(transaction_type, transaction_type)
            
            points_change = record.get('points_change', 0)
            change_text = f"+{points_change}" if points_change > 0 else str(points_change)
            
            # 根据变化类型设置颜色标签
            tag = 'positive' if points_change > 0 else 'negative'
            
            tree.insert("", "end", values=(
                record.get('created_at', '')[:19],  # 只显示到秒
                type_text,
                change_text,
                record.get('balance_after', 0),
                record.get('reason', '') or ''
            ), tags=(tag,))
        
        # 设置标签颜色
        tree.tag_configure("positive", foreground="#27AE60")  # 绿色 - 增加
        tree.tag_configure("negative", foreground="#E74C3C")  # 红色 - 减少
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 关闭按钮
        close_button = ctk.CTkButton(
            dialog,
            text="关闭",
            width=120,
            height=40,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color="#95A5A6",
            corner_radius=8,
            command=dialog.destroy
        )
        close_button.pack(pady=15)
    
    def show_curriculum(self):
        """显示培养方案（增强版：带开课状态和跳转功能）"""
        self.set_active_menu(2)
        self.clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="培养方案",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取学生专业
        major_name = self.user.extra_info.get('major', '')
        if not major_name:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="无法获取您的专业信息，请联系管理员",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 查询培养方案 - 包含学期信息
        sql = """
            SELECT cm.grade, cm.term, cm.course_id, c.course_name, 
                   c.credits, cm.category
            FROM curriculum_matrix cm
            JOIN majors m ON cm.major_id = m.major_id
            JOIN courses c ON cm.course_id = c.course_id
            WHERE m.name = ?
            ORDER BY cm.grade, 
                     CASE cm.term WHEN '秋' THEN 1 WHEN '春' THEN 2 END,
                     cm.category DESC, 
                     cm.course_id
        """
        
        curriculum_data = self.db.execute_query(sql, (major_name,))
        
        if not curriculum_data:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text=f"未找到【{major_name}】专业的培养方案数据",
                font=("Microsoft YaHei UI", 16),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # 查询所有课程的开课状态和学生选课状态
        course_status_map = self._get_course_status_map()
        
        # 使用表格显示（性能更好）
        table_frame = ctk.CTkFrame(self.content_frame, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 表格样式
        style = ttk.Style()
        style.configure("Curriculum.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=35,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Curriculum.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("Curriculum.Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        # 创建表格 - 添加状态列
        tree = ttk.Treeview(
            table_frame,
            columns=("grade_term", "course_id", "course_name", "credits", "category", "status"),
            show="headings",
            style="Curriculum.Treeview",
            height=20
        )
        
        # 设置列标题
        tree.heading("grade_term", text="学期")
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("category", text="类型")
        tree.heading("status", text="状态")
        
        # 设置列宽
        tree.column("grade_term", width=120, anchor="center")
        tree.column("course_id", width=100, anchor="center")
        tree.column("course_name", width=300, anchor="w")
        tree.column("credits", width=70, anchor="center")
        tree.column("category", width=70, anchor="center")
        tree.column("status", width=100, anchor="center")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 插入数据到表格
        for record in curriculum_data:
            grade = record['grade']
            term = record['term']
            course_id = record['course_id']
            course_name = record['course_name']
            credits = record['credits']
            category = record['category']
            
            grade_cn = {1: "一", 2: "二", 3: "三", 4: "四"}.get(grade, str(grade))
            grade_term_text = f"大{grade_cn}（{term}）"
            
            # 获取课程状态
            status_info = course_status_map.get(course_id, {})
            status_text = status_info.get('status_text', '未开课')
            status_tag = status_info.get('status_tag', 'not_offered')
            
            # 插入数据，使用course_id作为tag以便点击时获取
            tag = f"{status_tag}_{course_id}"
            tree.insert("", "end", values=(
                grade_term_text,
                course_id,
                course_name,
                f"{credits}",
                category,
                status_text
            ), tags=(tag,))
        
        # 设置标签颜色和样式
        tree.tag_configure("available", foreground="#27AE60")  # 绿色 - 可选
        tree.tag_configure("enrolled", foreground="#3498DB")   # 蓝色 - 已选
        tree.tag_configure("full", foreground="#E67E22")       # 橙色 - 已满
        tree.tag_configure("not_offered", foreground="#95A5A6") # 灰色 - 未开课
        
        # 绑定双击事件
        tree.bind("<Double-1>", lambda e: self._on_curriculum_course_click(tree))
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加图例说明
        legend_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        legend_frame.pack(pady=10, padx=20, anchor="w")
        
        legend_label = ctk.CTkLabel(
            legend_frame,
            text="提示：双击有开课的课程可跳转到选课页面  |  🟢可选  🔵已选  🟠已满  ⚪未开课",
            font=("Microsoft YaHei UI", 13),
            text_color="#666666"
        )
        legend_label.pack(side="left")
        
        Logger.info(f"学生查看培养方案: {self.user.name} ({major_name})")
    
    def _get_course_status_map(self) -> Dict[str, Dict]:
        """
        获取所有课程的开课状态和学生选课状态
        
        Returns:
            字典，key为course_id，value为状态信息
        """
        status_map = {}
        
        # 查询所有开课信息
        sql_offerings = """
            SELECT co.course_id, co.offering_id, co.current_students, co.max_students
            FROM course_offerings co
            WHERE co.status != 'cancelled'
        """
        offerings = self.db.execute_query(sql_offerings)
        
        # 查询学生已选课程
        sql_enrolled = """
            SELECT co.course_id
            FROM enrollments e
            JOIN course_offerings co ON e.offering_id = co.offering_id
            WHERE e.student_id = ? AND e.status = 'enrolled'
        """
        enrolled_courses = self.db.execute_query(sql_enrolled, (self.user.id,))
        enrolled_course_ids = {row['course_id'] for row in enrolled_courses}
        
        # 构建状态映射
        for offering in offerings:
            course_id = offering['course_id']
            
            # 如果已选，状态为"已选"
            if course_id in enrolled_course_ids:
                status_map[course_id] = {
                    'status_text': '✓ 已选',
                    'status_tag': 'enrolled',
                    'has_offering': True
                }
            # 如果已满，状态为"已满"
            elif offering['current_students'] >= offering['max_students']:
                # 只有在还没有记录或当前记录不是"已选"时才更新为"已满"
                if course_id not in status_map or status_map[course_id]['status_tag'] != 'enrolled':
                    status_map[course_id] = {
                        'status_text': '⚠ 已满',
                        'status_tag': 'full',
                        'has_offering': True
                    }
            # 否则状态为"可选"
            else:
                # 只有在还没有记录时才设置为"可选"
                if course_id not in status_map:
                    status_map[course_id] = {
                        'status_text': '✓ 可选',
                        'status_tag': 'available',
                        'has_offering': True
                    }
        
        return status_map
    
    def _on_curriculum_course_click(self, tree):
        """
        处理培养方案中课程的点击事件
        
        Args:
            tree: Treeview对象
        """
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        tags = item['tags']
        
        if not tags:
            return
        
        # 从tag中提取course_id和status
        tag = tags[0]
        parts = tag.split('_', 1)
        if len(parts) != 2:
            return
        
        status_tag = parts[0]
        course_id = parts[1]
        
        # 如果课程未开课，显示提示
        if status_tag == 'not_offered':
            messagebox.showinfo("提示", "该课程本学期未开课")
            return
        
        # 跳转到选课页面
        self.jump_to_course_selection(course_id)
    
    def jump_to_course_selection(self, course_id: str):
        """
        从培养方案跳转到选课页面并自动搜索该课程
        
        Args:
            course_id: 课程代码
        """
        # 切换到选课页面
        self.show_course_selection()
        
        # 自动填充搜索框并搜索
        if hasattr(self, 'course_search_entry'):
            self.course_search_entry.delete(0, 'end')
            self.course_search_entry.insert(0, course_id)
            self.search_courses(course_id)
    
    def do_logout(self):
        """注销登录"""
        if messagebox.askyesno("确认", "确定要退出登录吗？"):
            self.root.destroy()
            self.logout_callback()
    
    def on_close(self):
        """关闭窗口"""
        self.do_logout()
