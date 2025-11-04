"""
数据库模块 - 北京邮电大学教学管理系统
负责数据库的创建、连接和基本操作
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from utils.logger import Logger


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "data/bupt_teaching.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        
        # 确保data目录存在
        Path(db_path).parent.mkdir(exist_ok=True)
        
        # 连接数据库
        self.connect()
        
        # 初始化表结构
        self.init_tables()
        
        Logger.info("数据库初始化完成")
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 返回字典格式
            self.cursor = self.conn.cursor()
            Logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            Logger.error(f"数据库连接失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            Logger.info("数据库连接已关闭")
    
    def init_tables(self):
        """初始化数据库表结构"""
        
        # 1. 学生表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,      -- 学号（10位）
                name TEXT NOT NULL,               -- 姓名
                password TEXT NOT NULL,           -- 密码哈希
                gender TEXT,                      -- 性别
                birth_date TEXT,                  -- 出生日期
                major TEXT,                       -- 专业
                grade INTEGER,                    -- 年级
                class_name TEXT,                  -- 班级
                enrollment_date TEXT,             -- 入学日期
                status TEXT DEFAULT 'active',     -- 学籍状态：active/suspended/graduated
                email TEXT,                       -- 邮箱
                phone TEXT,                       -- 电话
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 2. 教师表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT PRIMARY KEY,      -- 教师工号
                name TEXT NOT NULL,               -- 姓名
                password TEXT NOT NULL,           -- 密码哈希
                gender TEXT,                      -- 性别
                title TEXT,                       -- 职称：教授/副教授/讲师
                department TEXT,                  -- 所属院系
                email TEXT,                       -- 邮箱
                phone TEXT,                       -- 电话
                hire_date TEXT,                   -- 入职日期
                status TEXT DEFAULT 'active',     -- 状态：active/inactive
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 3. 课程表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,       -- 课程代码
                course_name TEXT NOT NULL,        -- 课程名称
                credits REAL NOT NULL,            -- 学分
                hours INTEGER,                    -- 学时
                course_type TEXT,                 -- 课程类型：必修/选修/通识
                department TEXT,                  -- 开课院系
                description TEXT,                 -- 课程描述
                prerequisite TEXT,                -- 先修课程
                max_students INTEGER DEFAULT 60,  -- 最大选课人数
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 4. 开课计划表（课程实例）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_offerings (
                offering_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,          -- 课程代码
                teacher_id TEXT NOT NULL,         -- 授课教师
                semester TEXT NOT NULL,           -- 学期：2024-2025-1
                class_time TEXT,                  -- 上课时间：周一1-2节
                classroom TEXT,                   -- 教室
                current_students INTEGER DEFAULT 0, -- 当前选课人数
                max_students INTEGER DEFAULT 60,  -- 最大人数
                status TEXT DEFAULT 'open',       -- 状态：open/closed/full
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(course_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
            )
        ''')
        
        # 5. 选课表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,         -- 学号
                offering_id INTEGER NOT NULL,     -- 开课计划ID
                semester TEXT NOT NULL,           -- 学期
                enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'enrolled',   -- 状态：enrolled/dropped/completed
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id),
                UNIQUE(student_id, offering_id)   -- 防止重复选课
            )
        ''')
        
        # 6. 成绩表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id INTEGER NOT NULL,   -- 选课记录ID
                student_id TEXT NOT NULL,         -- 学号
                offering_id INTEGER NOT NULL,     -- 开课计划ID
                score REAL,                       -- 成绩（0-100）
                grade_level TEXT,                 -- 等级：A/B/C/D/F
                gpa REAL,                         -- 绩点（4.0制）
                exam_type TEXT DEFAULT 'final',   -- 考试类型：midterm/final/makeup
                remarks TEXT,                     -- 备注
                input_by TEXT,                    -- 录入教师
                input_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id)
            )
        ''')
        
        # 7. 系统日志表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,            -- 用户ID（学号或工号）
                user_type TEXT NOT NULL,          -- 用户类型：student/teacher
                action TEXT NOT NULL,             -- 操作类型
                target TEXT,                      -- 操作目标
                details TEXT,                     -- 详细信息
                ip_address TEXT,                  -- IP地址
                status TEXT,                      -- 状态：success/failed
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        Logger.info("数据表初始化完成")
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict]:
        """
        执行查询语句
        
        Args:
            sql: SQL查询语句
            params: 查询参数
        
        Returns:
            查询结果列表
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            Logger.error(f"查询执行失败: {e}, SQL: {sql}")
            return []
    
    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行更新语句（INSERT/UPDATE/DELETE）
        
        Args:
            sql: SQL语句
            params: 参数
        
        Returns:
            影响的行数
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            self.conn.commit()
            return self.cursor.rowcount
        except Exception as e:
            Logger.error(f"更新执行失败: {e}, SQL: {sql}")
            self.conn.rollback()
            return 0
    
    def insert_data(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        插入数据（便捷方法）
        
        Args:
            table: 表名
            data: 数据字典
        
        Returns:
            新插入记录的ID
        """
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            self.cursor.execute(sql, tuple(data.values()))
            self.conn.commit()
            
            return self.cursor.lastrowid
        except Exception as e:
            Logger.error(f"插入数据失败: {e}, 表: {table}")
            self.conn.rollback()
            return None
    
    def update_data(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        """
        更新数据
        
        Args:
            table: 表名
            data: 要更新的数据
            condition: 更新条件
        
        Returns:
            影响的行数
        """
        try:
            set_clause = ', '.join([f"{k}=?" for k in data.keys()])
            where_clause = ' AND '.join([f"{k}=?" for k in condition.keys()])
            sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            params = tuple(data.values()) + tuple(condition.values())
            self.cursor.execute(sql, params)
            self.conn.commit()
            
            return self.cursor.rowcount
        except Exception as e:
            Logger.error(f"更新数据失败: {e}, 表: {table}")
            self.conn.rollback()
            return 0
    
    def delete_data(self, table: str, condition: Dict[str, Any]) -> int:
        """
        删除数据
        
        Args:
            table: 表名
            condition: 删除条件
        
        Returns:
            影响的行数
        """
        try:
            where_clause = ' AND '.join([f"{k}=?" for k in condition.keys()])
            sql = f"DELETE FROM {table} WHERE {where_clause}"
            
            self.cursor.execute(sql, tuple(condition.values()))
            self.conn.commit()
            
            return self.cursor.rowcount
        except Exception as e:
            Logger.error(f"删除数据失败: {e}, 表: {table}")
            self.conn.rollback()
            return 0
    
    def init_demo_data(self):
        """初始化演示数据"""
        from utils.crypto import CryptoUtil
        
        # 检查是否已有数据
        result = self.execute_query("SELECT COUNT(*) as count FROM students")
        if result and result[0]['count'] > 0:
            Logger.info("数据库已有数据，跳过初始化演示数据")
            return
        
        Logger.info("开始初始化演示数据...")
        
        # 1. 添加教师
        teachers = [
            {
                'teacher_id': 'teacher001',
                'name': '张教授',
                'password': CryptoUtil.hash_password('teacher123'),
                'gender': '男',
                'title': '教授',
                'department': '计算机学院',
                'email': 'zhang@bupt.edu.cn',
                'phone': '010-12345678'
            },
            {
                'teacher_id': 'teacher002',
                'name': '李副教授',
                'password': CryptoUtil.hash_password('teacher123'),
                'gender': '女',
                'title': '副教授',
                'department': '计算机学院',
                'email': 'li@bupt.edu.cn',
                'phone': '010-12345679'
            }
        ]
        
        for teacher in teachers:
            self.insert_data('teachers', teacher)
        
        # 2. 添加学生
        students = [
            {
                'student_id': '2021211001',
                'name': '李明',
                'password': CryptoUtil.hash_password('student123'),
                'gender': '男',
                'major': '计算机科学与技术',
                'grade': 2021,
                'class_name': '2021211',
                'email': '2021211001@bupt.edu.cn'
            },
            {
                'student_id': '2021211002',
                'name': '王芳',
                'password': CryptoUtil.hash_password('student123'),
                'gender': '女',
                'major': '计算机科学与技术',
                'grade': 2021,
                'class_name': '2021211',
                'email': '2021211002@bupt.edu.cn'
            },
            {
                'student_id': '2021211003',
                'name': '张伟',
                'password': CryptoUtil.hash_password('student123'),
                'gender': '男',
                'major': '软件工程',
                'grade': 2021,
                'class_name': '2021212',
                'email': '2021211003@bupt.edu.cn'
            }
        ]
        
        for student in students:
            self.insert_data('students', student)
        
        # 3. 添加课程
        courses = [
            {
                'course_id': 'CS101',
                'course_name': 'Python程序设计',
                'credits': 3.0,
                'hours': 48,
                'course_type': '必修',
                'department': '计算机学院',
                'description': 'Python语言基础与应用'
            },
            {
                'course_id': 'CS102',
                'course_name': '数据结构',
                'credits': 4.0,
                'hours': 64,
                'course_type': '必修',
                'department': '计算机学院',
                'description': '数据结构与算法'
            },
            {
                'course_id': 'CS201',
                'course_name': '数据库原理',
                'credits': 3.0,
                'hours': 48,
                'course_type': '必修',
                'department': '计算机学院',
                'description': '数据库系统原理与应用'
            },
            {
                'course_id': 'CS301',
                'course_name': '机器学习',
                'credits': 3.0,
                'hours': 48,
                'course_type': '选修',
                'department': '计算机学院',
                'description': '机器学习基础与应用'
            }
        ]
        
        for course in courses:
            self.insert_data('courses', course)
        
        # 4. 添加开课计划
        offerings = [
            {
                'course_id': 'CS101',
                'teacher_id': 'teacher001',
                'semester': '2024-2025-2',
                'class_time': '周一1-2节，周三3-4节',
                'classroom': '教三201',
                'max_students': 60
            },
            {
                'course_id': 'CS102',
                'teacher_id': 'teacher001',
                'semester': '2024-2025-2',
                'class_time': '周二1-2节，周四3-4节',
                'classroom': '教三202',
                'max_students': 60
            },
            {
                'course_id': 'CS201',
                'teacher_id': 'teacher002',
                'semester': '2024-2025-2',
                'class_time': '周三1-2节，周五3-4节',
                'classroom': '教三203',
                'max_students': 50
            },
            {
                'course_id': 'CS301',
                'teacher_id': 'teacher002',
                'semester': '2024-2025-2',
                'class_time': '周一5-6节，周三5-6节',
                'classroom': '教三301',
                'max_students': 40
            }
        ]
        
        for offering in offerings:
            self.insert_data('course_offerings', offering)
        
        Logger.info("演示数据初始化完成")
        self.conn.commit()


# 单例模式
_db_instance = None

def get_database() -> Database:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance


if __name__ == "__main__":
    # 测试数据库
    db = Database("data/test.db")
    db.init_demo_data()
    
    # 测试查询
    students = db.execute_query("SELECT * FROM students")
    print("学生列表：")
    for s in students:
        print(f"  {s['student_id']} - {s['name']} - {s['major']}")
    
    courses = db.execute_query("SELECT * FROM courses")
    print("\n课程列表：")
    for c in courses:
        print(f"  {c['course_id']} - {c['course_name']} - {c['credits']}学分")
    
    db.close()

