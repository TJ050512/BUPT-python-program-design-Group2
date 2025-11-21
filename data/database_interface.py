"""
数据库接口模块
提供统一的数据库访问接口，对接队友的数据库模块
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

# 确保项目根在模块搜索路径中（当作为脚本直接运行时）
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import Logger
# 尝试从配置读取数据库路径
try:
    from utils.config_manager import Config  # type: ignore
except Exception:
    Config = None  # type: ignore
    
from models import Student, Teacher, Course, CourseOffering, Enrollment, Grade

class _DBAdapter:
    """内部适配器：屏蔽不同数据库实现差异"""
    def __init__(self, db_path: str):
        self._impl = None
        from data.database import Database, get_database  # type: ignore
        # 尝试使用单例 get_database if provided
        try:
            self._impl = get_database()  # type: ignore
            self._mode = 'data.database.single'
        except Exception:
            self._impl = Database(str(db_path)) #
            self._mode = 'data.database'
        Logger.info("DatabaseInterface: 回退使用 data.database")

    # 统一方法名：query 返回 list[dict], execute 返回受影响行数, insert 返回新 id 或 None
    def query(self, sql: str, params: Tuple = None) -> List[Dict]:
        """执行查询语句，返回 List[Dict]"""
        return self._impl.execute_query(sql, params)

    def execute(self, sql: str, params: Tuple = None) -> int:
        """执行更新语句（返回受影响行数）"""
        return self._impl.execute_update(sql, params)

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """插入数据（返回新ID）"""
        return self._impl.insert_data(table, data)

    def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        """更新数据（返回受影响行数）"""
        return self._impl.update_data(table, data, condition)

    def delete(self, table: str, condition: Dict[str, Any]) -> int:
        """删除数据（返回受影响行数）"""
        return self._impl.delete_data(table, condition)

    def close(self):
        try:
            if hasattr(self._impl, 'close'):
                return self._impl.close()
        except Exception:
            pass


class DatabaseInterface:
    """
    数据库接口类
    这个类作为中间层，调用队友提供的数据库模块
    """

    def __init__(self, config: dict = None):
        """初始化数据库接口"""
        self.config = config or {}
        self.db: Optional[_DBAdapter] = None
        self._init_database()

        def _get_academic_year(self, student_grade: int, semester: str) -> int:
            """
            计算当前是大几：
            semester 形如 '2024-2025-1'
            student_grade 为入学年份（如 2022）
            """
            try:
                start_year = int(semester.split("-")[0])
            except Exception:
                return 1
            diff = start_year - int(student_grade)
            year = diff + 1  # 大一=1、大二=2...
            if year < 1:
                year = 1
            if year > 4:
                year = 4
            return year

    def _get_db_path(self) -> str:
        # 获取数据库路径逻辑不变
        db_path = self.config.get('path') or self.config.get('database.path')
        if not db_path and Config:
            try:
                db_path = Config.get('database.path') or Config.get('database.file') or Config.get('database')
            except Exception:
                db_path = None
        if not db_path:
            db_path = 'data/bupt_teaching.db'
        p = Path(db_path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)

    def _init_database(self):
        """初始化数据库连接"""
        try:
            db_path = self._get_db_path()
            self.db = _DBAdapter(db_path)
            Logger.info("数据库接口初始化完成")
        except Exception as e:
            Logger.error(f"数据库初始化失败: {e}", exc_info=True)
            self.db = None

    # ============ 核心方法：通用查询/插入/更新/删除 ============

    def query(self, sql: str, params: Tuple = None) -> List[Dict]:
        """执行原生查询，返回字典列表"""
        if self.db:
            return self.db.query(sql, params)
        return []

    def execute(self, sql: str, params: Tuple = None) -> int:
        """执行原生更新/删除 SQL，返回影响行数"""
        if self.db:
            return self.db.execute(sql, params)
        return 0

    def insert_record(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """插入数据到指定表，返回新ID"""
        if self.db:
            return self.db.insert(table, data)
        return None

    def update_record(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        """更新指定表数据，返回影响行数"""
        if self.db:
            return self.db.update(table, data, condition)
        return 0

    def delete_record(self, table: str, condition: Dict[str, Any]) -> int:
        """删除指定表数据，返回影响行数"""
        if self.db:
            return self.db.delete(table, condition)
        return 0

    # ============ 学生/教师操作 ============
    
    def query_student_by_id(self, student_id: str) -> Optional[Student]:
        """按学号查询学生信息，返回 Student 模型"""
        try:
            sql = "SELECT * FROM students WHERE student_id=? LIMIT 1"
            res = self.db.query(sql, (student_id,))
            return Student.from_dict(res[0]) if res else None #
        except Exception as e:
            Logger.error(f"查询学生失败: {e}", exc_info=True)
            return None

    def insert_student(self, student: Student) -> Optional[int]:
        """插入学生信息"""
        try:
            # Note: 插入时 student.to_dict() 应包含 password 字段，否则数据库会报错
            return self.db.insert('students', student.to_dict()) #
        except Exception as e:
            Logger.error(f"插入学生失败: {e}", exc_info=True)
            return None

    def query_teacher_by_id(self, teacher_id: str) -> Optional[Teacher]:
        """按工号查询教师信息，返回 Teacher 模型"""
        try:
            sql = "SELECT * FROM teachers WHERE teacher_id=? LIMIT 1"
            res = self.db.query(sql, (teacher_id,))
            return Teacher.from_dict(res[0]) if res else None #
        except Exception as e:
            Logger.error(f"查询教师失败: {e}", exc_info=True)
            return None

    # ============ 用户相关操作 ============

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        try:
            sql = "SELECT * FROM users WHERE username=? LIMIT 1"
            res = self.db.query(sql, (username,))
            return res[0] if res else None
        except Exception as e:
            Logger.error(f"查询用户失败: {e}", exc_info=True)
            return None

    def query_user_by_id(self, user_id: int) -> Optional[Dict]:
        try:
            sql = "SELECT * FROM users WHERE id=? LIMIT 1"
            res = self.db.query(sql, (user_id,))
            return res[0] if res else None
        except Exception as e:
            Logger.error(f"查询用户失败: {e}", exc_info=True)
            return None

    def insert_user(self, user_data: Dict) -> int:
        try:
            return self.db.insert('users', user_data)  # 期望返回 id 或 None
        except Exception as e:
            Logger.error(f"插入用户失败: {e}", exc_info=True)
            raise

    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        try:
            affected = self.db.update('users', {'password': new_password_hash}, {'id': user_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"更新密码失败: {e}", exc_info=True)
            return False

    def update_last_login(self, user_id: int) -> bool:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            affected = self.db.update('users', {'last_login': now}, {'id': user_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"更新最后登录时间失败: {e}", exc_info=True)
            return False

    def query_my_enrollments_by_student_id_and_semester(self, student_id: str, semester: Optional[str] = None) -> List[Dict]:
        """
        查询学生在指定学期（或所有学期）已选课程的详细信息，使用 course_offerings 的 class_time 字段（节次文本）。
        """
        sql = """
            SELECT 
                e.enrollment_id, 
                e.semester,
                c.course_id, c.course_name, c.credits, 
                t.name AS teacher_name, 
                o.class_time, -- 🎯 直接读取节次文本字段
                o.classroom,  -- 🎯 直接读取教室字段
                g.score, g.gpa, g.grade_level, g.exam_round
            FROM enrollments e
            JOIN course_offerings o ON e.offering_id = o.offering_id
            JOIN courses c ON o.course_id = c.course_id
            JOIN teachers t ON o.teacher_id = t.teacher_id
            LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
            WHERE e.student_id = ?
        """
        params: List[Any] = [student_id]
        
        # 筛选学期
        # 如果没传 semester，就自动用该学生最新的一个学期
        if not semester:
            sem_rows = self.db.query(
                "SELECT DISTINCT semester FROM enrollments WHERE student_id=? ORDER BY semester DESC LIMIT 1",
                (student_id,)
            )
            if sem_rows:
                semester = sem_rows[0]["semester"]
        if semester:
            sql += " AND e.semester = ?"
            params.append(semester)

        rows = self.db.query(sql, tuple(params)) if self.db else []
        
        results: List[Dict] = []
        for row in rows:
            # 🎯 关键：使用 class_time (节次文本) 作为 schedule_str
            schedule_text = row.get("class_time") 
            if schedule_text:
                 results.append({
                    "enrollment_id": row["enrollment_id"],
                    "semester": row["semester"],
                    "course_id": row["course_id"],
                    "course_name": row["course_name"],
                    "credits": row["credits"],
                    "teacher_name": row["teacher_name"],
                    "schedule_str": schedule_text, # 🎯 包含周X节次的文本
                    "classroom_name": row.get("classroom"), 
                    "score": row.get("score"),
                    "gpa": row.get("gpa"),
                    "grade_level": row.get("grade_level")
                })
        return results

    # ============ 数据记录相关操作 ============

    def query_data_list(self, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        try:
            sql = "SELECT * FROM data_records"
            params: List[Any] = []
            if filters:
                conds = []
                for k, v in filters.items():
                    conds.append(f"{k}=?")
                    params.append(v)
                sql += " WHERE " + " AND ".join(conds)
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            return self.db.query(sql, tuple(params))
        except Exception as e:
            Logger.error(f"查询数据失败: {e}", exc_info=True)
            return []

    def insert_data_record(self, data: Dict) -> int:
        try:
            return self.db.insert('data_records', data)
        except Exception as e:
            Logger.error(f"插入数据记录失败: {e}", exc_info=True)
            raise

    def update_data_record(self, record_id: int, data: Dict) -> bool:
        try:
            affected = self.db.update('data_records', data, {'id': record_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"更新数据失败: {e}", exc_info=True)
            return False

    def delete_data_record(self, record_id: int) -> bool:
        try:
            affected = self.db.delete('data_records', {'id': record_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"删除数据失败: {e}", exc_info=True)
            return False

    # ============ 统计查询 ============

    def get_data_count(self, filters: Dict = None) -> int:
        try:
            sql = "SELECT COUNT(*) as count FROM data_records"
            params: List[Any] = []
            if filters:
                conds = []
                for k, v in filters.items():
                    conds.append(f"{k}=?")
                    params.append(v)
                sql += " WHERE " + " AND ".join(conds)
            res = self.db.query(sql, tuple(params) if params else None)
            if res and isinstance(res, list):
                # 兼容不同实现返回的键名
                first = res[0]
                return int(first.get('count') or first.get('c') or list(first.values())[0])
            return 0
        except Exception as e:
            Logger.error(f"查询数据总数失败: {e}", exc_info=True)
            return 0

    def get_category_statistics(self) -> List[Dict]:
        try:
            sql = "SELECT category, COUNT(*) as count FROM data_records GROUP BY category"
            return self.db.query(sql)
        except Exception as e:
            Logger.error(f"查询分类统计失败: {e}", exc_info=True)
            return []

    # === Colleges / Majors ===
    def upsert_college(self, code: str, name: str) -> int:
        return self.insert_record('colleges', {'college_code': code, 'name': name}) or 0

    def add_major(self, college_code: str, name: str, code: str=None) -> int:
        return self.insert_record('majors', {'college_code': college_code, 'name': name, 'code': code}) or 0

    # === Classrooms / TimeSlots ===
    def add_classroom(self, name: str, location_type: str, seat_count: int, room_type: str) -> int:
        return self.insert_record('classrooms', {
            'name': name, 'location_type': location_type, 'seat_count': seat_count, 'room_type': room_type
        }) or 0

    def add_timeslot(self, day: int, sec: int, start: str, end: str, session: str) -> int:
        return self.insert_record('time_slots', {
            'day_of_week': day, 'section_no': sec, 'starts_at': start, 'ends_at': end, 'session': session
        }) or 0

    # === Program courses ===
    def add_program_course(self, major_id: int, course_id: str, category: str, cross_quota: int=0, grade_rec: int=None) -> int:
        return self.insert_record('program_courses', {
            'major_id': major_id, 'course_id': course_id, 'course_category': category,
            'cross_major_quota': cross_quota, 'grade_recommendation': grade_rec
        }) or 0

    # === Offering sessions ===
    def bind_offering_session(self, offering_id: int, slot_id: int, classroom_id: int) -> int:
        return self.insert_record('offering_sessions', {
            'offering_id': offering_id, 'slot_id': slot_id, 'classroom_id': classroom_id
        }) or 0
        
    # ============ 操作日志 ============

    def log_operation(self, user_id: int, action: str, target: str,
                  details: str = None, ip_address: str = None,
                  device: str = None, os: str = None, browser: str = None):
        try:
            log_data = {
                'user_id': user_id,
                'action': action,
                'target': target,
                'details': details,
                'ip_address': ip_address,
                'device': device,
                'os': os,
                'browser': browser,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.db.insert('system_logs', log_data)
        except Exception as e:
            Logger.error(f"记录操作日志失败: {e}", exc_info=True)

    def close(self):
        """关闭数据库连接"""
        try:
            if self.db:
                self.db.close()
                Logger.info("数据库连接已关闭")
        except Exception as e:
            Logger.error(f"关闭数据库连接失败: {e}", exc_info=True)

    # ============ 课程/开课查询 ============
    def query_offerings_by_semester(self, semester: str, student_id: str=None) -> List[Dict]:
        """
        查询本学期所有【可选】开课班级：
        - 只看传入的 semester
        - 只返回 status='open' 且已排好课（class_time 不为空/未排课）且未满员的课程
        如果提供 student_id，则增加字段：
        - is_enrolled: 该学生是否已选这个班
        - is_required: 该课程是否是该学生在本学年的必修课（根据 program_courses）
        """
        required_course_ids: set[str] = set()

        # 如果传了 student_id：先算出这学期该学生的必修课列表
        if student_id:
            stu_rows = self.db.query(
                "SELECT grade, major_id FROM students WHERE student_id=? LIMIT 1",
                (student_id,)
            )
            if stu_rows:
                grade = int(stu_rows[0].get("grade") or 0)
                major_id = stu_rows[0].get("major_id")
                academic_year = self._get_academic_year(grade, semester)
                if major_id:
                    pc_rows = self.db.query(
                        """
                        SELECT course_id 
                        FROM program_courses
                        WHERE major_id=? 
                          AND course_category='必修'
                          AND (grade_recommendation IS NULL OR grade_recommendation=?)
                        """,
                        (major_id, academic_year)
                    )
                    required_course_ids = {r["course_id"] for r in pc_rows}

        # 主查询：本学期所有“可选”的班级
        sql = """
            SELECT
                o.offering_id,
                o.course_id,
                o.semester,
                o.max_students,
                o.current_students,
                o.status,
                o.class_time,
                o.classroom,
                c.course_name,
                c.credits,
                c.hours,
                c.course_type,
                t.teacher_id,
                t.name AS teacher_name,
                ts.day_of_week,
                ts.starts_at,
                ts.ends_at,
                r.name AS classroom_name,
                -- 是否已选该班
                (SELECT COUNT(*) 
                 FROM enrollments e 
                 WHERE e.student_id = ? 
                   AND e.offering_id = o.offering_id) AS is_enrolled
            FROM course_offerings o
            JOIN courses c ON o.course_id = c.course_id
            JOIN teachers t ON o.teacher_id = t.teacher_id
            LEFT JOIN offering_sessions os ON o.offering_id = os.offering_id
            LEFT JOIN time_slots ts ON os.slot_id = ts.slot_id
            LEFT JOIN classrooms r ON os.classroom_id = r.classroom_id
            WHERE o.semester = ?
              AND o.status = 'open'
              AND o.class_time IS NOT NULL
              AND o.class_time <> '未排课'
              AND o.current_students < o.max_students
            ORDER BY o.course_id, o.teacher_id
        """
        params = (student_id or "", semester)
        rows = self.db.query(sql, params) if self.db else []

        # 聚合：同一 course_id 下多个 offering
        aggregated_courses: Dict[str, Dict] = {}

        for row in rows:
            cid = row["course_id"]

            # 已有的 class_time 是 “周一1-2节, 周三3-4节” 这样的文本，这里主要用于 UI 展示
            teacher_time_str = ""
            if row.get("class_time"):
                teacher_time_str = row["class_time"]
            elif row.get("day_of_week") and row.get("starts_at"):
                # 兜底：如果没有 class_time 字段，临时拼一下（一般用不到）
                day_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五"}
                day = day_map.get(row["day_of_week"], "未知")
                start = row["starts_at"][:-3]
                end = row["ends_at"][:-3]
                classroom = row.get("classroom_name") or "待定"
                teacher_time_str = f"{day}{start}~{end} @ {classroom}"

            offering_detail = {
                "offering_id": row["offering_id"],
                "teacher_id": row["teacher_id"],
                "teacher_name": row["teacher_name"],
                "max_students": row["max_students"],
                "current_students": row["current_students"],
                "class_time": teacher_time_str,
                "classroom_name": row.get("classroom") or row.get("classroom_name"),
                "is_enrolled": row["is_enrolled"] > 0,
            }

            if cid not in aggregated_courses:
                aggregated_courses[cid] = {
                    "course_id": cid,
                    "course_name": row["course_name"],
                    "credits": row["credits"],
                    "course_type": row["course_type"],
                    # 该课程是否为“本学年必修课”
                    "is_required": cid in required_course_ids,
                    "offerings": [offering_detail],
                }
            else:
                aggregated_courses[cid]["offerings"].append(offering_detail)

        # 返回 list
        return list(aggregated_courses.values())


if __name__ == "__main__":
    try:
        db_config = {}
        if Config:
            try:
                Config.load('config/config.yaml')
                db_config['path'] = Config.get('database.path') or Config.get('database.file')
            except Exception:
                pass
        di = DatabaseInterface(db_config)
        user = di.query_user_by_username('admin')
        print(f"查询结果: {user}")
    finally:
        try:
            di.close()
        except Exception:
            pass