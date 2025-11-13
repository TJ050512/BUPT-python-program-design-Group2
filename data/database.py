"""
数据库模块 - BUPT 教学管理系统（重构）
- 新增学院/专业/教室/节次/关系表
- 学号/工号/学院编号格式校验（SQLite GLOB/CHECK）
- 公选课仅晚间、跨专业名额限制的触发器
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
        """初始化数据库表结构（增强版，保留原有字段 + 新增学院/专业/教室/节次/触发器）"""

        # === 原有基础表（完全保留） ===

        # 1. 学生表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                batch_no INTEGER,
                gender TEXT,
                birth_date TEXT,
                major TEXT,
                grade INTEGER,
                class_name TEXT,
                enrollment_date TEXT,
                status TEXT DEFAULT 'active',
                email TEXT,
                phone TEXT,
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
                title TEXT,                       -- 职称：教授/副教授/讲师/助教/研究员...
                job_type TEXT,                    -- 岗位类型：教学科研岗/实验岗/管理岗/辅导员
                hire_level TEXT,                  -- 职级：正高级/副高级/中级/初级
                department TEXT,                  -- 所属院系
                email TEXT,                       -- 邮箱
                phone TEXT,                       -- 电话
                hire_date TEXT,                   -- 入职日期
                status TEXT DEFAULT 'active',     -- 状态：active/inactive
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2.5 管理员表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                role TEXT DEFAULT 'admin',
                department TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. 课程表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                credits REAL NOT NULL,
                hours INTEGER,
                course_type TEXT,
                department TEXT,
                description TEXT,
                prerequisite TEXT,
                max_students INTEGER DEFAULT 60,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_public_elective INTEGER DEFAULT 0   -- 是否公选课
            )
        ''')

        # 4. 开课计划表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS course_offerings (
                offering_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id TEXT NOT NULL,
                teacher_id TEXT NOT NULL,
                semester TEXT NOT NULL,
                class_time TEXT,
                classroom TEXT,
                current_students INTEGER DEFAULT 0,
                max_students INTEGER DEFAULT 60,
                status TEXT DEFAULT 'open',
                classroom_id INTEGER,
                is_cross_major_open INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(course_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
            )
        ''')

        # === 新增学院/专业结构 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS colleges (
                college_code TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                CHECK (length(college_code)=7 AND college_code GLOB '202[1-5][0-9][0-9][0-9]')
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS majors (
                major_id INTEGER PRIMARY KEY AUTOINCREMENT,
                college_code TEXT NOT NULL,
                name TEXT NOT NULL,
                code TEXT UNIQUE,
                FOREIGN KEY (college_code) REFERENCES colleges(college_code) ON DELETE CASCADE
            )
        ''')

        # 学生外键字段（只在不存在时添加）
        try:
            self.cursor.execute("ALTER TABLE students ADD COLUMN college_code TEXT;")
        except Exception:
            pass
        try:
            self.cursor.execute("ALTER TABLE students ADD COLUMN major_id INTEGER;")
        except Exception:
            pass

        # === 校验触发器 ===
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS _students_fmt_guard(
                student_id TEXT PRIMARY KEY,
                CHECK (
                    length(student_id)=10
                    AND student_id GLOB '20[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'
                )
            );

            CREATE TRIGGER IF NOT EXISTS trg_students_format_ai
            AFTER INSERT ON students
            WHEN NEW.student_id IS NOT NULL
            BEGIN
                INSERT OR REPLACE INTO _students_fmt_guard(student_id) VALUES (NEW.student_id);
            END;

            CREATE TRIGGER IF NOT EXISTS trg_students_college_match_bi
            BEFORE INSERT ON students
            WHEN NEW.college_code IS NOT NULL
            BEGIN
                SELECT
                    CASE
                        WHEN substr(NEW.student_id,5,3) <> NEW.college_code
                        THEN RAISE(ABORT, '学生学号与学院专业编码不匹配（yyy部分应等于college_code）')
                    END;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_students_college_match_bu
            BEFORE UPDATE OF student_id, college_code ON students
            BEGIN
                SELECT
                    CASE WHEN NEW.college_code IS NOT NULL
                        AND substr(NEW.student_id,1,7) <> NEW.college_code
                    THEN RAISE(ABORT, '学生学号与学院编号不匹配')
                END;
            END;
        ''')

        # === 教师工号格式校验 ===
        self.cursor.executescript('''
            CREATE TABLE IF NOT EXISTS _teachers_fmt_guard(
                teacher_id TEXT PRIMARY KEY,
                CHECK (length(teacher_id)=10 AND teacher_id GLOB '20[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]')
            );

            CREATE TRIGGER IF NOT EXISTS trg_teachers_format_ai
            AFTER INSERT ON teachers
            WHEN NEW.teacher_id IS NOT NULL
            BEGIN
                INSERT OR REPLACE INTO _teachers_fmt_guard(teacher_id) VALUES (NEW.teacher_id);
            END;
        ''')

        # === 教室表 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS classrooms (
                classroom_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location_type TEXT NOT NULL,
                seat_count INTEGER NOT NULL,
                room_type TEXT NOT NULL,
                UNIQUE(name),
                CHECK (location_type IN ('1','2','3','4','主','体育馆','体育场')),
                CHECK (seat_count IN (32,64,128)),
                CHECK (room_type IN ('普通教室','互动研讨教室','智慧教室','会议室','体育馆','体育场'))
            )
        ''')

        # === 节次表 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slots (
                slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week INTEGER NOT NULL,
                section_no INTEGER NOT NULL,
                starts_at TEXT NOT NULL,
                ends_at TEXT NOT NULL,
                session TEXT NOT NULL,
                CHECK (day_of_week BETWEEN 1 AND 7),
                CHECK (session IN ('AM','PM','EVENING'))
            )
        ''')

        # === 教师-专业-课程关系表 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_major_course (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id TEXT NOT NULL,
                major_id INTEGER,
                course_id TEXT NOT NULL,
                role TEXT DEFAULT '讲授',
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
                FOREIGN KEY (major_id) REFERENCES majors(major_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )
        ''')

        # === 培养方案表 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS program_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                major_id INTEGER NOT NULL,
                course_id TEXT NOT NULL,
                course_category TEXT NOT NULL,
                cross_major_quota INTEGER DEFAULT 0,
                grade_recommendation INTEGER,
                UNIQUE(major_id, course_id),
                CHECK (course_category IN ('必修','选修','公选')),
                FOREIGN KEY (major_id) REFERENCES majors(major_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )
        ''')

        # === 开课节次表 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS offering_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offering_id INTEGER NOT NULL,
                slot_id INTEGER NOT NULL,
                classroom_id INTEGER NOT NULL,
                FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id) ON DELETE CASCADE,
                FOREIGN KEY (slot_id) REFERENCES time_slots(slot_id),
                FOREIGN KEY (classroom_id) REFERENCES classrooms(classroom_id),
                UNIQUE (offering_id, slot_id)
            )
        ''')

        # === 选课表（保留原字段） ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                offering_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'enrolled',
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id),
                UNIQUE(student_id, offering_id)
            )
        ''')

        # === 成绩表（保留原字段） ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                offering_id INTEGER NOT NULL,
                score REAL,
                grade_level TEXT,
                gpa REAL,
                exam_type TEXT DEFAULT 'final',
                remarks TEXT,
                input_by TEXT,
                input_date TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id)
            )
        ''')

        # === 系统日志表 ===
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_type TEXT NOT NULL,
                action TEXT NOT NULL,
                target TEXT,
                details TEXT,
                ip_address TEXT,
                status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # === 触发器（公选课仅晚间 & 跨专业限额） ===
        self.cursor.executescript('''
            CREATE TRIGGER IF NOT EXISTS trg_public_only_evening_bi
            BEFORE INSERT ON offering_sessions
            BEGIN
            SELECT
            CASE
                WHEN (SELECT is_public_elective FROM courses c
                    JOIN course_offerings o ON o.course_id=c.course_id
                    WHERE o.offering_id=NEW.offering_id)=1
                AND (SELECT session FROM time_slots WHERE slot_id=NEW.slot_id) <> 'EVENING'
                THEN RAISE(ABORT,'公选课必须安排在晚间节次(19:20~20:55)')
            END;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_cross_major_quota_bi
            BEFORE INSERT ON enrollments
            BEGIN
                SELECT
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM program_courses pc
                        JOIN course_offerings o ON o.course_id = pc.course_id
                        JOIN students s ON s.student_id = NEW.student_id
                        WHERE o.offering_id = NEW.offering_id
                            AND pc.course_category IN ('必修','选修')
                            AND s.major_id IS NOT NULL
                            AND s.major_id <> pc.major_id
                    )
                    THEN
                    CASE
                        WHEN (
                            SELECT pcx.cross_major_quota - (
                                SELECT COUNT(*)
                                FROM enrollments e
                                JOIN students sx ON sx.student_id = e.student_id
                                WHERE e.offering_id = NEW.offering_id
                                AND sx.major_id IS NOT NULL
                                AND sx.major_id <> (
                                    SELECT pc2.major_id
                                    FROM program_courses pc2
                                    JOIN course_offerings o2 ON o2.course_id=pc2.course_id
                                    WHERE o2.offering_id=NEW.offering_id
                                    LIMIT 1
                                )
                            )
                            FROM program_courses pcx
                            JOIN course_offerings ox ON ox.course_id = pcx.course_id
                            WHERE ox.offering_id = NEW.offering_id
                            LIMIT 1
                        ) <= 0
                        THEN RAISE(ABORT,'跨专业名额已满')
                    END
                END;
            END;
        ''')

        # ====== 兼容性追加字段（已存在则跳过） ======
        # 学生表：入学方式 / 学制（年）
        for sql in [
            "ALTER TABLE students ADD COLUMN admission_type TEXT",  # 保送/统招/推免/交换/留学生等
            "ALTER TABLE students ADD COLUMN program_years INTEGER" # 2/3/4/5 年等
        ]:
            try: self.cursor.execute(sql)
            except Exception: pass

        # 课程表：公选标记已存在；再加 credit_type（学位课/任选/通识等）
        try: self.cursor.execute("ALTER TABLE courses ADD COLUMN credit_type TEXT")
        except Exception: pass

        # 教师-课程关系表：主讲标记
        try: self.cursor.execute("ALTER TABLE teacher_major_course ADD COLUMN main_teacher INTEGER DEFAULT 1")
        except Exception: pass

        # 教室表：设备信息（JSON 或 TEXT）
        try: self.cursor.execute("ALTER TABLE classrooms ADD COLUMN available_equipment TEXT")
        except Exception: pass

        # 成绩表：补考/重修轮次
        for sql in [
            "ALTER TABLE grades ADD COLUMN is_makeup INTEGER DEFAULT 0",
            "ALTER TABLE grades ADD COLUMN exam_round INTEGER"      # 1=初考,2=补考,3=重修...
        ]:
            try: self.cursor.execute(sql)
            except Exception: pass

        # 学院表：院长姓名
        try: self.cursor.execute("ALTER TABLE colleges ADD COLUMN dean_name TEXT")
        except Exception: pass

        # 日志表：设备/系统/浏览器
        for sql in [
            "ALTER TABLE system_logs ADD COLUMN device TEXT",
            "ALTER TABLE system_logs ADD COLUMN os TEXT",
            "ALTER TABLE system_logs ADD COLUMN browser TEXT"
        ]:
            try: self.cursor.execute(sql)
            except Exception: pass
        self.conn.commit()
        Logger.info("✅ 数据表结构初始化完成（保留原信息 + 增强学院/专业/教室/节次）")

    
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
    
    def ensure_admin_exists(self):
        """确保默认管理员账号存在"""
        from utils.crypto import CryptoUtil
        
        # 检查管理员是否存在
        admin_check = self.execute_query("SELECT * FROM admins WHERE admin_id='admin001'")
        
        if not admin_check:
            Logger.info("创建默认管理员账号...")
            admin_data = {
                'admin_id': 'admin001',
                'name': '系统管理员',
                'password': CryptoUtil.hash_password('admin123'),
                'email': 'admin@bupt.edu.cn',
                'phone': '010-12345000',
                'role': 'admin',
                'department': '教务处'
            }
            try:
                self.insert_data('admins', admin_data)
                Logger.info("默认管理员账号创建成功 (admin001/admin123)")
            except Exception as e:
                Logger.error(f"创建管理员账号失败: {e}")
        else:
            Logger.info("默认管理员账号已存在")
    
    def init_demo_data(self):
        """初始化演示数据"""
        from utils.crypto import CryptoUtil
        
        # 检查是否已有数据
        result = self.execute_query("SELECT COUNT(*) as count FROM students")
        has_students = result and result[0]['count'] > 0
        
        if has_students:
            Logger.info("数据库已有学生数据，跳过学生数据初始化")
        else:
            Logger.info("开始初始化演示数据...")
        
        # 1. 确保管理员账号存在（无论是否有其他数据）
        self.ensure_admin_exists()
        
        if has_students:
            return  # 如果已有学生数据，只创建管理员后返回
        
        # 2. 添加教师
        teachers = [
            {
                'teacher_id': 'teacher001',
                'name': '张教授',
                'password': CryptoUtil.hash_password('2001234567'),
                'gender': '男',
                'title': '教授',
                'department': '计算机学院',
                'email': 'zhang@bupt.edu.cn',
                'phone': '010-12345678'
            },
            {
                'teacher_id': 'teacher002',
                'name': '李副教授',
                'password': CryptoUtil.hash_password('2019876543'),
                'gender': '女',
                'title': '副教授',
                'department': '计算机学院',
                'email': 'li@bupt.edu.cn',
                'phone': '010-12345679'
            }
        ]
        
        for teacher in teachers:
            try:
                self.insert_data('teachers', teacher)
            except Exception as e:
                Logger.warning(f"教师数据可能已存在: {e}")
        
        # 3. 添加学生
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

