"""
学生端主窗口 - 北京邮电大学教学管理系统
提供选课、查成绩、查课表等功能
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import tkinter as tk
import re
from typing import Optional
from pathlib import Path
from PIL import Image
from utils.logger import Logger
from core.course_manager import CourseManager
from core.enrollment_manager import EnrollmentManager
from core.grade_manager import GradeManager


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
        
        # 当前学期
        self.current_semester = "2024-2025-2"
        
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
        """显示我的选课"""
        self.set_active_menu(0)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="我的选课",
            font=("Microsoft YaHei UI", 26, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取选课记录
        enrollments = self.enrollment_manager.get_student_enrollments(
            self.user.id, self.current_semester, 'enrolled'
        )
        
        if not enrollments:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="本学期暂无选课记录",
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
            columns=("course_id", "course_name", "credits", "teacher", "time", "classroom", "action"),
            show="headings",
            height=15
        )
        
        # 列标题
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("teacher", text="授课教师")
        tree.heading("time", text="上课时间")
        tree.heading("classroom", text="教室")
        tree.heading("action", text="操作")
        
        # 列宽
        tree.column("course_id", width=100)
        tree.column("course_name", width=200)
        tree.column("credits", width=80)
        tree.column("teacher", width=100)
        tree.column("time", width=180)
        tree.column("classroom", width=100)
        tree.column("action", width=100)
        
        # 插入数据
        for enrollment in enrollments:
            tree.insert("", "end", values=(
                enrollment['course_id'],
                enrollment['course_name'],
                f"{enrollment['credits']}学分",
                enrollment['teacher_name'],
                enrollment['class_time'] or '',
                enrollment['classroom'] or '',
                "可退课"
            ), tags=(enrollment['offering_id'],))
        
        # 双击退课
        tree.bind("<Double-1>", lambda e: self.drop_course_dialog(tree))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 统计信息
        total_credits = sum(e['credits'] for e in enrollments)
        info_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0F8FF", corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=15)
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=f"已选课程：{len(enrollments)} 门    总学分：{total_credits} 分",
            font=("Microsoft YaHei UI", 17, "bold"),
            text_color=self.BUPT_BLUE
        )
        info_label.pack(pady=12, padx=20)
        
        # 提示
        hint_label = ctk.CTkLabel(
            self.content_frame,
            text="提示：双击课程可退课",
            font=("Microsoft YaHei UI", 14),
            text_color="#666666"
        )
        hint_label.pack(pady=5, anchor="w", padx=20)
    
    def drop_course_dialog(self, tree):
        """退课对话框"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        values = item['values']
        offering_id = int(item['tags'][0])
        
        if messagebox.askyesno("确认退课", f"确定要退选【{values[1]}】吗？"):
            success, message = self.enrollment_manager.drop_course(self.user.id, offering_id)
            if success:
                # 获取课程信息用于日志
                offering_info = self.course_manager.get_offering_by_id(offering_id)
                course_name = offering_info['course_name'] if offering_info else values[1]
                Logger.info(f"学生退课: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
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
        courses = self.course_manager.get_available_courses(self.current_semester)
        
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
            columns=("course_id", "course_name", "type", "credits", "teacher", "time", "students", "action"),
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
        tree.heading("action", text="操作")
        
        tree.column("course_id", width=100)
        tree.column("course_name", width=180)
        tree.column("type", width=80)
        tree.column("credits", width=60)
        tree.column("teacher", width=100)
        tree.column("time", width=160)
        tree.column("students", width=100)
        tree.column("action", width=80)
        
        for course in courses:
            tree.insert("", "end", values=(
                course['course_id'],
                course['course_name'],
                course['course_type'],
                f"{course['credits']}",
                course['teacher_name'],
                course['class_time'] or '',
                f"{course['current_students']}/{course['max_students']}",
                "选课"
            ), tags=(course['offering_id'],))
        
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
        """选课对话框"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        values = item['values']
        offering_id = int(item['tags'][0])
        
        if messagebox.askyesno("确认选课", f"确定要选择【{values[1]}】吗？"):
            success, message = self.enrollment_manager.enroll_course(
                self.user.id, offering_id, self.current_semester
            )
            if success:
                # 获取课程信息用于日志
                offering_info = self.course_manager.get_offering_by_id(offering_id)
                course_name = offering_info['course_name'] if offering_info else values[1]
                Logger.info(f"学生选课: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id}, 学期: {self.current_semester})")
                messagebox.showinfo("成功", message)
                self.show_course_selection()  # 刷新
            else:
                Logger.warning(f"学生选课失败: {self.user.name} ({self.user.id}) - {message}")
                messagebox.showerror("失败", message)
    
    def search_courses(self, keyword):
        """搜索课程"""
        if not hasattr(self, 'course_selection_tree'):
            # 如果表格不存在，先显示选课页面
            self.show_course_selection()
            return
        
        # 清空表格
        for item in self.course_selection_tree.get_children():
            self.course_selection_tree.delete(item)
        
        # 获取所有可选课程
        all_courses = self.course_manager.get_available_courses(self.current_semester)
        
        # 如果没有关键词，显示所有课程
        if not keyword or keyword.strip() == "":
            filtered_courses = all_courses
        else:
            # 过滤课程：搜索课程名称或课程代码
            keyword_lower = keyword.strip().lower()
            filtered_courses = []
            for course in all_courses:
                course_name = course.get('course_name', '').lower()
                course_id = course.get('course_id', '').lower()
                teacher_name = course.get('teacher_name', '').lower()
                
                # 检查是否包含关键词（在课程名称、代码或教师姓名中）
                if (keyword_lower in course_name or 
                    keyword_lower in course_id or 
                    keyword_lower in teacher_name):
                    filtered_courses.append(course)
        
        # 更新表格显示
        if not filtered_courses:
            # 如果没有结果，显示提示
            self.course_selection_tree.insert("", "end", values=(
                "", "未找到匹配的课程", "", "", "", "", "", ""
            ))
        else:
            for course in filtered_courses:
                self.course_selection_tree.insert("", "end", values=(
                    course['course_id'],
                    course['course_name'],
                    course['course_type'],
                    f"{course['credits']}",
                    course['teacher_name'],
                    course['class_time'] or '',
                    f"{course['current_students']}/{course['max_students']}",
                    "选课"
                ), tags=(course['offering_id'],))
    
    def show_my_grades(self):
        """显示我的成绩"""
        self.set_active_menu(2)
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
        grades = self.grade_manager.get_student_grades(self.user.id, self.current_semester)
        
        if not grades:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="本学期暂无成绩记录",
                font=("Microsoft YaHei UI", 18),
                text_color="#666666"
            )
            no_data_label.pack(pady=50)
            return
        
        # GPA显示
        gpa = self.grade_manager.calculate_student_gpa(self.user.id, self.current_semester)
        gpa_frame = ctk.CTkFrame(self.content_frame, fg_color=self.BUPT_BLUE, height=80)
        gpa_frame.pack(fill="x", padx=20, pady=10)
        gpa_frame.pack_propagate(False)
        
        gpa_label = ctk.CTkLabel(
            gpa_frame,
            text=f"本学期GPA: {gpa}",
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
        self.set_active_menu(3)
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
            self.user.id, self.current_semester, 'enrolled'
        )
        
        # 学期信息
        semester_label = ctk.CTkLabel(
            self.content_frame,
            text=f"学期：{self.current_semester}",
            font=("Microsoft YaHei UI", 16),
            text_color="#666666"
        )
        semester_label.pack(pady=8, anchor="w", padx=20)
        
        if not enrollments:
            # 没有选课记录
            no_schedule_label = ctk.CTkLabel(
                self.content_frame,
                text="本学期暂无选课记录\n请前往「课程选课」进行选课",
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
                # 周一1-2节、周一1-3节、周一 1-2节、周1第1-2节等
                pattern = r'(周[一二三四五]|周[1-5])\s*(\d+)\s*[-~至]\s*(\d+)\s*[节堂]'
                match = re.search(pattern, block)
                
                if match:
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
        self.set_active_menu(4)
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
            ("学号", self.user.id),
            ("姓名", self.user.name),
            ("学院", self.user.extra_info.get('college', '')),
            ("专业", self.user.extra_info.get('major', '')),
            ("年级", self.user.extra_info.get('grade', '')),
            ("班级", self.user.extra_info.get('class_name', '')),
            ("邮箱", self.user.email or '')
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
    
    def do_logout(self):
        """注销登录"""
        if messagebox.askyesno("确认", "确定要退出登录吗？"):
            self.root.destroy()
            self.logout_callback()
    
    def on_close(self):
        """关闭窗口"""
        self.do_logout()

