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
from utils.qwen_client import QwenAdvisor
import threading


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
        
        # 设置窗口
        self.root.title(f"北京邮电大学教学管理系统 - 学生端 - {user.name}")
        
        window_width = 1200
        window_height = 800  # 增加窗口高度，为建议显示区域提供更多空间
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
            ("🤖 学习建议", self.show_ai_advice),
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
        
        # 获取选课记录 - 只显示当前学期的已选课程（包括必修课程）
        import os
        from utils.logger import Logger
        current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
        
        enrollments = self.enrollment_manager.get_student_enrollments(
            self.user.id, status='enrolled'
        )
        
        # 调试信息：记录查询到的所有选课记录
        Logger.debug(f"学生 {self.user.id} 查询到 {len(enrollments)} 条选课记录")
        
        # 如果查询结果为0，检查数据库中是否有该学生的任何记录
        if len(enrollments) == 0:
            try:
                # 检查是否有任何状态的选课记录（直接查询数据库）
                all_status_enrollments = self.db.execute_query(
                    """
                    SELECT e.enrollment_id, e.status, e.semester, co.course_id
                    FROM enrollments e
                    LEFT JOIN course_offerings co ON e.offering_id = co.offering_id
                    WHERE e.student_id = ?
                    LIMIT 10
                    """,
                    (self.user.id,)
                )
                Logger.debug(f"学生 {self.user.id} 所有状态的选课记录数: {len(all_status_enrollments)}")
                
                # 检查数据库中是否有该学生的记录
                student_check = self.db.execute_query(
                    "SELECT student_id, grade, major FROM students WHERE student_id=? LIMIT 1",
                    (self.user.id,)
                )
                if student_check:
                    Logger.debug(f"学生 {self.user.id} 存在于数据库中: {student_check[0]}")
                else:
                    Logger.warning(f"学生 {self.user.id} 不存在于数据库中！")
                
                # 检查是否有该学期的开课记录
                offering_check = self.db.execute_query(
                    "SELECT COUNT(*) as cnt FROM course_offerings WHERE semester=?",
                    (current_semester,)
                )
                if offering_check:
                    Logger.debug(f"学期 {current_semester} 的开课记录数: {offering_check[0].get('cnt', 0)}")
            except Exception as e:
                Logger.warning(f"诊断查询时出错: {e}")
        
        if enrollments:
            semesters_found = set()
            for e in enrollments:
                sem = e.get('semester', '') or ''
                if sem:
                    semesters_found.add(sem)
            Logger.debug(f"找到的学期: {semesters_found}, 当前查询学期: {current_semester}")
        
        # 过滤：只显示当前学期的所有课程
        # 注意：包括所有已选课程，包括默认必修课程
        # 使用字符串比较确保学期匹配（处理可能的格式差异）
        # 如果enrollments中的semester为空，尝试从course_offerings获取
        filtered_enrollments = []
        for e in enrollments:
            semester = e.get('semester', '').strip() if e.get('semester') else ''
            # 如果semester为空，尝试从course_offerings获取（通过offering_id）
            if not semester:
                offering_id = e.get('offering_id')
                if offering_id:
                    offering_info = self.course_manager.get_offering_by_id(offering_id)
                    if offering_info and offering_info.get('semester'):
                        semester = offering_info['semester'].strip()
                        # 更新enrollments记录中的semester字段
                        e['semester'] = semester
            
            # 匹配当前学期
            if semester and semester.strip() == current_semester.strip():
                # 确保semester字段被设置（用于显示）
                e['semester'] = semester
                filtered_enrollments.append(e)
        
        enrollments = filtered_enrollments
        
        # 调试信息：记录过滤后的结果
        Logger.debug(f"过滤后，当前学期 {current_semester} 的选课记录数: {len(enrollments)}")
        
        if not enrollments:
            # 检查是否有其他学期的选课记录
            all_enrollments = self.enrollment_manager.get_student_enrollments(
                self.user.id, status='enrolled'
            )
            
            # 收集所有学期信息
            all_semesters = set()
            for e in all_enrollments:
                sem = e.get('semester', '').strip() if e.get('semester') else ''
                if not sem:
                    # 尝试从course_offerings获取
                    offering_id = e.get('offering_id')
                    if offering_id:
                        offering_info = self.course_manager.get_offering_by_id(offering_id)
                        if offering_info and offering_info.get('semester'):
                            sem = offering_info['semester'].strip()
                if sem:
                    all_semesters.add(sem)
            
            # 显示提示信息
            info_frame = ctk.CTkFrame(self.content_frame, fg_color="#F0F8FF", corner_radius=10)
            info_frame.pack(fill="x", padx=20, pady=20)
            
            if not all_enrollments:
                # 完全没有选课记录
                no_data_label = ctk.CTkLabel(
                    info_frame,
                    text="暂无选课记录\n\n提示：如果这是首次使用，请先运行数据生成脚本生成选课数据\n\n"
                         f"当前学期：{current_semester}",
                    font=("Microsoft YaHei UI", 16),
                    text_color="#666666",
                    justify="center"
                )
                no_data_label.pack(pady=30, padx=20)
            else:
                # 有其他学期的选课记录
                sem_list = sorted(list(all_semesters)) if all_semesters else ["未知"]
                
                # 解析学生年级信息，提供更准确的提示
                student_grade = None
                try:
                    student_info = self.db.execute_query(
                        "SELECT grade FROM students WHERE student_id=? LIMIT 1",
                        (self.user.id,)
                    )
                    if student_info:
                        student_grade = student_info[0].get('grade')
                except:
                    pass
                
                # 计算学生在当前学期应该是大几
                if student_grade:
                    try:
                        current_year = int(current_semester.split("-")[0])
                        academic_year = current_year - int(student_grade) + 1
                        if academic_year < 1:
                            academic_year = 1
                        elif academic_year > 4:
                            academic_year = 4
                        grade_text = f"大{['一', '二', '三', '四'][academic_year-1]}"
                    except:
                        grade_text = ""
                else:
                    grade_text = ""
                
                hint_text = f"当前学期（{current_semester}）暂无选课记录"
                if grade_text:
                    hint_text += f"\n\n您当前应该是{grade_text}学生，应该有对应的必修课程"
                hint_text += f"\n\n您在其他学期有 {len(all_enrollments)} 条选课记录\n"
                hint_text += f"学期：{', '.join(sem_list)}\n\n"
                hint_text += f"⚠️ 重要提示：\n"
                hint_text += f"1. 数据生成会为所有8个学期生成数据（从2022-2023-1到2025-2026-2）\n"
                hint_text += f"2. base_semester参数仅用于确定起始年份，查询时可以使用任意学期\n"
                hint_text += f"3. 生成数据命令示例：python -m utils.data_simulator all 300 50 bupt_teaching.db 2025-2026-2\n"
                hint_text += f"4. 运行程序命令：python main.py {current_semester}\n"
                hint_text += f"5. 如果数据已生成但查询不到，可能是该学期的选课数据生成失败，请检查日志"
                
                no_data_label = ctk.CTkLabel(
                    info_frame,
                    text=hint_text,
                    font=("Microsoft YaHei UI", 14),
                    text_color="#666666",
                    justify="center"
                )
                no_data_label.pack(pady=30, padx=20)
            
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
            columns=("course_id", "course_name", "credits", "semester", "teacher", "time", "classroom", "action"),
            show="headings",
            height=15
        )
        
        # 列标题
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("semester", text="学期")
        tree.heading("teacher", text="授课教师")
        tree.heading("time", text="上课时间")
        tree.heading("classroom", text="教室")
        tree.heading("action", text="操作")
        
        # 列宽
        tree.column("course_id", width=100)
        tree.column("course_name", width=200)
        tree.column("credits", width=80)
        tree.column("semester", width=120)
        tree.column("teacher", width=100)
        tree.column("time", width=180)
        tree.column("classroom", width=120)
        tree.column("action", width=100)
        
        # 插入数据
        for enrollment in enrollments:
            tree.insert("", "end", values=(
                enrollment['course_id'],
                enrollment['course_name'],
                f"{enrollment['credits']}学分",
                enrollment.get('semester', ''),
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
        
        # 获取可选课程 - 从环境变量或配置中读取当前学期
        # 如果生成数据时指定了学期（如 2024-2025-2），GUI应该只显示该学期的课程
        import os
        current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
        
        # 传入学期和当前用户的ID
        courses = self.course_manager.get_available_courses(
            current_semester, 
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
        
        # --- 修复核心逻辑：双重循环遍历 offerings，并去除重复课程 ---
        # 使用集合记录已显示的课程（课程名称、老师、上课时间）
        seen_courses = set()
        
        for course in courses:
            # 遍历该课程下的所有开课班级
            for offering in course.get('offerings', []):
                # 构建唯一标识：课程名称 + 老师 + 上课时间
                course_name = course.get('course_name', '')
                teacher_name = offering.get('teacher_name', '未知')
                class_time = offering.get('class_time', '')
                unique_key = (course_name, teacher_name, class_time)
                
                # 如果已经显示过相同的课程（相同名称、老师、时间），跳过
                if unique_key in seen_courses:
                    continue
                
                seen_courses.add(unique_key)
                tree.insert("", "end", values=(
                    course.get('course_id', ''),
                    course.get('course_name', ''),
                    course.get('course_type', ''),
                    f"{course.get('credits', 0)}",
                    offering.get('teacher_name', '未知'),
                    offering.get('class_time', ''),
                    f"{offering.get('current_students', 0)}/{offering.get('max_students', 0)}",
                    "选课"
                ), tags=(offering['offering_id'],))
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
        """选课对话框"""
        selection = tree.selection()
        if not selection:
            return
        
        item = tree.item(selection[0])
        values = item['values']
        offering_id = int(item['tags'][0])
        
        if messagebox.askyesno("确认选课", f"确定要选择【{values[1]}】吗？"):
            success, message = self.enrollment_manager.enroll_course(
                self.user.id, offering_id
            )
            if success:
                # 获取课程信息用于日志
                offering_info = self.course_manager.get_offering_by_id(offering_id)
                course_name = offering_info['course_name'] if offering_info else values[1]
                Logger.info(f"学生选课: {self.user.name} ({self.user.id}) - 课程: {course_name} (开课ID: {offering_id})")
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
        
        # 获取所有可选课程 (修复：补全参数)
        import os
        current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
        all_courses = self.course_manager.get_available_courses(current_semester, self.user.id)
        
        keyword_lower = keyword.strip().lower() if keyword else ""
        found_any = False
        # 使用集合记录已显示的课程（课程名称、老师、上课时间），避免重复
        seen_courses = set()

        # 遍历课程
        for course in all_courses:
            # 遍历该课程下的所有开课班级（offering）
            for offering in course.get('offerings', []):
                # 构建唯一标识：课程名称 + 老师 + 上课时间
                course_name = course.get('course_name', '')
                teacher_name = offering.get('teacher_name', '未知')
                class_time = offering.get('class_time', '')
                unique_key = (course_name, teacher_name, class_time)
                
                # 如果已经显示过相同的课程（相同名称、老师、时间），跳过
                if unique_key in seen_courses:
                    continue
                
                # 获取匹配所需的字段
                c_name = course.get('course_name', '').lower()
                c_id = course.get('course_id', '').lower()
                t_name = offering.get('teacher_name', '').lower()
                
                # 如果没有关键词，或关键词匹配成功
                if (not keyword_lower) or (keyword_lower in c_name or 
                                           keyword_lower in c_id or 
                                           keyword_lower in t_name):
                    
                    found_any = True
                    seen_courses.add(unique_key)
                    self.course_selection_tree.insert("", "end", values=(
                        course.get('course_id', ''),
                        course.get('course_name', ''),
                        course.get('course_type', ''),
                        f"{course.get('credits', 0)}",
                        offering.get('teacher_name', '未知'),
                        offering.get('class_time', ''),
                        f"{offering.get('current_students', 0)}/{offering.get('max_students', 0)}",
                        "选课"
                    ), tags=(offering['offering_id'],))

        # 如果没有结果，显示提示
        if not found_any:
            self.course_selection_tree.insert("", "end", values=(
                "", "未找到匹配的课程", "", "", "", "", "", ""
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
        
        # 获取当前学期
        import os
        current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
        
        # 获取成绩
        all_grades = self.grade_manager.get_student_grades(self.user.id)
        
        # 过滤成绩：只显示当前学期及之前的成绩
        def semester_before_or_equal(semester1: str, semester2: str) -> bool:
            """
            判断 semester1 是否在 semester2 之前或等于 semester2
            学期格式：YYYY-YYYY-N（N=1为秋季，N=2为春季）
            """
            if not semester1 or not semester2:
                return False
            
            try:
                parts1 = semester1.split("-")
                parts2 = semester2.split("-")
                
                if len(parts1) < 3 or len(parts2) < 3:
                    return False
                
                year1 = int(parts1[0])
                term1 = int(parts1[2])
                year2 = int(parts2[0])
                term2 = int(parts2[2])
                
                # 先比较年份
                if year1 < year2:
                    return True
                elif year1 > year2:
                    return False
                else:
                    # 年份相同，比较学期（1=秋，2=春）
                    return term1 <= term2
            except Exception:
                return False
        
        # 过滤成绩
        grades = [g for g in all_grades if semester_before_or_equal(g.get('semester', ''), current_semester)]
        
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
            columns=("semester", "course_id", "course_name", "credits", "score", "grade", "gpa", "teacher"),
            show="headings",
            height=12
        )
        
        tree.heading("semester", text="学期")
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("score", text="成绩")
        tree.heading("grade", text="等级")
        tree.heading("gpa", text="绩点")
        tree.heading("teacher", text="教师")
        
        tree.column("semester", width=120)
        tree.column("course_id", width=100)
        tree.column("course_name", width=200)
        tree.column("credits", width=80)
        tree.column("score", width=80)
        tree.column("grade", width=80)
        tree.column("gpa", width=80)
        tree.column("teacher", width=100)
        
        # 获取学生入学年份，用于计算年级
        student_grade = self.user.extra_info.get('grade') or getattr(self.user, 'grade', None)
        if not student_grade:
            # 从数据库查询
            sql = "SELECT grade FROM students WHERE student_id = ?"
            result = self.db.execute_query(sql, (self.user.id,))
            if result:
                student_grade = result[0].get('grade')
        
        for grade in grades:
            # 格式化学期显示
            semester_str = grade.get('semester', '')
            semester_display = self._format_semester_display(semester_str, student_grade)
            
            tree.insert("", "end", values=(
                semester_display,
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
        
        # 学期选择 - 从环境变量或配置中读取当前学期
        import os
        current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
        semester_label = ctk.CTkLabel(
            self.content_frame,
            text=f"当前查看学期: {current_semester}（课表显示该学期的已选课程）",
            font=("Microsoft YaHei UI", 14),
            text_color="#666666"
        )
        semester_label.pack(pady=(0, 15), anchor="w", padx=20)
        
        # 获取选课记录（显示当前学期的所有已选课程，包括必修课程）
        enrollments = self.enrollment_manager.get_student_enrollments(
            self.user.id, status='enrolled'
        )
        
        # 过滤：只显示当前学期的课程，并过滤掉没有排课的课程
        # 注意：包括所有已选课程，包括默认必修课程
        enrollments = [
            e for e in enrollments 
            if e.get('semester') == current_semester
            and e.get('class_time') and e.get('class_time') != '未排课'
        ]
        
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
        
        # 初始化5天，每天14节课（包括晚上12-14节）
        for day in range(1, 6):
            schedule_data[day] = {}
            for period in range(1, 15):  # 1-14节
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
                    
                    # 确保节次在合理范围内（1-14节，支持晚上课程）
                    if start_period < 1 or end_period > 14 or start_period > end_period:
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
        # 定义14个单节次：上午5节（1-5），下午6节（6-11），晚上3节（12-14）
        periods = [str(i) for i in range(1, 15)]
        period_names = [f"第{i}节" for i in range(1, 15)]
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
        
        # 创建14行（每行代表一节课）
        cell_height = 65  # 增加高度以容纳更大的文字
        for i, (period, period_name) in enumerate(zip(periods, period_names)):
            row_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # 时间段标签（左侧）- 优化样式：上午、下午、晚上不同颜色
            if i < 5:
                period_label_bg = "#E8E8E8"  # 上午：浅灰
            elif i < 11:
                period_label_bg = "#D8E8F0"  # 下午：浅蓝
            else:
                period_label_bg = "#F0E8D8"  # 晚上：浅黄
            
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
        self.set_active_menu(6)  # 更新索引
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
    
    def show_curriculum(self):
        """显示培养方案"""
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
        
        # 查询培养方案
        # 排序：年级 -> 学期（秋季在春季之前）-> 类型（必修优先）-> 课程代码
        sql = """
            SELECT cm.grade, cm.term, cm.course_id, c.course_name, 
                   c.credits, cm.category
            FROM curriculum_matrix cm
            JOIN majors m ON cm.major_id = m.major_id
            JOIN courses c ON cm.course_id = c.course_id
            WHERE m.name = ?
            ORDER BY cm.grade, 
                     CASE WHEN cm.term = '秋' THEN 0 ELSE 1 END,
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
        
        # 创建表格
        tree = ttk.Treeview(
            table_frame,
            columns=("semester", "course_id", "course_name", "credits", "category"),
            show="headings",
            style="Curriculum.Treeview",
            height=20
        )
        
        # 设置列标题
        tree.heading("semester", text="学期")
        tree.heading("course_id", text="课程代码")
        tree.heading("course_name", text="课程名称")
        tree.heading("credits", text="学分")
        tree.heading("category", text="类型")
        
        # 设置列宽
        tree.column("semester", width=120, anchor="center")
        tree.column("course_id", width=100, anchor="center")
        tree.column("course_name", width=400, anchor="w")
        tree.column("credits", width=80, anchor="center")
        tree.column("category", width=80, anchor="center")
        
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
            
            # 学期名称
            term_cn = "秋季" if term == "秋" else "春季"
            grade_cn = {1: "一", 2: "二", 3: "三", 4: "四"}.get(grade, str(grade))
            semester_text = f"大{grade_cn}（{term_cn}）"
            
            # 插入数据
            tag = "required" if category == "必修" else "elective"
            tree.insert("", "end", values=(
                semester_text,
                course_id,
                course_name,
                f"{credits}",
                category
            ), tags=(tag,))
        
        # 设置标签颜色
        tree.tag_configure("required", foreground="#E74C3C")
        tree.tag_configure("elective", foreground="#3498DB")
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        Logger.info(f"学生查看培养方案: {self.user.name} ({major_name})")
    
    def show_ai_advice(self):
        """显示AI学习建议"""
        self.set_active_menu(5)  # 更新索引，因为添加了新菜单项
        self.clear_content()
        
        # 标题区域 - 更美观的设计
        title_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title = ctk.CTkLabel(
            title_frame,
            text="🤖 AI智能学习建议",
            font=("Microsoft YaHei UI", 28, "bold"),
            text_color=self.BUPT_BLUE
        )
        title.pack(side="left")
        
        # 说明文字 - 更精美的卡片样式
        desc_frame = ctk.CTkFrame(
            self.content_frame, 
            fg_color="#E8F4F8", 
            corner_radius=12,
            border_width=1,
            border_color=self.BUPT_LIGHT_BLUE
        )
        desc_frame.pack(fill="x", padx=20, pady=10)
        
        desc_label = ctk.CTkLabel(
            desc_frame,
            text="💡 基于您的专业背景、已选课程和行业趋势，AI将为您提供个性化的学习建议和职业规划指导",
            font=("Microsoft YaHei UI", 15),
            text_color="#2C3E50",
            wraplength=1000,
            justify="left"
        )
        desc_label.pack(pady=18, padx=25)
        
        # 按钮区域 - 更美观的布局
        button_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 15))
        
        # 生成建议按钮 - 更大更醒目
        generate_button = ctk.CTkButton(
            button_frame,
            text="✨ 生成学习建议",
            width=220,
            height=55,
            font=("Microsoft YaHei UI", 19, "bold"),
            fg_color=self.BUPT_BLUE,
            hover_color=self.BUPT_LIGHT_BLUE,
            corner_radius=12,
            command=self._generate_advice
        )
        generate_button.pack(side="left", padx=(0, 15))
        
        # 刷新数据按钮
        refresh_button = ctk.CTkButton(
            button_frame,
            text="🔄 刷新数据",
            width=160,
            height=55,
            font=("Microsoft YaHei UI", 17),
            fg_color=self.BUPT_LIGHT_BLUE,
            hover_color=self.BUPT_BLUE,
            corner_radius=12,
            command=self.show_ai_advice
        )
        refresh_button.pack(side="left", padx=5)
        
        # 显示当前选课信息预览
        self._show_course_preview()
    
    def _show_course_preview(self):
        """显示当前已选课程预览 - 美观的卡片式布局"""
        enrollments = self.enrollment_manager.get_student_enrollments(
            self.user.id, status='enrolled'
        )
        
        preview_frame = ctk.CTkFrame(
            self.content_frame, 
            fg_color="#F8F9FA", 
            corner_radius=15,
            border_width=2,
            border_color="#D0E8F0"
        )
        preview_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # 标题区域
        title_frame = ctk.CTkFrame(preview_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=25, pady=(20, 15))
        
        preview_title = ctk.CTkLabel(
            title_frame,
            text="📋 当前已选课程预览",
            font=("Microsoft YaHei UI", 20, "bold"),
            text_color=self.BUPT_BLUE
        )
        preview_title.pack(side="left")
        
        if not enrollments:
            no_course_label = ctk.CTkLabel(
                preview_frame,
                text="暂无已选课程，建议先进行选课后再生成学习建议",
                font=("Microsoft YaHei UI", 15),
                text_color="#666666"
            )
            no_course_label.pack(pady=20, padx=25, anchor="w")
        else:
            total_credits = sum(e['credits'] for e in enrollments)
            
            # 统计信息卡片
            stats_frame = ctk.CTkFrame(
                preview_frame,
                fg_color="#E3F2FD",
                corner_radius=10,
                border_width=1,
                border_color="#90CAF9"
            )
            stats_frame.pack(fill="x", padx=25, pady=(0, 15))
            
            stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
            stats_inner.pack(pady=12, padx=15)
            
            course_count_label = ctk.CTkLabel(
                stats_inner,
                text=f"📚 {len(enrollments)} 门课程",
                font=("Microsoft YaHei UI", 16, "bold"),
                text_color="#1976D2"
            )
            course_count_label.pack(side="left", padx=(0, 30))
            
            credits_label = ctk.CTkLabel(
                stats_inner,
                text=f"⭐ {total_credits} 学分",
                font=("Microsoft YaHei UI", 16, "bold"),
                text_color="#1976D2"
            )
            credits_label.pack(side="left")
            
            # 课程列表 - 使用滚动框架
            courses_container = ctk.CTkScrollableFrame(
                preview_frame,
                fg_color="transparent",
                corner_radius=0
            )
            courses_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
            
            # 显示所有课程（最多显示8门，超过的显示提示）
            display_count = min(8, len(enrollments))
            for i, enrollment in enumerate(enrollments[:display_count]):
                # 每个课程一个卡片
                course_card = ctk.CTkFrame(
                    courses_container,
                    fg_color="white",
                    corner_radius=10,
                    border_width=1,
                    border_color="#E0E0E0"
                )
                course_card.pack(fill="x", pady=6, padx=5)
                
                # 课程信息布局
                card_content = ctk.CTkFrame(course_card, fg_color="transparent")
                card_content.pack(fill="x", padx=15, pady=12)
                
                # 课程名称和代码
                course_name_label = ctk.CTkLabel(
                    card_content,
                    text=f"📖 {enrollment['course_name']}",
                    font=("Microsoft YaHei UI", 15, "bold"),
                    text_color="#2C3E50",
                    anchor="w"
                )
                course_name_label.pack(side="left", padx=(0, 15))
                
                # 课程代码
                course_id_label = ctk.CTkLabel(
                    card_content,
                    text=f"({enrollment['course_id']})",
                    font=("Microsoft YaHei UI", 13),
                    text_color="#7F8C8D",
                    anchor="w"
                )
                course_id_label.pack(side="left", padx=(0, 15))
                
                # 学分标签
                credits_badge = ctk.CTkFrame(
                    card_content,
                    fg_color=self.BUPT_LIGHT_BLUE,
                    corner_radius=12,
                    width=60,
                    height=24
                )
                credits_badge.pack(side="right")
                credits_badge.pack_propagate(False)
                
                credits_text = ctk.CTkLabel(
                    credits_badge,
                    text=f"{enrollment['credits']}学分",
                    font=("Microsoft YaHei UI", 12, "bold"),
                    text_color="white"
                )
                credits_text.pack(expand=True)
            
            # 如果还有更多课程
            if len(enrollments) > display_count:
                more_label = ctk.CTkLabel(
                    courses_container,
                    text=f"... 还有 {len(enrollments) - display_count} 门课程未显示",
                    font=("Microsoft YaHei UI", 13),
                    text_color="#95A5A6",
                    anchor="center"
                )
                more_label.pack(pady=10)
    
    def _generate_advice(self):
        """生成学习建议 - 打开新窗口显示"""
        # 检查API密钥
        try:
            advisor = QwenAdvisor()
        except RuntimeError as e:
            messagebox.showerror("错误", f"无法初始化AI服务：{str(e)}\n\n请设置环境变量 DASH_SCOPE_API_KEY")
            return
        
        # 打开新窗口显示建议
        self._open_advice_window()
    
    def _open_advice_window(self):
        """打开AI建议显示窗口"""
        # 创建新窗口
        advice_window = ctk.CTkToplevel(self.root)
        advice_window.title(f"AI学习建议 - {self.user.name}")
        advice_window.geometry("1000x700")
        
        # 设置窗口图标和样式
        advice_window.transient(self.root)  # 设置为父窗口的子窗口
        advice_window.grab_set()  # 模态窗口
        
        # 主容器
        main_frame = ctk.CTkFrame(advice_window, fg_color="white")
        main_frame.pack(fill="both", expand=True)
        
        # 顶部标题栏
        header_frame = ctk.CTkFrame(
            main_frame,
            fg_color=self.BUPT_BLUE,
            height=80,
            corner_radius=0
        )
        header_frame.pack(fill="x", side="top")
        header_frame.pack_propagate(False)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="🤖 AI智能学习建议",
            font=("Microsoft YaHei UI", 24, "bold"),
            text_color="white"
        )
        title_label.pack(side="left", padx=30, pady=25)
        
        close_button = ctk.CTkButton(
            header_frame,
            text="✕",
            width=40,
            height=40,
            font=("Microsoft YaHei UI", 18, "bold"),
            fg_color="transparent",
            hover_color="#E74C3C",
            text_color="white",
            command=advice_window.destroy
        )
        close_button.pack(side="right", padx=20, pady=20)
        
        # 内容区域
        content_frame = ctk.CTkFrame(main_frame, fg_color="#FAFAFA")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 状态提示区域
        status_frame = ctk.CTkFrame(
            content_frame,
            fg_color="#FFF9E6",
            corner_radius=12,
            border_width=2,
            border_color="#FFD700"
        )
        status_frame.pack(fill="x", pady=(0, 15))
        
        status_label = ctk.CTkLabel(
            status_frame,
            text="⏳ 正在生成学习建议，请稍候...",
            font=("Microsoft YaHei UI", 18, "bold"),
            text_color="#D68910"
        )
        status_label.pack(pady=15, padx=25)
        
        # 建议显示区域
        result_frame = ctk.CTkFrame(
            content_frame,
            corner_radius=15,
            border_width=2,
            border_color="#E0E0E0",
            fg_color="white"
        )
        result_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # 文本显示框
        advice_textbox = ctk.CTkTextbox(
            result_frame,
            font=("Microsoft YaHei UI", 16),
            wrap="word",
            corner_radius=12,
            fg_color="white",
            text_color="#2C3E50",
            border_width=1,
            border_color="#E0E0E0"
        )
        advice_textbox.pack(fill="both", expand=True, padx=20, pady=20)
        advice_textbox.insert("1.0", "正在生成建议，请稍候...")
        advice_textbox.configure(state="disabled")
        
        # 底部按钮区域
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))
        
        copy_button = ctk.CTkButton(
            button_frame,
            text="📋 复制建议",
            width=180,
            height=45,
            font=("Microsoft YaHei UI", 16, "bold"),
            fg_color=self.BUPT_LIGHT_BLUE,
            hover_color=self.BUPT_BLUE,
            corner_radius=12,
            command=lambda: self._copy_text_to_clipboard(advice_textbox, advice_window)
        )
        copy_button.pack(side="left", padx=(0, 15))
        
        # 在新线程中调用API
        def update_ui(advice, error):
            """更新UI的回调函数"""
            if error:
                status_frame.configure(fg_color="#FFEBEE", border_color="#E57373")
                status_label.configure(
                    text=f"❌ {error}",
                    text_color="#C62828"
                )
                advice_textbox.configure(state="normal")
                advice_textbox.delete("1.0", "end")
                error_text = f"生成建议时出现错误：\n\n{error}\n\n请检查：\n1. 是否设置了 DASH_SCOPE_API_KEY 环境变量\n2. API密钥是否有效\n3. 网络连接是否正常"
                advice_textbox.insert("1.0", error_text)
                advice_textbox.configure(state="disabled", text_color="#C62828")
            elif advice:
                status_frame.configure(fg_color="#E8F5E9", border_color="#81C784")
                status_label.configure(
                    text="✅ 建议生成完成",
                    text_color="#2E7D32"
                )
                advice_textbox.configure(state="normal")
                advice_textbox.delete("1.0", "end")
                advice_textbox.insert("1.0", advice)
                advice_textbox.configure(state="disabled", text_color="#2C3E50")
        
        # 在新线程中调用API
        thread = threading.Thread(
            target=self._call_qwen_api_for_window,
            args=(advice_window, update_ui),
            daemon=True
        )
        thread.start()
    
    def _call_qwen_api_for_window(self, window, update_callback):
        """为新窗口调用Qwen API"""
        try:
            import os
            current_semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
            
            # 获取学生信息
            student_info = self._get_student_info()
            
            # 获取所有学期的选课记录
            all_enrollments = self.enrollment_manager.get_student_enrollments(
                self.user.id, status='enrolled'
            )
            
            # 获取所有学期的成绩
            all_grades = self.grade_manager.get_student_grades(self.user.id)
            
            # 分离以往学期、当前学期和下个学期的数据
            past_semester_courses = []
            current_semester_courses = []
            past_semester_grades = []
            
            # 解析当前学期，计算下个学期
            sem_parts = current_semester.split("-")
            current_year = int(sem_parts[0])
            current_term = int(sem_parts[-1])  # 1=秋, 2=春
            
            # 计算下个学期
            if current_term == 1:
                next_semester = f"{current_year}-{current_year+1}-2"  # 春季
            else:
                next_semester = f"{current_year+1}-{current_year+2}-1"  # 秋季
            
            # 分类课程和成绩
            for e in all_enrollments:
                semester = e.get('semester', '')
                course_data = {
                    'course_name': e.get('course_name', ''),
                    'course_id': e.get('course_id', ''),
                    'credits': e.get('credits', 0),
                    'teacher_name': e.get('teacher_name', ''),
                    'course_type': e.get('course_type', ''),
                    'semester': semester
                }
                
                if semester < current_semester:
                    past_semester_courses.append(course_data)
                elif semester == current_semester:
                    current_semester_courses.append(course_data)
            
            # 获取以往学期的成绩（所有有成绩的历史课程）
            # 将成绩与课程关联，确保每个历史课程都有对应的成绩信息
            grades_by_course_semester = {}
            for grade in all_grades:
                semester = grade.get('semester', '')
                course_id = grade.get('course_id', '')
                if semester < current_semester:
                    key = (course_id, semester)
                    grades_by_course_semester[key] = {
                        'course_name': grade.get('course_name', ''),
                        'course_id': course_id,
                        'score': grade.get('score', 0),
                        'gpa': grade.get('gpa', 0),
                        'grade_level': grade.get('grade_level', ''),
                        'semester': semester
                    }
            
            # 将历史课程与成绩合并
            # 对于有成绩的课程，添加成绩信息；对于没有成绩的课程，也保留（可能是刚选课还没成绩）
            # 确保所有有成绩的历史课程都在past_semester_grades中
            for course in past_semester_courses:
                key = (course['course_id'], course['semester'])
                if key in grades_by_course_semester:
                    # 有成绩，添加到成绩列表
                    past_semester_grades.append(grades_by_course_semester[key])
            
            # 确保所有有成绩的历史课程都在past_semester_grades中
            # past_semester_courses包含所有历史课程（无论是否有成绩）
            
            # 获取下个学期的推荐课程（从培养方案中获取）
            next_semester_courses = self._get_next_semester_courses(student_info, next_semester)
            
            # 调用API
            advisor = QwenAdvisor()
            advice = advisor.advise(
                student_info, 
                current_semester_courses,
                past_semester_courses=past_semester_courses,
                past_semester_grades=past_semester_grades,
                next_semester_courses=next_semester_courses
            )
            
            # 更新UI（需要在主线程中执行）
            window.after(0, update_callback, advice, None)
            
        except Exception as e:
            error_msg = f"生成建议失败：{str(e)}"
            Logger.error(error_msg, exc_info=True)
            window.after(0, update_callback, None, error_msg)
    
    def _get_next_semester_courses(self, student_info: dict, next_semester: str) -> list:
        """获取下个学期的推荐课程（从培养方案中获取）"""
        try:
            # 获取学生的专业ID
            sql = "SELECT major_id, grade FROM students WHERE student_id = ?"
            result = self.db.execute_query(sql, (self.user.id,))
            if not result:
                return []
            
            major_id = result[0].get('major_id')
            grade = result[0].get('grade', 1)
            
            if not major_id:
                return []
            
            # 计算下个学期的年级和学期（秋/春）
            sem_parts = next_semester.split("-")
            next_year = int(sem_parts[0])
            next_term = int(sem_parts[-1])  # 1=秋, 2=春
            
            # 计算下个学期的年级（简化计算，假设每学年2个学期）
            # 这里需要根据实际情况调整
            academic_year = grade  # 当前年级
            if next_term == 1:  # 秋季学期，年级不变
                next_grade = academic_year
            else:  # 春季学期，年级不变（同一学年）
                next_grade = academic_year
            
            # 从curriculum_matrix获取下个学期的课程
            term_str = '秋' if next_term == 1 else '春'
            sql = """
                SELECT DISTINCT cm.course_id, c.course_name, c.credits, c.course_type
                FROM curriculum_matrix cm
                JOIN courses c ON cm.course_id = c.course_id
                WHERE cm.major_id = ? 
                AND cm.grade = ?
                AND cm.term = ?
            """
            result = self.db.execute_query(sql, (major_id, next_grade, term_str))
            
            next_courses = []
            for row in result:
                next_courses.append({
                    'course_name': row.get('course_name', ''),
                    'course_id': row.get('course_id', ''),
                    'credits': row.get('credits', 0),
                    'course_type': row.get('course_type', ''),
                    'semester': next_semester
                })
            
            return next_courses
            
        except Exception as e:
            Logger.warning(f"获取下个学期课程失败: {e}")
            return []
    
    def _format_semester_display(self, semester: str, student_grade: int = None) -> str:
        """
        将学期字符串格式化为"大一（春）"这样的格式
        
        Args:
            semester: 学期字符串，如 "2024-2025-2"
            student_grade: 学生入学年份，如 2024
        
        Returns:
            格式化后的学期字符串，如 "大一（春）"
        """
        if not semester:
            return ""
        
        try:
            # 解析学期字符串，如 "2024-2025-2"
            parts = semester.split("-")
            if len(parts) < 3:
                return semester
            
            start_year = int(parts[0])
            term_num = int(parts[-1])  # 1=秋, 2=春
            
            # 如果没有提供学生入学年份，尝试从user对象获取
            if not student_grade:
                student_grade = self.user.extra_info.get('grade') or getattr(self.user, 'grade', None)
            
            # 计算年级
            if student_grade:
                grade_level = start_year - student_grade + 1
                if grade_level < 1:
                    grade_level = 1
                elif grade_level > 4:
                    grade_level = 4
            else:
                # 如果无法确定入学年份，使用学期年份推断（假设是2024级）
                grade_level = start_year - 2024 + 1
                if grade_level < 1:
                    grade_level = 1
                elif grade_level > 4:
                    grade_level = 4
            
            # 年级中文映射
            grade_map = {1: "一", 2: "二", 3: "三", 4: "四"}
            grade_cn = grade_map.get(grade_level, "一")
            
            # 学期中文
            term_cn = "秋" if term_num == 1 else "春"
            
            return f"大{grade_cn}（{term_cn}）"
        except Exception:
            # 如果解析失败，返回原始字符串
            return semester
    
    def _copy_text_to_clipboard(self, textbox, window):
        """复制文本到剪贴板"""
        try:
            text = textbox.get("1.0", "end-1c")
            if text and text.strip():
                window.clipboard_clear()
                window.clipboard_append(text)
                messagebox.showinfo("成功", "建议已复制到剪贴板", parent=window)
            else:
                messagebox.showwarning("提示", "没有可复制的内容", parent=window)
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}", parent=window)
    
    def _get_student_info(self) -> dict:
        """获取学生信息"""
        # 查询学院名称
        college_name = ""
        if hasattr(self.user, 'college_code') and self.user.college_code:
            sql = "SELECT name FROM colleges WHERE college_code = ?"
            result = self.db.execute_query(sql, (self.user.college_code,))
            if result:
                college_name = result[0].get('name', '')
        
        # 如果没有从user对象获取，尝试从数据库查询
        if not college_name:
            sql = """
                SELECT s.major, s.grade, s.class_name, c.name as college_name
                FROM students s
                LEFT JOIN colleges c ON s.college_code = c.college_code
                WHERE s.student_id = ?
            """
            result = self.db.execute_query(sql, (self.user.id,))
            if result:
                row = result[0]
                college_name = row.get('college_name', '')
        
        return {
            'name': self.user.name,
            'id': self.user.id,
            'major': self.user.extra_info.get('major') or getattr(self.user, 'major', ''),
            'college': college_name,
            'grade': self.user.extra_info.get('grade') or getattr(self.user, 'grade', ''),
            'class_name': self.user.extra_info.get('class_name') or getattr(self.user, 'class_name', '')
        }
    
    def _update_advice_result(self, advice: Optional[str], error: Optional[str]):
        """更新建议结果显示"""
        if self.advice_status_label:
            if error:
                # 错误状态 - 红色背景
                status_frame = self.advice_status_label.master
                status_frame.configure(fg_color="#FFEBEE", border_color="#E57373")
                self.advice_status_label.configure(
                    text=f"❌ {error}",
                    text_color="#C62828",
                    font=("Microsoft YaHei UI", 16, "bold")
                )
            else:
                # 成功状态 - 绿色背景
                status_frame = self.advice_status_label.master
                status_frame.configure(fg_color="#E8F5E9", border_color="#81C784")
                self.advice_status_label.configure(
                    text="✅ 建议生成完成",
                    text_color="#2E7D32",
                    font=("Microsoft YaHei UI", 17, "bold")
                )
        
        if self.advice_text_widget:
            self.advice_text_widget.configure(state="normal")
            self.advice_text_widget.delete("1.0", "end")
            
            if error:
                error_text = f"生成建议时出现错误：\n\n{error}\n\n请检查：\n1. 是否设置了 DASH_SCOPE_API_KEY 环境变量\n2. API密钥是否有效\n3. 网络连接是否正常"
                self.advice_text_widget.insert("1.0", error_text)
                self.advice_text_widget.configure(text_color="#C62828")
            elif advice:
                self.advice_text_widget.insert("1.0", advice)
                self.advice_text_widget.configure(text_color="#2C3E50")
            else:
                self.advice_text_widget.insert("1.0", "未能生成建议，请重试")
                self.advice_text_widget.configure(text_color="#666666")
            
            self.advice_text_widget.configure(state="disabled")
            
            # 添加复制按钮（只在有建议时显示）
            if advice and not self._copy_button_created:
                copy_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
                copy_frame.pack(pady=(0, 10), padx=20)
                
                copy_button = ctk.CTkButton(
                    copy_frame,
                    text="📋 复制建议",
                    width=180,
                    height=45,
                    font=("Microsoft YaHei UI", 16, "bold"),
                    fg_color=self.BUPT_LIGHT_BLUE,
                    hover_color=self.BUPT_BLUE,
                    corner_radius=10,
                    command=lambda: self._copy_advice_to_clipboard()
                )
                copy_button.pack()
                self._copy_button_created = True
    
    def _copy_advice_to_clipboard(self):
        """复制建议到剪贴板"""
        if self.advice_text_widget:
            advice_text = self.advice_text_widget.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(advice_text)
            messagebox.showinfo("成功", "建议已复制到剪贴板")
    
    def do_logout(self):
        """注销登录"""
        if messagebox.askyesno("确认", "确定要退出登录吗？"):
            self.root.destroy()
            self.logout_callback()
    
    def on_close(self):
        """关闭窗口"""
        self.do_logout()

