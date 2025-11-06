"""
合成数据生成脚本（写入项目 data 目录下的 SQLite 文件）
用法（在项目根目录运行）:
    python -m utils.data_simulator [学生数] [教师数] [数据库文件名可选, 默认 bupt_teaching.db]
或（已支持直接运行）:
    python utils\data_simulator.py [学生数] [教师数] [数据库文件名可选, 默认 bupt_teaching.db]
示例:
    python -m utils.data_simulator 200 10
"""
import sys
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, List, Dict

# 确保项目根在模块搜索路径中（当直接运行脚本时）
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.logger import Logger

# 先尝试兼容队友提供的 database_module.DatabaseManager，其次回退到 data.database.Database
DBAdapter = None
try:
    # 队友对接指南建议的模块位置（项目根）
    from database_module import DatabaseManager  # type: ignore

    class DBAdapter:
        def __init__(self, db_path: str):
            # 假设 DatabaseManager 接受 config dict
            cfg = {'type': 'sqlite', 'path': str(db_path)}
            self._db = DatabaseManager(cfg)

        def insert_data(self, table: str, data: Dict[str, Any]) -> Any:
            if hasattr(self._db, "insert"):
                return self._db.insert(table, data)
            elif hasattr(self._db, "insert_data"):
                return self._db.insert_data(table, data)
            raise AttributeError("DatabaseManager 缺少 insert/insert_data 方法")

        def execute_query(self, sql: str, params: tuple = None) -> List[Dict]:
            if hasattr(self._db, "query"):
                return self._db.query(sql, params)
            elif hasattr(self._db, "execute_query"):
                return self._db.execute_query(sql, params)
            elif hasattr(self._db, "execute"):
                return self._db.execute(sql, params)
            raise AttributeError("DatabaseManager 缺少 query/execute_query/execute 方法")

        def execute_update(self, sql: str, params: tuple = None) -> int:
            if hasattr(self._db, "execute"):
                return self._db.execute(sql, params)
            elif hasattr(self._db, "execute_update"):
                return self._db.execute_update(sql, params)
            raise AttributeError("DatabaseManager 缺少 execute/execute_update 方法")

        def close(self):
            if hasattr(self._db, "close"):
                return self._db.close()

    Logger.info("使用 database_module.DatabaseManager 作为数据库后端")
except Exception:
    try:
        from data.database import Database as NativeDatabase  # type: ignore

        class DBAdapter:
            def __init__(self, db_path: str):
                self._db = NativeDatabase(str(db_path))

            def insert_data(self, table: str, data: Dict[str, Any]) -> Any:
                return self._db.insert_data(table, data)

            def execute_query(self, sql: str, params: tuple = None) -> List[Dict]:
                return self._db.execute_query(sql, params)

            def execute_update(self, sql: str, params: tuple = None) -> int:
                return self._db.execute_update(sql, params)

            def close(self):
                return self._db.close()

        Logger.info("回退使用 data.database.Database 作为数据库后端")
    except Exception as e:
        Logger.error("既无法导入 database_module.DatabaseManager，也无法导入 data.database.Database", exc_info=True)
        raise ImportError("缺少可用的数据库模块") from e

# 尝试获取项目内 CryptoUtil，回退到 bcrypt 或 sha256
try:
    from utils.crypto import CryptoUtil  # type: ignore
except Exception:
    try:
        import bcrypt

        class CryptoUtil:
            @staticmethod
            def hash_password(p: str) -> str:
                return bcrypt.hashpw(p.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except Exception:
        class CryptoUtil:
            @staticmethod
            def hash_password(p: str) -> str:
                Logger.warning("未找到 bcrypt 或 utils.crypto，使用 sha256 作为开发环境替代（非生产）")
                return hashlib.sha256(p.encode('utf-8')).hexdigest()

# 可选 faker，提高姓名等真实性
try:
    from faker import Faker
    faker = Faker("zh_CN")
except Exception:
    faker = None

# data 目录（项目根/data）
data_dir = project_root / "data"
data_dir.mkdir(parents=True, exist_ok=True)


def gen_student_id(year: int, idx: int) -> str:
    return f"{year}{idx:06d}"[:10]


def random_major() -> str:
    majors = ["计算机科学与技术", "软件工程", "通信工程", "信息安全", "人工智能", "电子信息工程"]
    return random.choice(majors)


def ensure_core_tables(db: DBAdapter):
    """根据队友对接指南创建核心表并插入测试用户（admin/user）"""
    Logger.info("检查/创建核心表 users, data_records, operation_logs")
    db.execute_update("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role VARCHAR(20) NOT NULL,
        email VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)
    db.execute_update("""
    CREATE TABLE IF NOT EXISTS data_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(200),
        content TEXT,
        category VARCHAR(50),
        source VARCHAR(100),
        url VARCHAR(500),
        author VARCHAR(100),
        publish_time TIMESTAMP,
        crawl_time TIMESTAMP,
        views INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    db.execute_update("""
    CREATE TABLE IF NOT EXISTS operation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action VARCHAR(50),
        target VARCHAR(100),
        details TEXT,
        ip_address VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """)

    # 插入测试用户（忽略可能的唯一约束错误）
    hashed_admin = CryptoUtil.hash_password("admin123")
    hashed_user = CryptoUtil.hash_password("user123")
    try:
        db.insert_data("users", {"username": "admin", "password": hashed_admin, "role": "admin", "email": "admin@example.com"})
    except Exception:
        pass
    try:
        db.insert_data("users", {"username": "user", "password": hashed_user, "role": "user", "email": "user@example.com"})
    except Exception:
        pass
    Logger.info("核心表和测试用户检查/创建完成")


# ---------- 以下为合成数据生成逻辑（使用 DBAdapter 作为抽象后端） ----------
def create_teachers(db: DBAdapter, n: int = 10):
    for i in range(1, n + 1):
        tid = f"teacher{i:03d}"
        rec = {
            "teacher_id": tid,
            "name": faker.name() if faker else f"教师{i:03d}",
            "password": CryptoUtil.hash_password("teacher123"),
            "gender": random.choice(["男", "女"]),
            "title": random.choice(["教授", "副教授", "讲师"]),
            "department": "计算机学院",
            "email": f"{tid}@bupt.edu.cn",
            "phone": f"010-{random.randint(10000000, 99999999)}"
        }
        try:
            db.insert_data("teachers", rec)
        except Exception:
            pass


def create_students(db: DBAdapter, count: int = 200, year: int = 2021):
    for i in range(1, count + 1):
        sid = gen_student_id(year, i)
        birth = (datetime.now() - timedelta(days=random.randint(18 * 365, 24 * 365))).strftime("%Y-%m-%d")
        rec = {
            "student_id": sid,
            "name": faker.name() if faker else f"学生{i:03d}",
            "password": CryptoUtil.hash_password("student123"),
            "gender": random.choice(["男", "女"]),
            "birth_date": birth,
            "major": random_major(),
            "grade": year,
            "class_name": f"{year}{random.randint(1, 4)}",
            "enrollment_date": f"{year}-09-01",
            "email": f"{sid}@bupt.edu.cn",
            "phone": f"1{random.randint(3000000000, 9999999999)}"[:11]
        }
        try:
            db.insert_data("students", rec)
        except Exception:
            pass


def create_courses(db: DBAdapter):
    courses = [
        {"course_id": "CS101", "course_name": "Python程序设计", "credits": 3.0, "hours": 48, "course_type": "必修",
         "department": "计算机学院", "description": "Python语言基础与应用", "max_students": 60},
        {"course_id": "CS102", "course_name": "数据结构", "credits": 4.0, "hours": 64, "course_type": "必修",
         "department": "计算机学院", "description": "数据结构与算法", "max_students": 60},
        {"course_id": "CS201", "course_name": "数据库原理", "credits": 3.0, "hours": 48, "course_type": "必修",
         "department": "计算机学院", "description": "数据库系统原理与应用", "max_students": 60},
        {"course_id": "CS301", "course_name": "机器学习", "credits": 3.0, "hours": 48, "course_type": "选修",
         "department": "计算机学院", "description": "机器学习基础与应用", "max_students": 60},
    ]
    for c in courses:
        try:
            db.insert_data("courses", c)
        except Exception:
            pass


def create_offerings(db: DBAdapter, semester: str = "2024-2025-2"):
    teachers = db.execute_query("SELECT teacher_id FROM teachers")
    teacher_ids = [t["teacher_id"] for t in teachers] if teachers else ["teacher001"]
    courses = db.execute_query("SELECT course_id FROM courses")
    course_ids = [c["course_id"] for c in courses] if courses else []
    times = ["周一1-2节", "周二3-4节", "周三1-2节", "周四3-4节", "周五1-2节"]
    rooms = [f"教三{num}" for num in range(201, 211)]
    for cid in course_ids:
        rec = {
            "course_id": cid,
            "teacher_id": random.choice(teacher_ids),
            "semester": semester,
            "class_time": random.choice(times),
            "classroom": random.choice(rooms),
            "max_students": random.choice([30, 40, 50, 60]),
            "current_students": 0
        }
        try:
            db.insert_data("course_offerings", rec)
        except Exception:
            pass


def enroll_students(db: DBAdapter, semester: str = "2024-2025-2", max_per_offering: int = 50):
    students = db.execute_query("SELECT student_id FROM students")
    sids = [s["student_id"] for s in students] if students else []
    offerings = db.execute_query("SELECT offering_id, max_students FROM course_offerings WHERE semester=?", (semester,))
    for off in offerings:
        off_id = off["offering_id"]
        cap = off.get("max_students", 60)
        enroll_num = min(cap, random.randint(5, max_per_offering))
        if not sids:
            break
        chosen = random.sample(sids, min(enroll_num, len(sids)))
        for sid in chosen:
            try:
                db.insert_data("enrollments", {"student_id": sid, "offering_id": off_id, "semester": semester})
            except Exception:
                pass
        try:
            db.execute_update("UPDATE course_offerings SET current_students = (SELECT COUNT(*) FROM enrollments WHERE offering_id=?) WHERE offering_id=?", (off_id, off_id))
        except Exception:
            pass


def assign_grades(db: DBAdapter):
    enrolls = db.execute_query("SELECT enrollment_id, student_id, offering_id FROM enrollments")
    for e in enrolls:
        score = round(random.uniform(50, 100), 1)
        if score >= 90:
            level, gpa = "A", 4.0
        elif score >= 80:
            level, gpa = "B", 3.0
        elif score >= 70:
            level, gpa = "C", 2.0
        elif score >= 60:
            level, gpa = "D", 1.0
        else:
            level, gpa = "F", 0.0
        try:
            db.insert_data("grades", {
                "enrollment_id": e["enrollment_id"],
                "student_id": e["student_id"],
                "offering_id": e["offering_id"],
                "score": score,
                "grade_level": level,
                "gpa": gpa,
                "input_by": random.choice([None, "teacher001"])
            })
        except Exception:
            pass


def seed_all(db: DBAdapter, students: int = 200, teachers: int = 10, semester: str = "2024-2025-2"):
    try:
        existing = db.execute_query("SELECT COUNT(*) as c FROM students")
        if existing and existing[0].get("c", 0) > 0:
            Logger.info("检测到已有学生数据，若需重新生成请先清空表或删除数据库文件。")
            return
    except Exception:
        # 表不存在或查询失败时继续执行（init_tables 通常会在 Database 初始化时完成）
        pass

    create_teachers(db, teachers)
    create_students(db, students)
    create_courses(db)
    create_offerings(db, semester)
    enroll_students(db, semester)
    assign_grades(db)
    Logger.info("合成数据生成完成。")


def main():
    students = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    teachers = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    db_file = sys.argv[3] if len(sys.argv) > 3 else "bupt_teaching.db"
    semester = sys.argv[4] if len(sys.argv) > 4 else "2024-2025-2"
    db_path = data_dir / db_file

    db = DBAdapter(str(db_path))
    try:
        ensure_core_tables(db)
        seed_all(db, students=students, teachers=teachers, semester=semester)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()