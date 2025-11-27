"""
教师端主窗口 - 北京邮电大学教学管理系统
提供成绩录入、查看授课班级、数据分析等功能
"""

import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog
import tkinter as tk
from pathlib import Path
from PIL import Image
from utils.logger import Logger
from core.course_manager import CourseManager
from core.enrollment_manager import EnrollmentManager
from core.grade_manager import GradeManager
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
        
        # 设置窗口
        self.root.title(f"北京邮电大学教学管理系统 - 教师端 - {user.name}")
        
        window_width = 1300
        window_height = 750
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 配置matplotlib中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建界面
        self.create_widgets()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        Logger.info(f"教师端窗口打开: {user.name}")
    
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
            text_color=self.BUPT_BLUE
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
    
    def show_data_analysis(self):
        """显示数据分析"""
        self.set_active_menu(3)
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
        self.set_active_menu(4)
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

