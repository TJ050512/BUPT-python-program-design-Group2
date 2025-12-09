"""
教师端主窗口 - 北京邮电大学教学管理系统
提供成绩录入、查看授课班级、数据分析等功能
"""

import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog
import tkinter as tk
from pathlib import Path
from PIL import Image
from datetime import datetime
from utils.logger import Logger
from core.course_manager import CourseManager
from core.enrollment_manager import EnrollmentManager
from core.grade_manager import GradeManager
from core.points_manager import PointsManager
from core.bidding_manager import BiddingManager
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('TkAgg')


class TeacherWindow:
    """教师端主窗口类"""
    
    # 北邮蓝色主题
    BUPT_BLUE = "#003087"
    BUPT_LIGHT_BLUE = "#0066CC"
    
    def __init__(self, root, user, db, logout_callback):
        """
        初始化教师端窗口
        
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
        self.root.title(f"北京邮电大学教学管理系统 - 教师端 - {user.name}")
        
        window_width = 1300
        window_height = 750
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 配置matplotlib中文字体（支持多平台）
        self._setup_matplotlib_fonts()
        
        # 创建界面
        self.create_widgets()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        Logger.info(f"教师端窗口打开: {user.name}")
    
    def _setup_matplotlib_fonts(self):
        """配置matplotlib中文字体"""
        import platform
        system = platform.system()
        
        if system == 'Darwin':  # macOS
            # macOS系统字体
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'STHeiti']
        elif system == 'Windows':
            # Windows系统字体
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong']
        else:  # Linux
            # Linux系统字体
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'Droid Sans Fallback', 'DejaVu Sans']
        
        # 解决负号显示问题
        plt.rcParams['axes.unicode_minus'] = False
        
        Logger.info(f"matplotlib字体配置完成: {plt.rcParams['font.sans-serif']}")
    
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
            text="北京邮电大学教学管理系统 - 教师端",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color="white"
        )
        title_label.pack(side="left")
        
        # 用户信息
        user_info_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        user_info_frame.pack(side="right", padx=20)
        
        title_text = self.user.extra_info.get('title', '')
        user_label = ctk.CTkLabel(
            user_info_frame,
            text=f"欢迎，{self.user.name} {title_text} ({self.user.id})",
            font=("Microsoft YaHei UI", 14),
            text_color="white"
        )
        user_label.pack(side="left", padx=(0, 10))
        
        logout_button = ctk.CTkButton(
            user_info_frame,
            text="退出登录",
            width=80,
            height=32,
            font=("Microsoft YaHei UI", 12),
            fg_color="transparent",
            border_width=1,
            border_color="white",
            hover_color=self.BUPT_LIGHT_BLUE,
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
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=self.BUPT_BLUE
        )
        menu_title.pack(pady=20)
        
        # 菜单按钮
        self.menu_buttons = []
        
        menus = [
            ("📚 我的课程", self.show_my_courses),
            ("📝 成绩录入", self.show_grade_input),
            ("👥 学生名单", self.show_students_list),
            ("🎯 选课管理", self.show_enrollment_management),
            ("📊 数据分析", self.show_data_analysis),
            ("👤 个人信息", self.show_personal_info)
        ]
        
        for text, command in menus:
            btn = ctk.CTkButton(
                left_menu,
                text=text,
                width=180,
                height=45,
                font=("Microsoft YaHei UI", 14),
                fg_color="transparent",
                text_color="gray",
                hover_color=self.BUPT_LIGHT_BLUE,
                anchor="w",
                command=command
            )
            btn.pack(pady=5, padx=10)
            self.menu_buttons.append(btn)
        
        # 右侧内容区
        self.content_frame = ctk.CTkFrame(main_container, fg_color="white")
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # 默认显示我的课程
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
        """显示我的课程"""
        self.set_active_menu(0)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="我的课程",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取授课列表
        courses = self.course_manager.get_teacher_courses(self.user.id)
        
        if not courses:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无授课课程",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_data_label.pack(pady=50)
            return
        
        # 创建课程卡片
        cards_frame = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        cards_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for course in courses:
            self.create_course_card(cards_frame, course)
    
    def create_course_card(self, parent, course):
        """创建课程卡片"""
        card = ctk.CTkFrame(parent, fg_color="#F8F9FA", corner_radius=10)
        card.pack(fill="x", pady=10)
        
        # 课程信息
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(fill="x", padx=20, pady=15)
        
        # 左侧信息
        left_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        course_title = ctk.CTkLabel(
            left_frame,
            text=f"{course['course_id']} - {course['course_name']}",
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=self.BUPT_BLUE
        )
        course_title.pack(anchor="w")
        
        course_info = ctk.CTkLabel(
            left_frame,
            text=f"学分：{course['credits']}  |  上课时间：{course['class_time'] or '未安排'}  |  教室：{course['classroom'] or '未安排'}",
            font=("Microsoft YaHei UI", 12),
            text_color="gray"
        )
        course_info.pack(anchor="w", pady=(5, 0))
        
        student_info = ctk.CTkLabel(
            left_frame,
            text=f"选课人数：{course['current_students']}/{course['max_students']}",
            font=("Microsoft YaHei UI", 12),
            text_color="gray"
        )
        student_info.pack(anchor="w", pady=(5, 0))
    
    def query_students_list(self):
        """查询学生名单"""
        if not hasattr(self, 'students_course_combo') or not hasattr(self, 'students_courses_list'):
            return
        
        selected_course = self.students_course_combo.get()
        if not selected_course:
            return
        
        # 找到选中的课程（通过下拉框的值匹配）
        # 构建完整的课程名称列表（与下拉框中的格式一致）
        course_names = []
        for c in self.students_courses_list:
            course_name = f"{c['course_name']} ({c['course_id']})"
            if c.get('class_time') or c.get('classroom'):
                details = []
                if c.get('class_time'):
                    details.append(c['class_time'])
                if c.get('classroom'):
                    details.append(c['classroom'])
                if details:
                    course_name += f" - {' | '.join(details)}"
            course_names.append(course_name)
        
        try:
            index = course_names.index(selected_course)
            offering_id = self.students_courses_list[index]['offering_id']
            course_name = self.students_courses_list[index]['course_name']
            self.display_students_in_content(offering_id, course_name)
        except ValueError:
            pass
    
    def display_students_in_content(self, offering_id, course_name):
        """在当前界面显示学生名单"""
        # 清除之前的显示内容（如果存在）
        if self.students_display_container is not None:
            self.students_display_container.destroy()
        
        # 创建显示容器
        self.students_display_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.students_display_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 创建分隔线
        separator = ctk.CTkFrame(self.students_display_container, height=2, fg_color="#E0E0E0")
        separator.pack(fill="x", pady=(0, 15))
        
        # 课程信息标题
        course_title = ctk.CTkLabel(
            self.students_display_container,
            text=f"{course_name} - 学生名单",
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color=self.BUPT_BLUE
        )
        course_title.pack(pady=(0, 15), anchor="w")
        
        # 获取学生名单
        students = self.enrollment_manager.get_course_students(offering_id)
        
        # 创建表格框架
        table_frame = ctk.CTkFrame(self.students_display_container)
        table_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        if not students:
            no_students_label = ctk.CTkLabel(
                table_frame,
                text="该课程暂无学生选课",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_students_label.pack(pady=50)
            
            # 统计信息
            count_label = ctk.CTkLabel(
                self.students_display_container,
                text="共 0 名学生",
                font=("Microsoft YaHei UI", 14),
                text_color=self.BUPT_BLUE
            )
            count_label.pack(pady=10, anchor="w")
            return
        
        # 获取所有学生的成绩信息
        grades = self.grade_manager.get_course_grades(offering_id)
        # 创建成绩字典，key为enrollment_id，value为成绩信息
        grade_dict = {g['enrollment_id']: g for g in grades}
        
        # 配置表格样式
        style = ttk.Style()
        style.configure("Student.Treeview", 
                       font=("Microsoft YaHei UI", 15), 
                       rowheight=45,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Student.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 16, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("Student.Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        # 创建表格
        tree = ttk.Treeview(
            table_frame,
            columns=("student_id", "name", "major", "class", "score", "grade", "enrollment_date"),
            show="headings",
            height=18,
            style="Student.Treeview"
        )
        
        tree.heading("student_id", text="学号")
        tree.heading("name", text="姓名")
        tree.heading("major", text="专业")
        tree.heading("class", text="班级")
        tree.heading("score", text="成绩")
        tree.heading("grade", text="等级")
        tree.heading("enrollment_date", text="选课日期")
        
        tree.column("student_id", width=140)
        tree.column("name", width=130)
        tree.column("major", width=200)
        tree.column("class", width=110)
        tree.column("score", width=100)
        tree.column("grade", width=90)
        tree.column("enrollment_date", width=180)
        
        for student in students:
            enrollment_id = student['enrollment_id']
            grade_info = grade_dict.get(enrollment_id)
            
            # 成绩显示
            if grade_info and grade_info.get('score') is not None:
                score_text = f"{grade_info['score']:.1f}"
                grade_text = grade_info.get('grade_level', '')
            else:
                score_text = "无"
                grade_text = ""
            
            tree.insert("", "end", values=(
                student['student_id'],
                student['student_name'],
                student['major'] or '',
                student['class_name'] or '',
                score_text,
                grade_text,
                student['enrollment_date']
            ))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 统计信息
        count_label = ctk.CTkLabel(
            self.students_display_container,
            text=f"共 {len(students)} 名学生",
            font=("Microsoft YaHei UI", 17, "bold"),
            text_color=self.BUPT_BLUE
        )
        count_label.pack(pady=15, anchor="w")
    
    def view_course_students(self, offering_id, course_name):
        """查看课程学生名单（保持兼容性，仍可用于从课程卡片查看）"""
        Logger.info(f"教师查看学生名单: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
        # 如果当前在学生名单页面，直接显示在当前界面
        # 否则保持原来的新窗口方式
        if hasattr(self, 'students_display_container') and hasattr(self, 'students_courses_list'):
            # 尝试切换到学生名单页面并显示
            self.show_students_list()
            # 设置下拉框并显示
            course_names = [f"{c['course_name']} ({c['course_id']})" for c in self.students_courses_list]
            try:
                # 找到对应的课程索引
                for i, course in enumerate(self.students_courses_list):
                    if course['offering_id'] == offering_id:
                        if i < len(course_names):
                            self.students_course_combo.set(course_names[i])
                        self.display_students_in_content(offering_id, course_name)
                        break
            except:
                pass
        else:
            # 创建新窗口（兼容旧的行为）
            students = self.enrollment_manager.get_course_students(offering_id)
            
            dialog = ctk.CTkToplevel(self.root)
            dialog.title(f"学生名单 - {course_name}")
            dialog.geometry("1100x600")
            
            title = ctk.CTkLabel(
                dialog,
                text=f"{course_name} - 学生名单",
                font=("Microsoft YaHei UI", 18, "bold")
            )
            title.pack(pady=20)
            
            # 获取所有学生的成绩信息
            grades = self.grade_manager.get_course_grades(offering_id)
            grade_dict = {g['enrollment_id']: g for g in grades}
            
            # 配置表格样式
            style = ttk.Style()
            style.configure("StudentDialog.Treeview", 
                           font=("Microsoft YaHei UI", 15), 
                           rowheight=45,
                           background="white",
                           foreground="black",
                           fieldbackground="white")
            style.configure("StudentDialog.Treeview.Heading", 
                           font=("Microsoft YaHei UI", 16, "bold"),
                           background="#E8F4F8",
                           foreground=self.BUPT_BLUE,
                           relief="flat")
            style.map("StudentDialog.Treeview.Heading",
                     background=[("active", "#D0E8F0")])
            
            # 创建表格
            table_frame = ctk.CTkFrame(dialog)
            table_frame.pack(fill="both", expand=True, padx=20, pady=10)
            
            tree = ttk.Treeview(
                table_frame,
                columns=("student_id", "name", "major", "class", "score", "grade", "enrollment_date"),
                show="headings",
                height=15,
                style="StudentDialog.Treeview"
            )
            
            tree.heading("student_id", text="学号")
            tree.heading("name", text="姓名")
            tree.heading("major", text="专业")
            tree.heading("class", text="班级")
            tree.heading("score", text="成绩")
            tree.heading("grade", text="等级")
            tree.heading("enrollment_date", text="选课日期")
            
            tree.column("student_id", width=140)
            tree.column("name", width=130)
            tree.column("major", width=200)
            tree.column("class", width=110)
            tree.column("score", width=100)
            tree.column("grade", width=90)
            tree.column("enrollment_date", width=180)
            
            for student in students:
                enrollment_id = student['enrollment_id']
                grade_info = grade_dict.get(enrollment_id)
                
                # 成绩显示
                if grade_info and grade_info.get('score') is not None:
                    score_text = f"{grade_info['score']:.1f}"
                    grade_text = grade_info.get('grade_level', '')
                else:
                    score_text = "无"
                    grade_text = ""
                
                tree.insert("", "end", values=(
                    student['student_id'],
                    student['student_name'],
                    student['major'] or '',
                    student['class_name'] or '',
                    score_text,
                    grade_text,
                    student['enrollment_date']
                ))
            
            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            close_btn = ctk.CTkButton(
                dialog,
                text="关闭",
                width=100,
                command=dialog.destroy
            )
            close_btn.pack(pady=10)
    
    def input_grades_for_course(self, offering_id, course_name):
        """为课程录入成绩"""
        # 切换到成绩录入页面
        self.show_grade_input(offering_id, course_name)
    
    def show_grade_input(self, offering_id=None, course_name=None):
        """显示成绩录入"""
        self.set_active_menu(1)
        self.clear_content()
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="成绩录入",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="#1a1a1a"  # 深色文字，更清晰
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 如果没有指定课程，显示课程选择
        if offering_id is None:
            courses = self.course_manager.get_teacher_courses(self.user.id)
            
            if not courses:
                no_data_label = ctk.CTkLabel(
                    self.content_frame,
                    text="暂无授课课程",
                    font=("Microsoft YaHei UI", 14),
                    text_color="gray"
                )
                no_data_label.pack(pady=50)
                return
            
            # 显示课程列表
            hint_label = ctk.CTkLabel(
                self.content_frame,
                text="请选择要录入成绩的课程：",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            hint_label.pack(pady=10, anchor="w", padx=20)
            
            for course in courses:
                card = ctk.CTkFrame(self.content_frame, fg_color="#F8F9FA")
                card.pack(fill="x", padx=20, pady=5)
                
                # 左侧：课程信息
                info_frame = ctk.CTkFrame(card, fg_color="transparent")
                info_frame.pack(side="left", fill="x", expand=True, padx=20, pady=15)
                
                # 课程名称和代码
                course_label = ctk.CTkLabel(
                    info_frame,
                    text=f"{course['course_name']} ({course['course_id']})",
                    font=("Microsoft YaHei UI", 14, "bold"),
                    text_color="black"
                )
                course_label.pack(anchor="w")
                
                # 上课时间和教室
                time_classroom_text = ""
                if course.get('class_time'):
                    time_classroom_text = f"上课时间：{course['class_time']}"
                if course.get('classroom'):
                    if time_classroom_text:
                        time_classroom_text += f"  |  教室：{course['classroom']}"
                    else:
                        time_classroom_text = f"教室：{course['classroom']}"
                
                if time_classroom_text:
                    time_label = ctk.CTkLabel(
                        info_frame,
                        text=time_classroom_text,
                        font=("Microsoft YaHei UI", 12),
                        text_color="#666666"
                    )
                    time_label.pack(anchor="w", pady=(5, 0))
                
                select_btn = ctk.CTkButton(
                    card,
                    text="选择",
                    width=100,
                    fg_color=self.BUPT_BLUE,
                    command=lambda o=course['offering_id'], n=course['course_name']: self.show_grade_input(o, n)
                )
                select_btn.pack(side="right", padx=20, pady=10)
            
            return
        
        # 显示选中课程的成绩录入界面
        # 获取课程详细信息（包括时间和教室）
        offering_info = self.course_manager.get_offering_by_id(offering_id)
        
        # 课程信息卡片
        course_card = ctk.CTkFrame(self.content_frame, fg_color="#F0F7FF", corner_radius=10)
        course_card.pack(fill="x", padx=20, pady=(10, 20))
        
        course_info_frame = ctk.CTkFrame(course_card, fg_color="transparent")
        course_info_frame.pack(fill="x", padx=20, pady=15)
        
        # 左侧：课程名称和时间信息
        left_info_frame = ctk.CTkFrame(course_info_frame, fg_color="transparent")
        left_info_frame.pack(side="left", fill="x", expand=True)
        
        course_label = ctk.CTkLabel(
            left_info_frame,
            text=f"课程：{course_name}",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color=self.BUPT_BLUE
        )
        course_label.pack(anchor="w")
        
        # 显示上课时间和教室
        if offering_info:
            time_classroom_text = ""
            if offering_info.get('class_time'):
                time_classroom_text = f"上课时间：{offering_info['class_time']}"
            if offering_info.get('classroom'):
                if time_classroom_text:
                    time_classroom_text += f"  |  教室：{offering_info['classroom']}"
                else:
                    time_classroom_text = f"教室：{offering_info['classroom']}"
            
            if time_classroom_text:
                time_label = ctk.CTkLabel(
                    left_info_frame,
                    text=time_classroom_text,
                    font=("Microsoft YaHei UI", 13),
                    text_color="#666666"
                )
                time_label.pack(anchor="w", pady=(5, 0))
        
        # 获取学生名单和成绩
        students = self.enrollment_manager.get_course_students(offering_id)
        grades = self.grade_manager.get_course_grades(offering_id)
        
        # 统计信息
        entered_count = len([g for g in grades if g.get('score')])
        total_count = len(students)
        
        stats_label = ctk.CTkLabel(
            course_info_frame,
            text=f"已录入：{entered_count}/{total_count}",
            font=("Microsoft YaHei UI", 14),
            text_color="gray"
        )
        stats_label.pack(side="right")
        
        # 创建成绩字典
        grade_dict = {g['enrollment_id']: g for g in grades}
        
        # 创建表格容器
        table_container = ctk.CTkFrame(self.content_frame, fg_color="#F8F9FA")
        table_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # 配置Treeview样式，增大字体和行高
        style = ttk.Style()
        style.configure("Grade.Treeview", 
                       font=("Microsoft YaHei UI", 15),
                       rowheight=45)  # 增大行高
        style.configure("Grade.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 16, "bold"),
                       background=self.BUPT_BLUE,
                       foreground="white",
                       padding=10)  # 增加表头内边距
        style.map("Grade.Treeview", 
                 background=[('selected', self.BUPT_LIGHT_BLUE)])
        
        # 创建表格
        table_frame = ctk.CTkFrame(table_container, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        tree = ttk.Treeview(
            table_frame,
            columns=("student_id", "name", "major", "score", "grade", "gpa", "action"),
            show="headings",
            height=18,
            style="Grade.Treeview"
        )
        
        tree.heading("student_id", text="学号")
        tree.heading("name", text="姓名")
        tree.heading("major", text="专业")
        tree.heading("score", text="成绩")
        tree.heading("grade", text="等级")
        tree.heading("gpa", text="绩点")
        tree.heading("action", text="操作")
        
        # 增大列宽以适应更大的字体
        tree.column("student_id", width=150, anchor="center")
        tree.column("name", width=130, anchor="center")
        tree.column("major", width=200, anchor="center")
        tree.column("score", width=120, anchor="center")
        tree.column("grade", width=100, anchor="center")
        tree.column("gpa", width=100, anchor="center")
        tree.column("action", width=130, anchor="center")
        
        # 交替行颜色和成绩状态标签
        for i, student in enumerate(students):
            enrollment_id = student['enrollment_id']
            grade = grade_dict.get(enrollment_id)
            
            score_text = f"{grade['score']:.1f}" if grade and grade.get('score') else '未录入'
            grade_text = grade['grade_level'] if grade and grade.get('grade_level') else ''
            gpa_text = f"{grade['gpa']:.2f}" if grade and grade.get('gpa') else ''
            
            # 根据是否有成绩设置标签
            tag = 'graded' if (grade and grade.get('score')) else 'ungraded'
            
            tree.insert("", "end", values=(
                student['student_id'],
                student['student_name'],
                student['major'] or '未设置',
                score_text,
                grade_text,
                gpa_text,
                "点击录入/修改"
            ), tags=(enrollment_id, tag))
        
        # 设置标签颜色
        tree.tag_configure('graded', background="#E8F5E9")  # 浅绿色背景表示已录入
        tree.tag_configure('ungraded', background="#FFF3E0")  # 浅橙色背景表示未录入
        
        # 双击录入成绩
        tree.bind("<Double-1>", lambda e: self.input_grade_dialog(tree, offering_id))
        # 单击高亮
        tree.bind("<Button-1>", lambda e: self._on_tree_select(tree))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 提示信息
        hint_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        hint_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        hint_label = ctk.CTkLabel(
            hint_frame,
            text="💡 提示：双击学生行可录入或修改成绩",
            font=("Microsoft YaHei UI", 13),
            text_color="gray"
        )
        hint_label.pack(side="left")
        
        # 图例
        legend_frame = ctk.CTkFrame(hint_frame, fg_color="transparent")
        legend_frame.pack(side="right")
        
        graded_legend = ctk.CTkLabel(
            legend_frame,
            text="已录入",
            font=("Microsoft YaHei UI", 12),
            text_color="#4CAF50",
            width=60,
            height=20,
            fg_color="#E8F5E9",
            corner_radius=3
        )
        graded_legend.pack(side="right", padx=5)
        
        ungraded_legend = ctk.CTkLabel(
            legend_frame,
            text="未录入",
            font=("Microsoft YaHei UI", 12),
            text_color="#FF9800",
            width=60,
            height=20,
            fg_color="#FFF3E0",
            corner_radius=3
        )
        ungraded_legend.pack(side="right", padx=5)
        
        # 保存tree引用以便刷新
        self.grade_tree = tree
        self.grade_offering_id = offering_id
        self.grade_course_name = course_name
    
    def _on_tree_select(self, tree):
        """处理树形视图选择事件"""
        pass  # 占位方法，可以根据需要添加功能
    
    def input_grade_dialog(self, tree, offering_id):
        """录入成绩对话框 - 自定义美观对话框"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        values = item['values']
        enrollment_id = int(item['tags'][0])
        
        current_score_str = values[3] if values[3] != '未录入' else ''
        try:
            current_score = float(current_score_str) if current_score_str else None
        except:
            current_score = None
        
        student_name = values[1]
        student_id = values[0]
        
        # 创建自定义对话框
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("录入成绩")
        dialog.geometry("480x420")
        dialog.resizable(False, False)
        
        # 居中显示
        dialog.transient(self.root)
        dialog.grab_set()  # 模态对话框
        
        # 计算居中位置
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (480 // 2)
        y = (dialog.winfo_screenheight() // 2) - (420 // 2)
        dialog.geometry(f"480x420+{x}+{y}")
        
        # 主容器
        main_frame = ctk.CTkFrame(dialog, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 标题区域
        header_frame = ctk.CTkFrame(main_frame, fg_color=self.BUPT_BLUE, height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="录入成绩",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(expand=True)
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="white")
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # 学生信息卡片
        info_card = ctk.CTkFrame(content_frame, fg_color="#F0F7FF", corner_radius=10)
        info_card.pack(fill="x", pady=(0, 25))
        
        # 学生姓名
        name_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=15)
        
        name_label_text = ctk.CTkLabel(
            name_frame,
            text="学生姓名：",
            font=("Microsoft YaHei UI", 16),
            text_color="gray",
            width=100,
            anchor="w"
        )
        name_label_text.pack(side="left")
        
        name_label_value = ctk.CTkLabel(
            name_frame,
            text=student_name,
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=self.BUPT_BLUE
        )
        name_label_value.pack(side="left", padx=(10, 0))
        
        # 学号
        id_frame = ctk.CTkFrame(info_card, fg_color="transparent")
        id_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        id_label_text = ctk.CTkLabel(
            id_frame,
            text="学号：",
            font=("Microsoft YaHei UI", 16),
            text_color="gray",
            width=100,
            anchor="w"
        )
        id_label_text.pack(side="left")
        
        id_label_value = ctk.CTkLabel(
            id_frame,
            text=student_id,
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=self.BUPT_BLUE
        )
        id_label_value.pack(side="left", padx=(10, 0))
        
        # 成绩输入区域
        score_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        score_frame.pack(fill="x", pady=(0, 15))
        
        score_label = ctk.CTkLabel(
            score_frame,
            text="请输入成绩（0-100分）：",
            font=("Microsoft YaHei UI", 16),
            text_color="black"
        )
        score_label.pack(anchor="w", pady=(0, 10))
        
        # 成绩输入框
        score_var = ctk.StringVar(value=str(current_score) if current_score is not None else "")
        score_entry = ctk.CTkEntry(
            score_frame,
            textvariable=score_var,
            width=300,
            height=50,
            font=("Microsoft YaHei UI", 20, "bold"),
            placeholder_text="0-100",
            border_color=self.BUPT_BLUE,
            border_width=2,
            fg_color="white",
            text_color="black",
            corner_radius=8
        )
        score_entry.pack(anchor="w")
        score_entry.select_range(0, 'end')  # 选中所有文本
        score_entry.focus()  # 获得焦点
        
        # 快速输入按钮
        quick_buttons_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        quick_buttons_frame.pack(fill="x", pady=(0, 20))
        
        quick_label = ctk.CTkLabel(
            quick_buttons_frame,
            text="快速输入：",
            font=("Microsoft YaHei UI", 14),
            text_color="gray"
        )
        quick_label.pack(side="left", padx=(0, 10))
        
        quick_scores = [90, 80, 70, 60]
        for qs in quick_scores:
            btn = ctk.CTkButton(
                quick_buttons_frame,
                text=str(qs),
                width=60,
                height=35,
                font=("Microsoft YaHei UI", 14, "bold"),
                fg_color=self.BUPT_LIGHT_BLUE,
                hover_color=self.BUPT_BLUE,
                command=lambda s=qs: score_var.set(str(s))
            )
            btn.pack(side="left", padx=5)
        
        # 按钮区域
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        def confirm_input():
            try:
                score_text = score_var.get().strip()
                if not score_text:
                    messagebox.showwarning("提示", "请输入成绩")
                    return
                
                score = float(score_text)
                if score < 0 or score > 100:
                    messagebox.showwarning("提示", "成绩必须在0-100分之间")
                    return
                
                # 提交成绩
                success, message = self.grade_manager.input_grade(
                    enrollment_id, score, self.user.id
                )
                
                if success:
                    # 获取课程信息用于日志
                    offering_info = self.course_manager.get_offering_by_id(offering_id)
                    course_name = offering_info['course_name'] if offering_info else "未知课程"
                    Logger.info(f"教师录入成绩: {self.user.name} ({self.user.id}) - 学生: {student_name} ({student_id}) - 课程: {course_name} - 成绩: {score}分")
                    dialog.destroy()
                    messagebox.showinfo("成功", f"成绩录入成功！\n{student_name}：{score}分")
                    # 刷新当前界面
                    if hasattr(self, 'grade_course_name'):
                        self.show_grade_input(offering_id, self.grade_course_name)
                    else:
                        self.show_grade_input(offering_id, "")
                else:
                    Logger.warning(f"教师录入成绩失败: {self.user.name} ({self.user.id}) - 学生: {student_name} ({student_id}) - {message}")
                    messagebox.showerror("失败", message)
                    
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
            except Exception as e:
                messagebox.showerror("错误", f"录入失败：{str(e)}")
        
        def cancel_input():
            dialog.destroy()
        
        # 确定按钮
        confirm_btn = ctk.CTkButton(
            button_frame,
            text="确认录入",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=confirm_input
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
            command=cancel_input
        )
        cancel_btn.pack(side="right")
        
        # 绑定回车键确认
        score_entry.bind('<Return>', lambda e: confirm_input())
        score_entry.bind('<Escape>', lambda e: cancel_input())
        
        # 对话框关闭事件
        dialog.protocol("WM_DELETE_WINDOW", cancel_input)
    
    def show_students_list(self):
        """显示学生名单（所有授课课程）"""
        self.set_active_menu(2)
        self.clear_content()
        
        Logger.info(f"教师查看学生名单页面: {self.user.name} ({self.user.id})")
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="学生名单",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取所有授课课程
        courses = self.course_manager.get_teacher_courses(self.user.id)
        
        if not courses:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无授课课程",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_data_label.pack(pady=50)
            return
        
        # 课程选择
        course_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        course_frame.pack(fill="x", padx=20, pady=10)
        
        label = ctk.CTkLabel(
            course_frame,
            text="选择课程：",
            font=("Microsoft YaHei UI", 14)
        )
        label.pack(side="left", padx=(0, 10))
        
        # 构建课程名称列表，包含时间和教室信息以便区分
        course_names = []
        for c in courses:
            course_name = f"{c['course_name']} ({c['course_id']})"
            if c.get('class_time') or c.get('classroom'):
                details = []
                if c.get('class_time'):
                    details.append(c['class_time'])
                if c.get('classroom'):
                    details.append(c['classroom'])
                if details:
                    course_name += f" - {' | '.join(details)}"
            course_names.append(course_name)
        
        self.students_course_combo = ctk.CTkComboBox(
            course_frame,
            values=course_names,
            width=500,
            font=("Microsoft YaHei UI", 12)
        )
        self.students_course_combo.pack(side="left")
        self.students_course_combo.set(course_names[0] if course_names else "")
        
        # 存储课程列表供查询使用
        self.students_courses_list = courses
        
        # 查询按钮
        query_btn = ctk.CTkButton(
            course_frame,
            text="查询",
            width=80,
            fg_color=self.BUPT_BLUE,
            command=self.query_students_list
        )
        query_btn.pack(side="left", padx=10)
        
        # 学生名单显示区域容器
        self.students_display_container = None
        
        # 默认显示第一门课程的学生名单
        if courses:
            self.display_students_in_content(courses[0]['offering_id'], courses[0]['course_name'])
    
    def show_enrollment_management(self):
        """显示选课管理 - 包含选课学生列表和积分竞价信息"""
        self.set_active_menu(3)
        self.clear_content()
        
        Logger.info(f"教师查看选课管理页面: {self.user.name} ({self.user.id})")
        
        # 标题
        title = ctk.CTkLabel(
            self.content_frame,
            text="选课管理",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取所有授课课程
        courses = self.course_manager.get_teacher_courses(self.user.id)
        
        if not courses:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无授课课程",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_data_label.pack(pady=50)
            return
        
        # 课程选择
        course_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        course_frame.pack(fill="x", padx=20, pady=10)
        
        label = ctk.CTkLabel(
            course_frame,
            text="选择课程：",
            font=("Microsoft YaHei UI", 14)
        )
        label.pack(side="left", padx=(0, 10))
        
        # 构建课程名称列表
        course_names = []
        for c in courses:
            course_name = f"{c['course_name']} ({c['course_id']})"
            if c.get('class_time') or c.get('classroom'):
                details = []
                if c.get('class_time'):
                    details.append(c['class_time'])
                if c.get('classroom'):
                    details.append(c['classroom'])
                if details:
                    course_name += f" - {' | '.join(details)}"
            course_names.append(course_name)
        
        self.enrollment_course_combo = ctk.CTkComboBox(
            course_frame,
            values=course_names,
            width=500,
            font=("Microsoft YaHei UI", 12),
            command=self.on_enrollment_course_selected
        )
        self.enrollment_course_combo.pack(side="left")
        self.enrollment_course_combo.set(course_names[0] if course_names else "")
        
        # 存储课程列表供查询使用
        self.enrollment_courses_list = courses
        
        # 查询按钮
        query_btn = ctk.CTkButton(
            course_frame,
            text="查询",
            width=80,
            fg_color=self.BUPT_BLUE,
            command=self.query_enrollment_info
        )
        query_btn.pack(side="left", padx=10)
        
        # 选课信息显示区域容器
        self.enrollment_display_container = None
        
        # 默认显示第一门课程的选课信息
        if courses:
            self.display_enrollment_info(courses[0]['offering_id'], courses[0])
    
    def on_enrollment_course_selected(self, choice):
        """课程选择改变时的回调"""
        try:
            index = self.enrollment_course_combo.cget("values").index(choice)
            offering_id = self.enrollment_courses_list[index]['offering_id']
            course_info = self.enrollment_courses_list[index]
            self.display_enrollment_info(offering_id, course_info)
        except (ValueError, IndexError):
            pass
    
    def query_enrollment_info(self):
        """查询选课信息"""
        try:
            choice = self.enrollment_course_combo.get()
            index = self.enrollment_course_combo.cget("values").index(choice)
            offering_id = self.enrollment_courses_list[index]['offering_id']
            course_info = self.enrollment_courses_list[index]
            self.display_enrollment_info(offering_id, course_info)
        except (ValueError, IndexError):
            messagebox.showerror("错误", "请选择有效的课程")
    
    def display_enrollment_info(self, offering_id, course_info):
        """显示选课信息（包括已选学生和积分竞价）"""
        # 保存当前课程信息，供刷新使用
        self.current_enrollment_course_info = course_info
        self.current_enrollment_offering_id = offering_id
        
        # 清除之前的显示内容
        if self.enrollment_display_container is not None:
            self.enrollment_display_container.destroy()
        
        # 创建显示容器
        self.enrollment_display_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.enrollment_display_container.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 分隔线
        separator = ctk.CTkFrame(self.enrollment_display_container, height=2, fg_color="#E0E0E0")
        separator.pack(fill="x", pady=(0, 15))
        
        course_name = course_info['course_name']
        course_id = course_info['course_id']
        course_type = course_info.get('course_type', '')
        is_elective = course_type != '必修' and '必修' not in course_type and '基础' not in course_type
        
        # 课程信息标题
        course_title = ctk.CTkLabel(
            self.enrollment_display_container,
            text=f"{course_name} ({course_id}) - 选课管理",
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color=self.BUPT_BLUE
        )
        course_title.pack(pady=(0, 10), anchor="w")
        
        # 课程类型和容量信息
        info_frame = ctk.CTkFrame(self.enrollment_display_container, fg_color="#F0F8FF", corner_radius=8)
        info_frame.pack(fill="x", pady=(0, 15))
        
        info_text = f"课程类型: {course_type} | "
        info_text += f"容量: {course_info.get('current_students', 0)}/{course_info.get('max_students', 0)}"
        if is_elective:
            bidding_status = self.bidding_manager.get_course_bidding_status(offering_id)
            if bidding_status.get('exists'):
                info_text += f" | 待处理竞价: {bidding_status.get('pending_bids', 0)}"
        
        info_label = ctk.CTkLabel(
            info_frame,
            text=info_text,
            font=("Microsoft YaHei UI", 13),
            text_color="#333333"
        )
        info_label.pack(pady=8, padx=15, anchor="w")
        
        # 获取已选课学生
        enrolled_students = self.enrollment_manager.get_course_students(offering_id)
        
        # 创建选项卡（如果为选修课，显示两个选项卡：已选学生和积分竞价）
        if is_elective:
            # 创建选项卡框架
            tab_frame = ctk.CTkFrame(self.enrollment_display_container, fg_color="transparent")
            tab_frame.pack(fill="both", expand=True)
            
            # 选项卡按钮
            tab_button_frame = ctk.CTkFrame(tab_frame, fg_color="transparent")
            tab_button_frame.pack(fill="x", pady=(0, 10))
            
            self.enrollment_tab_var = ctk.StringVar(value="enrolled")
            
            enrolled_tab_btn = ctk.CTkButton(
                tab_button_frame,
                text="已选学生",
                width=150,
                height=35,
                font=("Microsoft YaHei UI", 13),
                fg_color=self.BUPT_BLUE if self.enrollment_tab_var.get() == "enrolled" else "#E0E0E0",
                text_color="white" if self.enrollment_tab_var.get() == "enrolled" else "gray",
                command=lambda: self.switch_enrollment_tab("enrolled", offering_id, course_info)
            )
            enrolled_tab_btn.pack(side="left", padx=(0, 5))
            
            bidding_tab_btn = ctk.CTkButton(
                tab_button_frame,
                text="积分竞价",
                width=150,
                height=35,
                font=("Microsoft YaHei UI", 13),
                fg_color=self.BUPT_BLUE if self.enrollment_tab_var.get() == "bidding" else "#E0E0E0",
                text_color="white" if self.enrollment_tab_var.get() == "bidding" else "gray",
                command=lambda: self.switch_enrollment_tab("bidding", offering_id, course_info)
            )
            bidding_tab_btn.pack(side="left")
            
            self.enrollment_tab_buttons = {
                "enrolled": enrolled_tab_btn,
                "bidding": bidding_tab_btn
            }
            
            # 内容区域
            self.enrollment_content_area = ctk.CTkFrame(tab_frame, fg_color="transparent")
            self.enrollment_content_area.pack(fill="both", expand=True)
            
            # 默认显示已选学生
            self.show_enrolled_students_table(offering_id, course_name, enrolled_students)
        else:
            # 必修课只显示已选学生
            self.show_enrolled_students_table(offering_id, course_name, enrolled_students)
    
    def refresh_enrollment_display(self):
        """刷新选课管理显示"""
        if hasattr(self, 'current_enrollment_offering_id') and hasattr(self, 'current_enrollment_course_info'):
            self.display_enrollment_info(self.current_enrollment_offering_id, self.current_enrollment_course_info)
        else:
            messagebox.showwarning("提示", "请先选择课程")
    
    def switch_enrollment_tab(self, tab_name, offering_id, course_info):
        """切换选课管理选项卡"""
        self.enrollment_tab_var.set(tab_name)
        
        # 更新按钮样式
        for name, btn in self.enrollment_tab_buttons.items():
            if name == tab_name:
                btn.configure(fg_color=self.BUPT_BLUE, text_color="white")
            else:
                btn.configure(fg_color="#E0E0E0", text_color="gray")
        
        # 清除内容区域
        for widget in self.enrollment_content_area.winfo_children():
            widget.destroy()
        
        # 显示对应内容
        if tab_name == "enrolled":
            enrolled_students = self.enrollment_manager.get_course_students(offering_id)
            self.show_enrolled_students_table(offering_id, course_info['course_name'], enrolled_students)
        elif tab_name == "bidding":
            self.show_bidding_ranking_table(offering_id, course_info)
    
    def show_enrolled_students_table(self, offering_id, course_name, enrolled_students):
        """显示已选学生表格"""
        # 保存当前信息供后续使用
        self.current_enrolled_offering_id = offering_id
        self.current_enrolled_course_name = course_name
        
        if not enrolled_students:
            no_students_label = ctk.CTkLabel(
                self.enrollment_content_area,
                text="该课程暂无学生选课",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_students_label.pack(pady=50)
            return
        
        # 操作按钮区域（放在表格上方）
        button_frame = ctk.CTkFrame(self.enrollment_content_area, fg_color="#FFEBEE", corner_radius=8)
        button_frame.pack(fill="x", pady=(0, 15), padx=0)
        
        button_inner = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_inner.pack(pady=12, padx=15)
        
        # 取消录取按钮
        cancel_btn = ctk.CTkButton(
            button_inner,
            text="❌ 取消录取选中学生",
            width=200,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color="#F44336",
            hover_color="#D32F2F",
            command=lambda: self.cancel_student_enrollment()
        )
        cancel_btn.pack(side="left", padx=(0, 15))
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            button_inner,
            text="🔄 刷新",
            width=120,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color="#666666",
            hover_color="#555555",
            command=lambda: self.refresh_enrollment_display()
        )
        refresh_btn.pack(side="left")
        
        # 提示信息
        hint_label = ctk.CTkLabel(
            button_inner,
            text="💡 提示：可按住Ctrl/Cmd键多选学生",
            font=("Microsoft YaHei UI", 12),
            text_color="#666666"
        )
        hint_label.pack(side="left", padx=(15, 0))
        
        # 创建表格框架
        table_frame = ctk.CTkFrame(self.enrollment_content_area)
        table_frame.pack(fill="both", expand=False, pady=(0, 10))
        
        # 配置表格样式
        style = ttk.Style()
        style.configure("Enrollment.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=40,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("Enrollment.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("Enrollment.Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        # 创建表格（支持多选）
        tree = ttk.Treeview(
            table_frame,
            columns=("student_id", "name", "major", "class", "enrollment_date", "status"),
            show="headings",
            height=15,
            style="Enrollment.Treeview",
            selectmode="extended"  # 支持多选
        )
        
        tree.heading("student_id", text="学号")
        tree.heading("name", text="姓名")
        tree.heading("major", text="专业")
        tree.heading("class", text="班级")
        tree.heading("enrollment_date", text="选课日期")
        tree.heading("status", text="状态")
        
        tree.column("student_id", width=120)
        tree.column("name", width=100)
        tree.column("major", width=150)
        tree.column("class", width=100)
        tree.column("enrollment_date", width=150)
        tree.column("status", width=80)
        
        for student in enrolled_students:
            status_text = {"enrolled": "已选", "completed": "已完成", "dropped": "已退课"}.get(
                student.get('status', 'enrolled'), "已选"
            )
            
            tree.insert("", "end", values=(
                student['student_id'],
                student['student_name'],
                student.get('major', '') or '',
                student.get('class_name', '') or '',
                student.get('enrollment_date', ''),
                status_text
            ))
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 保存tree引用
        self.current_enrolled_tree = tree
        
        # 统计信息
        count_label = ctk.CTkLabel(
            self.enrollment_content_area,
            text=f"共 {len(enrolled_students)} 名学生已选课",
            font=("Microsoft YaHei UI", 14, "bold"),
            text_color=self.BUPT_BLUE
        )
        count_label.pack(pady=10, anchor="w")
    
    def show_bidding_ranking_table(self, offering_id, course_info):
        """显示积分竞价排名表格"""
        # 获取竞价状态
        bidding_status = self.bidding_manager.get_course_bidding_status(offering_id)
        
        if not bidding_status.get('exists'):
            no_data_label = ctk.CTkLabel(
                self.enrollment_content_area,
                text="无法获取竞价信息",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_data_label.pack(pady=50)
            return
        
        # 获取竞价排名
        ranking = self.bidding_manager.get_bidding_ranking(offering_id)
        
        # 显示统计信息
        stats_frame = ctk.CTkFrame(self.enrollment_content_area, fg_color="#F0F8FF", corner_radius=8)
        stats_frame.pack(fill="x", pady=(0, 15))
        
        stats_text = f"待处理竞价: {bidding_status.get('pending_bids', 0)} | "
        stats_text += f"最高积分: {bidding_status.get('max_points', 0) or 0} | "
        stats_text += f"最低积分: {bidding_status.get('min_points', 0) or 0} | "
        avg_points = bidding_status.get('avg_points', 0) or 0
        stats_text += f"平均积分: {avg_points:.1f}"
        
        stats_label = ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=("Microsoft YaHei UI", 13, "bold"),
            text_color=self.BUPT_BLUE
        )
        stats_label.pack(pady=10, padx=15, anchor="w")
        
        if not ranking:
            no_bids_label = ctk.CTkLabel(
                self.enrollment_content_area,
                text="暂无积分竞价记录",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_bids_label.pack(pady=50)
            return
        
        # 先初始化tree变量供后续使用
        self.current_bidding_tree = None
        self.current_bidding_offering_id = offering_id
        self.current_bidding_course_info = course_info
        
        # 操作按钮区域（放在表格上方）
        button_frame = ctk.CTkFrame(self.enrollment_content_area, fg_color="#E8F5E9", corner_radius=8)
        button_frame.pack(fill="x", pady=(0, 15), padx=0)
        
        button_inner = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_inner.pack(pady=12, padx=15)
        
        # 自动处理竞价按钮（按排名自动录取）
        if bidding_status.get('pending_bids', 0) > 0:
            auto_process_btn = ctk.CTkButton(
                button_inner,
                text="🚀 自动处理竞价（按排名录取）",
                width=220,
                height=40,
                font=("Microsoft YaHei UI", 14, "bold"),
                fg_color="#4CAF50",
                hover_color="#45a049",
                command=lambda: self.process_bidding_auto(offering_id, course_info)
            )
            auto_process_btn.pack(side="left", padx=(0, 15))
        
        # 手动录取选中学生按钮（始终显示）
        manual_accept_btn = ctk.CTkButton(
            button_inner,
            text="✅ 录取选中学生",
            width=170,
            height=40,
            font=("Microsoft YaHei UI", 14, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            command=lambda: self.manual_accept_students()
        )
        manual_accept_btn.pack(side="left", padx=(0, 15))
        
        # 刷新按钮
        refresh_btn = ctk.CTkButton(
            button_inner,
            text="🔄 刷新",
            width=120,
            height=40,
            font=("Microsoft YaHei UI", 14),
            fg_color="#666666",
            hover_color="#555555",
            command=lambda: self.display_enrollment_info(offering_id, course_info)
        )
        refresh_btn.pack(side="left")
        
        # 创建表格框架（不使用expand=True，避免挤压按钮）
        table_frame = ctk.CTkFrame(self.enrollment_content_area)
        table_frame.pack(fill="both", expand=False, pady=(0, 10))
        
        # 配置表格样式
        style = ttk.Style()
        style.configure("BiddingRank.Treeview", 
                       font=("Microsoft YaHei UI", 13), 
                       rowheight=40,
                       background="white",
                       foreground="black",
                       fieldbackground="white")
        style.configure("BiddingRank.Treeview.Heading", 
                       font=("Microsoft YaHei UI", 14, "bold"),
                       background="#E8F4F8",
                       foreground=self.BUPT_BLUE,
                       relief="flat")
        style.map("BiddingRank.Treeview.Heading",
                 background=[("active", "#D0E8F0")])
        
        # 创建表格（支持多选）
        tree = ttk.Treeview(
            table_frame,
            columns=("rank", "student_id", "name", "points_bid", "bid_time"),
            show="headings",
            height=15,
            style="BiddingRank.Treeview",
            selectmode="extended"  # 支持多选
        )
        
        tree.heading("rank", text="排名")
        tree.heading("student_id", text="学号")
        tree.heading("name", text="姓名")
        tree.heading("points_bid", text="投入积分")
        tree.heading("bid_time", text="投入时间")
        
        tree.column("rank", width=60)
        tree.column("student_id", width=110)
        tree.column("name", width=100)
        tree.column("points_bid", width=90)
        tree.column("bid_time", width=150)
        
        # 标记前N名（N为课程容量）
        max_students = course_info.get('max_students', 0) or 0
        current_students = course_info.get('current_students', 0) or 0
        available_slots = max_students - current_students
        
        for bid in ranking:
            rank = bid.get('rank', 0)
            # 如果排名在可用名额内，使用特殊标记
            if rank <= available_slots:
                tag = "accepted"
            else:
                tag = "rejected"
            
            tree.insert("", "end", values=(
                rank,
                bid['student_id'],
                bid.get('student_name', ''),
                bid['points_bid'],
                bid.get('bid_time', '')
            ), tags=(tag,))
        
        # 配置标签颜色
        tree.tag_configure("accepted", background="#E8F5E9")  # 浅绿色
        tree.tag_configure("rejected", background="#FFF3E0")  # 浅橙色
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 保存tree引用
        self.current_bidding_tree = tree
        
        # 说明信息
        info_text = f"共 {len(ranking)} 名学生参与竞价 | "
        info_text += f"可用名额: {available_slots} | "
        info_text += "绿色标记表示在当前排名下可被录取 | "
        info_text += "可选中学生后点击'录取选中学生'，或点击'自动处理竞价'按排名自动录取"
        
        info_label = ctk.CTkLabel(
            self.enrollment_content_area,
            text=info_text,
            font=("Microsoft YaHei UI", 12),
            text_color="#666666"
        )
        info_label.pack(pady=10, anchor="w")
    
    def process_bidding_auto(self, offering_id, course_info):
        """自动处理竞价（按排名自动录取）"""
        course_name = course_info.get('course_name', '未知课程')
        
        # 确认对话框
        if not messagebox.askyesno(
            "确认处理",
            f"确定要自动处理【{course_name}】的竞价吗？\n"
            f"系统将按照积分排名自动录取前N名学生（N为可用名额）。",
            parent=self.root
        ):
            return
        
        try:
            # 调用竞价管理器处理竞价结果
            success, message = self.bidding_manager.process_bidding_results(offering_id)
            
            if success:
                Logger.info(f"教师自动处理竞价成功: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
                messagebox.showinfo("成功", message, parent=self.root)
                # 刷新显示 - 重新从数据库获取最新的课程信息
                updated_course_info = self.course_manager.get_offering_by_id(offering_id)
                if updated_course_info:
                    self.display_enrollment_info(offering_id, updated_course_info)
                else:
                    self.display_enrollment_info(offering_id, course_info)
            else:
                Logger.warning(f"教师自动处理竞价失败: {self.user.name} ({self.user.id}) - {message}")
                messagebox.showerror("失败", message, parent=self.root)
        except Exception as e:
            Logger.error(f"自动处理竞价异常: {e}", exc_info=True)
            messagebox.showerror("错误", f"处理失败：{str(e)}", parent=self.root)
    
    def manual_accept_students(self):
        """手动录取选中的学生"""
        # 使用保存的tree和课程信息
        if not hasattr(self, 'current_bidding_tree') or not self.current_bidding_tree:
            messagebox.showerror("错误", "无法获取竞价表格信息", parent=self.root)
            return
        
        tree = self.current_bidding_tree
        offering_id = self.current_bidding_offering_id
        course_info = self.current_bidding_course_info
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要录取的学生", parent=self.root)
            return
        
        course_name = course_info.get('course_name', '未知课程')
        selected_count = len(selection)
        
        # 获取选中学生的信息
        selected_students = []
        for item_id in selection:
            item = tree.item(item_id)
            values = item['values']
            if len(values) >= 2:
                student_id = values[1]  # 学号在第二列
                student_name = values[2] if len(values) > 2 else ''  # 姓名在第三列
                points_bid = values[3] if len(values) > 3 else 0  # 投入积分
                selected_students.append({
                    'student_id': student_id,
                    'student_name': student_name,
                    'points_bid': points_bid
                })
        
        # 确认对话框
        students_list = "\n".join([f"  - {s['student_name']} ({s['student_id']}) - 投入积分: {s['points_bid']}" 
                                   for s in selected_students[:5]])
        if len(selected_students) > 5:
            students_list += f"\n  ... 还有 {len(selected_students) - 5} 名学生"
        
        if not messagebox.askyesno(
            "确认录取",
            f"确定要录取以下 {selected_count} 名学生吗？\n\n{students_list}\n\n"
            f"录取后将从学生账户扣除相应积分。",
            parent=self.root
        ):
            return
        
        # 检查课程容量
        max_students = course_info.get('max_students', 0) or 0
        current_students = course_info.get('current_students', 0) or 0
        available_slots = max_students - current_students
        
        if selected_count > available_slots:
            messagebox.showerror(
                "错误",
                f"可用名额不足！\n当前可用名额: {available_slots}\n选中学生数: {selected_count}",
                parent=self.root
            )
            return
        
        # 逐个录取学生
        success_count = 0
        failed_students = []
        
        for student_info in selected_students:
            student_id = student_info['student_id']
            points = student_info['points_bid']
            
            try:
                # 1. 获取竞价记录ID
                bid_info = self.bidding_manager.get_bid_info(student_id, offering_id)
                if not bid_info or bid_info.get('status') != 'pending':
                    failed_students.append(f"{student_info['student_name']} ({student_id}): 竞价记录不存在或已处理")
                    continue

                bidding_id = bid_info['bidding_id']
                
                # 1.5 检查是否已选过该课程
                existing_check = self.enrollment_manager._get_enrollment(student_id, offering_id)
                if existing_check and existing_check['status'] == 'enrolled':
                    failed_students.append(f"{student_info['student_name']} ({student_id}): 已选过该课程")
                    continue
                
                # 1.6 检查是否选了同一门课程的其他班级
                offering = self.course_manager.get_offering_by_id(offering_id)
                if offering:
                    same_course = self.enrollment_manager._check_same_course_enrolled(
                        student_id, offering['course_id']
                    )
                    if same_course:
                        failed_students.append(f"{student_info['student_name']} ({student_id}): 已选择了该课程的其他班级")
                        continue

                # 2. 更新竞价状态为accepted
                self.db.update_data(
                    'course_biddings',
                    {
                        'status': 'accepted',
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    {'bidding_id': bidding_id}
                )
                
                # 3. 扣除积分
                success, msg = self.points_manager.deduct_points(
                    student_id,
                    points,
                    f"选修课录取扣除（课程: {course_name}, 开课ID: {offering_id}）"
                )
                
                if not success:
                    # 如果扣除积分失败，回滚竞价状态
                    self.db.update_data(
                        'course_biddings',
                        {
                            'status': 'pending',
                            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        {'bidding_id': bidding_id}
                    )
                    failed_students.append(f"{student_info['student_name']} ({student_id}): {msg}")
                    continue
                
                # 4. 创建或更新选课记录
                try:
                    # 先检查是否已存在该学生的enrollment记录（可能是dropped状态）
                    existing_enrollment = self.db.execute_query("""
                        SELECT enrollment_id, status 
                        FROM enrollments 
                        WHERE student_id = ? AND offering_id = ?
                        LIMIT 1
                    """, (student_id, offering_id))
                    
                    result_success = False
                    
                    if existing_enrollment and existing_enrollment[0]['status'] == 'dropped':
                        # 如果存在dropped状态的记录，更新为enrolled
                        enrollment_id = existing_enrollment[0]['enrollment_id']
                        update_count = self.db.update_data(
                            'enrollments',
                            {
                                'status': 'enrolled',
                                'enrollment_date': datetime.now().strftime('%Y-%m-%d')
                            },
                            {'enrollment_id': enrollment_id}
                        )
                        result_success = update_count > 0
                    else:
                        # 如果不存在，插入新记录
                        enrollment_data = {
                            'student_id': student_id,
                            'offering_id': offering_id,
                            'enrollment_date': datetime.now().strftime('%Y-%m-%d'),
                            'status': 'enrolled'
                        }
                        result_id = self.db.insert_data('enrollments', enrollment_data)
                        result_success = result_id is not None
                    
                    if result_success:
                        success_count += 1
                        Logger.info(f"教师手动录取学生: {self.user.name} ({self.user.id}) - 学生: {student_id}, 课程: {course_name}")
                    else:
                        # 操作失败，回滚积分和竞价状态
                        self.points_manager.refund_points(
                            student_id,
                            points,
                            f"录取失败退还积分（课程: {course_name}）"
                        )
                        self.db.update_data(
                            'course_biddings',
                            {
                                'status': 'pending',
                                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            },
                            {'bidding_id': bidding_id}
                        )
                        failed_students.append(f"{student_info['student_name']} ({student_id}): 选课记录创建失败")
                        
                except Exception as insert_error:
                    # 插入失败，回滚积分和竞价状态
                    Logger.error(f"插入enrollment记录失败: {insert_error}", exc_info=True)
                    self.points_manager.refund_points(
                        student_id,
                        points,
                        f"录取失败退还积分（课程: {course_name}）"
                    )
                    self.db.update_data(
                        'course_biddings',
                        {
                            'status': 'pending',
                            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        {'bidding_id': bidding_id}
                    )
                    failed_students.append(f"{student_info['student_name']} ({student_id}): {str(insert_error)}")
                    
            except Exception as e:
                Logger.error(f"录取学生失败: {student_id}, {e}", exc_info=True)
                failed_students.append(f"{student_info['student_name']} ({student_id}): {str(e)}")
        
        # 更新课程的current_students
        if success_count > 0:
            new_current = current_students + success_count
            self.db.update_data(
                'course_offerings',
                {'current_students': new_current},
                {'offering_id': offering_id}
            )
        
        # 显示结果
        result_message = f"处理完成！\n成功录取: {success_count} 名学生"
        if failed_students:
            result_message += f"\n失败: {len(failed_students)} 名学生\n\n失败详情:\n"
            result_message += "\n".join(failed_students[:5])
            if len(failed_students) > 5:
                result_message += f"\n... 还有 {len(failed_students) - 5} 个失败记录"
        
        if success_count > 0:
            messagebox.showinfo("处理完成", result_message, parent=self.root)
            # 刷新显示 - 重新从数据库获取最新的课程信息
            updated_course_info = self.course_manager.get_offering_by_id(offering_id)
            if updated_course_info:
                self.display_enrollment_info(offering_id, updated_course_info)
            else:
                # 如果获取失败，使用旧的course_info但更新人数
                course_info['current_students'] = new_current
                self.display_enrollment_info(offering_id, course_info)
        else:
            messagebox.showerror("处理失败", result_message, parent=self.root)
    
    def cancel_student_enrollment(self):
        """取消录取选中的学生（支持批量） - 学生回到竞价队列"""
        # 使用保存的tree和课程信息
        if not hasattr(self, 'current_enrolled_tree') or not self.current_enrolled_tree:
            messagebox.showerror("错误", "无法获取学生表格信息", parent=self.root)
            return
        
        tree = self.current_enrolled_tree
        offering_id = self.current_enrolled_offering_id
        course_name = self.current_enrolled_course_name
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要取消录取的学生", parent=self.root)
            return
        
        selected_count = len(selection)
        
        # 获取选中学生的信息
        selected_students = []
        for item_id in selection:
            item = tree.item(item_id)
            values = item['values']
            if len(values) >= 2:
                student_id = values[0]  # 学号在第一列
                student_name = values[1] if len(values) > 1 else ''  # 姓名在第二列
                selected_students.append({
                    'student_id': student_id,
                    'student_name': student_name
                })
        
        # 确认对话框
        students_list = "\n".join([f"  - {s['student_name']} ({s['student_id']})" 
                                   for s in selected_students[:5]])
        if len(selected_students) > 5:
            students_list += f"\n  ... 还有 {len(selected_students) - 5} 名学生"
        
        if not messagebox.askyesno(
            "确认取消录取",
            f"确定要取消录取以下 {selected_count} 名学生吗？\n\n{students_list}\n\n"
            f"取消录取后，学生将回到竞价队列，可以继续参与竞价。",
            parent=self.root
        ):
            return
        
        # 执行取消录取
        success_count = 0
        failed_students = []
        refunded_students = []  # 记录返还积分并回到竞价队列的学生
        
        for student_info in selected_students:
            student_id = student_info['student_id']
            
            try:
                # 1. 检查选课记录
                enrollment = self.db.execute_query("""
                    SELECT enrollment_id 
                    FROM enrollments 
                    WHERE student_id = ? AND offering_id = ? AND status = 'enrolled'
                """, (student_id, offering_id))
                
                if not enrollment:
                    failed_students.append(f"{student_info['student_name']} ({student_id}): 未找到选课记录")
                    continue
                
                enrollment_id = enrollment[0]['enrollment_id']
                
                # 2. 获取竞价信息
                bid_info = self.bidding_manager.get_bid_info(student_id, offering_id)
                
                if bid_info and bid_info.get('status') == 'accepted':
                    points_bid = bid_info.get('points_bid', 0)
                    
                    # 3. 返还积分（先返还，失败则不继续）
                    success, msg = self.points_manager.refund_points(
                        student_id,
                        points_bid,
                        f"取消录取退还积分（课程: {course_name}, 开课ID: {offering_id}）"
                    )
                    
                    if not success:
                        failed_students.append(f"{student_info['student_name']} ({student_id}): 返还积分失败 - {msg}")
                        continue
                    
                    # 4. 删除选课记录（标记为dropped）
                    update_count = self.db.update_data(
                        'enrollments',
                        {'status': 'dropped'},
                        {'enrollment_id': enrollment_id}
                    )
                    
                    if update_count == 0:
                        # 回滚积分
                        self.points_manager.deduct_points(
                            student_id,
                            points_bid,
                            f"回滚：取消录取失败（课程: {course_name}, 开课ID: {offering_id}）"
                        )
                        failed_students.append(f"{student_info['student_name']} ({student_id}): 更新选课记录失败")
                        continue
                    
                    # 5. 将竞价状态改回pending（而不是cancelled）
                    bidding_update_count = self.db.update_data(
                        'course_biddings',
                        {
                            'status': 'pending',
                            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        {'student_id': student_id, 'offering_id': offering_id}
                    )
                    
                    if bidding_update_count == 0:
                        Logger.warning(f"更新竞价状态失败: student_id={student_id}, offering_id={offering_id}")
                    
                    # 6. 更新课程选课人数
                    self.db.execute_update(
                        "UPDATE course_offerings SET current_students = current_students - 1 WHERE offering_id = ?",
                        (offering_id,)
                    )
                    self.db.conn.commit()  # 确保提交
                    
                    # 7. 检查取消录取后的人数，如果不满就重新开放选课和竞价
                    offering_info = self.db.execute_query("""
                        SELECT co.current_students, co.max_students, co.bidding_status, c.course_type, co.status
                        FROM course_offerings co
                        JOIN courses c ON co.course_id = c.course_id
                        WHERE co.offering_id = ?
                    """, (offering_id,))
                    
                    if offering_info:
                        current = offering_info[0]['current_students']
                        max_students = offering_info[0]['max_students']
                        course_type = offering_info[0].get('course_type', '')
                        current_status = offering_info[0].get('status', '')
                        
                        update_data = {}
                        
                        # 如果原来是满的，改为open以允许其他学生选课
                        if current < max_students and current_status == 'full':
                            update_data['status'] = 'open'
                            Logger.info(f"  取消录取后人数不满 ({current}/{max_students})，已重新开放选课")
                            
                            # 如果是选修课且人数不满，重新开放竞价
                            if '选修' in course_type:
                                update_data['bidding_status'] = 'open'
                                Logger.info(f"  选修课已重新开放竞价")
                        
                        if update_data:
                            self.db.update_data('course_offerings', update_data, {'offering_id': offering_id})
                    
                    success_count += 1
                    refunded_students.append({
                        'name': student_info['student_name'],
                        'id': student_id,
                        'points': points_bid
                    })
                    
                    Logger.info(f"教师取消录取学生: {self.user.name} ({self.user.id}) - 学生: {student_id}, 课程: {course_name}, 返还积分: {points_bid}")
                else:
                    # 非竞价课程或状态异常
                    failed_students.append(f"{student_info['student_name']} ({student_id}): 该学生不是通过竞价录取的")
                    
            except Exception as e:
                Logger.error(f"取消录取学生失败: {student_id}, {e}", exc_info=True)
                failed_students.append(f"{student_info['student_name']} ({student_id}): {str(e)}")
        
        # 显示结果
        result_message = f"处理完成！\n成功取消录取: {success_count} 名学生"
        
        if refunded_students:
            result_message += f"\n\n学生已回到竞价队列 ({len(refunded_students)} 名):"
            for item in refunded_students[:5]:
                result_message += f"\n  - {item['name']} ({item['id']}) - 返还积分: {item['points']}分"
            if len(refunded_students) > 5:
                result_message += f"\n  ... 还有 {len(refunded_students) - 5} 名学生"
            result_message += "\n\n这些学生可以继续参与竞价或修改投入积分。"
        
        if failed_students:
            result_message += f"\n\n失败: {len(failed_students)} 名学生"
            result_message += "\n失败详情:\n"
            result_message += "\n".join(failed_students[:5])
            if len(failed_students) > 5:
                result_message += f"\n... 还有 {len(failed_students) - 5} 个失败记录"
        
        if success_count > 0:
            messagebox.showinfo("处理完成", result_message, parent=self.root)
            # 刷新显示
            self.refresh_enrollment_display()
        else:
            messagebox.showerror("处理失败", result_message, parent=self.root)
    
    def show_data_analysis(self):
        """显示数据分析"""
        self.set_active_menu(4)
        self.clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="数据分析",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 获取授课课程
        courses = self.course_manager.get_teacher_courses(self.user.id)
        
        if not courses:
            no_data_label = ctk.CTkLabel(
                self.content_frame,
                text="暂无授课课程",
                font=("Microsoft YaHei UI", 14),
                text_color="gray"
            )
            no_data_label.pack(pady=50)
            return
        
        # 保存课程列表
        self.analysis_courses_list = courses
        
        # 课程选择
        course_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0F8FF", corner_radius=10)
        course_frame.pack(fill="x", padx=20, pady=15)
        
        course_inner_frame = ctk.CTkFrame(course_frame, fg_color="transparent")
        course_inner_frame.pack(pady=15, padx=20)
        
        label = ctk.CTkLabel(
            course_inner_frame,
            text="选择课程：",
            font=("Microsoft YaHei UI", 16, "bold"),
            text_color=self.BUPT_BLUE
        )
        label.pack(side="left", padx=(0, 15))
        
        # 改进课程名称显示：包含课程代码、时间和教室以便区分
        course_names = []
        for c in courses:
            course_name = f"{c['course_name']} ({c['course_id']})"
            if c.get('class_time') or c.get('classroom'):
                details = []
                if c.get('class_time'):
                    details.append(c['class_time'])
                if c.get('classroom'):
                    details.append(c['classroom'])
                if details:
                    course_name += f" - {' | '.join(details)}"
            course_names.append(course_name)
        
        self.analysis_course_combo = ctk.CTkComboBox(
            course_inner_frame,
            values=course_names,
            width=600,
            height=40,
            font=("Microsoft YaHei UI", 13),
            command=self.on_analysis_course_changed
        )
        self.analysis_course_combo.pack(side="left")
        if course_names:
            self.analysis_course_combo.set(course_names[0])
        
        # 创建图表显示容器
        self.analysis_chart_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.analysis_chart_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # 默认显示第一门课程的统计
        if courses:
            self.show_course_statistics(
                courses[0]['offering_id'], 
                courses[0].get('course_name', ''),
                courses[0].get('class_time'),
                courses[0].get('classroom')
            )
    
    def on_analysis_course_changed(self, selected_course_name):
        """课程选择变化时的回调"""
        if not hasattr(self, 'analysis_courses_list') or not selected_course_name:
            return
        
        # 找到选中的课程（通过下拉框的值匹配）
        # 构建完整的课程名称列表（与下拉框中的格式一致）
        course_names = []
        for c in self.analysis_courses_list:
            course_name = f"{c['course_name']} ({c['course_id']})"
            if c.get('class_time') or c.get('classroom'):
                details = []
                if c.get('class_time'):
                    details.append(c['class_time'])
                if c.get('classroom'):
                    details.append(c['classroom'])
                if details:
                    course_name += f" - {' | '.join(details)}"
            course_names.append(course_name)
        
        try:
            index = course_names.index(selected_course_name)
            selected_course = self.analysis_courses_list[index]
            self.show_course_statistics(
                selected_course['offering_id'],
                selected_course.get('course_name', ''),
                selected_course.get('class_time'),
                selected_course.get('classroom')
            )
        except (ValueError, IndexError):
            pass
    
    def show_course_statistics(self, offering_id, course_name="", class_time=None, classroom=None):
        """显示课程统计信息"""
        # 清除之前的图表容器内容
        if hasattr(self, 'analysis_chart_container'):
            for widget in self.analysis_chart_container.winfo_children():
                widget.destroy()
        else:
            # 如果容器不存在，创建一个
            self.analysis_chart_container = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            self.analysis_chart_container.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # 获取统计数据
        stats = self.grade_manager.get_grade_statistics(offering_id)
        
        # 课程名称标签
        if course_name:
            course_label_frame = ctk.CTkFrame(self.analysis_chart_container, fg_color="transparent")
            course_label_frame.pack(fill="x", pady=(0, 15))
            
            # 课程名称
            course_title = ctk.CTkLabel(
                course_label_frame,
                text=f"课程：{course_name}",
                font=("Microsoft YaHei UI", 18, "bold"),
                text_color=self.BUPT_BLUE
            )
            course_title.pack(anchor="w")
            
            # 显示上课时间和教室
            if class_time or classroom:
                time_classroom_text = ""
                if class_time:
                    time_classroom_text = f"上课时间：{class_time}"
                if classroom:
                    if time_classroom_text:
                        time_classroom_text += f"  |  教室：{classroom}"
                    else:
                        time_classroom_text = f"教室：{classroom}"
                
                if time_classroom_text:
                    time_label = ctk.CTkLabel(
                        course_label_frame,
                        text=time_classroom_text,
                        font=("Microsoft YaHei UI", 13),
                        text_color="#666666"
                    )
                    time_label.pack(anchor="w", pady=(5, 0))
        
        if stats['total_count'] == 0:
            no_data = ctk.CTkLabel(
                self.analysis_chart_container,
                text="该课程暂无成绩数据",
                font=("Microsoft YaHei UI", 16),
                text_color="gray"
            )
            no_data.pack(pady=50)
            return
        
        # 统计卡片
        stats_frame = ctk.CTkFrame(self.analysis_chart_container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 20))
        
        stat_items = [
            ("总人数", stats['total_count'], "#007bff"),
            ("平均分", f"{stats['avg_score']:.1f}", "#28a745"),
            ("最高分", stats['max_score'], "#ffc107"),
            ("最低分", stats['min_score'], "#dc3545"),
            ("及格率", f"{stats['pass_rate']:.1f}%", "#17a2b8")
        ]
        
        for i, (label, value, color) in enumerate(stat_items):
            card = ctk.CTkFrame(stats_frame, fg_color=color, corner_radius=10)
            card.pack(side="left", fill="both", expand=True, padx=5)
            
            value_label = ctk.CTkLabel(
                card,
                text=str(value),
                font=("Microsoft YaHei UI", 24, "bold"),
                text_color="white"
            )
            value_label.pack(pady=(10, 0))
            
            label_label = ctk.CTkLabel(
                card,
                text=label,
                font=("Microsoft YaHei UI", 12),
                text_color="white"
            )
            label_label.pack(pady=(0, 10))
        
        # 图表区域
        chart_frame = tk.Frame(self.analysis_chart_container, bg="white")
        chart_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        # 创建图表
        fig = Figure(figsize=(10, 4), dpi=100)
        
        # 成绩分布柱状图
        ax1 = fig.add_subplot(121)
        categories = ['优秀\n(≥90)', '良好\n(80-89)', '中等\n(70-79)', '及格\n(60-69)', '不及格\n(<60)']
        counts = [
            stats['excellent_count'],
            stats['good_count'],
            stats['medium_count'],
            stats['pass_count'],
            stats['fail_count']
        ]
        colors = ['#28a745', '#17a2b8', '#ffc107', '#fd7e14', '#dc3545']
        
        bars = ax1.bar(categories, counts, color=colors, alpha=0.8)
        ax1.set_ylabel('人数', fontsize=12)
        ax1.set_title('成绩分布', fontsize=14, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        # 在柱状图上显示数值
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}',
                        ha='center', va='bottom', fontsize=10)
        
        # 成绩分布饼图
        ax2 = fig.add_subplot(122)
        if sum(counts) > 0:
            # 只显示有数据的部分
            valid_data = [(cat, count, col) for cat, count, col in zip(categories, counts, colors) if count > 0]
            if valid_data:
                labels, sizes, colors_pie = zip(*valid_data)
                ax2.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                ax2.set_title('成绩比例', fontsize=14, fontweight='bold')
        
        fig.tight_layout()
        
        # 嵌入图表
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def show_personal_info(self):
        """显示个人信息"""
        self.set_active_menu(5)
        self.clear_content()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="个人信息",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(pady=20, anchor="w", padx=20)
        
        # 信息卡片
        info_frame = ctk.CTkFrame(self.content_frame, fg_color="#F8F9FA")
        info_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        infos = [
            ("工号", self.user.id),
            ("姓名", self.user.name),
            ("职称", self.user.extra_info.get('title', '')),
            ("院系", self.user.extra_info.get('department', '')),
            ("邮箱", self.user.email or '')
        ]
        
        for label_text, value in infos:
            row_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=30, pady=15)
            
            label = ctk.CTkLabel(
                row_frame,
                text=f"{label_text}：",
                font=("Microsoft YaHei UI", 14, "bold"),
                text_color=self.BUPT_BLUE,
                width=100,
                anchor="e"
            )
            label.pack(side="left")
            
            value_label = ctk.CTkLabel(
                row_frame,
                text=str(value),
                font=("Microsoft YaHei UI", 14),
                text_color="black"
            )
            value_label.pack(side="left", padx=20)
    
    def do_logout(self):
        """注销登录"""
        if messagebox.askyesno("确认", "确定要退出登录吗？"):
            self.root.destroy()
            self.logout_callback()
    
    def on_close(self):
        """关闭窗口"""
        self.do_logout()

