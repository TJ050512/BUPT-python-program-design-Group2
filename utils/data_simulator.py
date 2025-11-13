"""
合成数据生成脚本（写入项目 data 目录下的 SQLite 文件）
用法:
    python -m utils.data_simulator <command> [students] [teachers] [dbfile] [semester]
    command: seed（仅生成 db 数据）, export（仅导出 CSV）, import（仅从 data/*.csv 导入）, all（seed->export->import）
    >> python -m utils.data_simulator all 3000 200 bupt_teaching.db 2024-2025-2
"""
import sys
import os
import csv
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, List, Dict
from faker import Faker
faker = Faker("zh_CN")
import numpy as np
import pandas as pd
from data.database import Database

# 确保项目根在模块搜索路径中（当直接运行脚本时）
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from utils.logger import Logger

# 使用 data.database.Database
DBAdapter = None
from data.database import Database as NativeDatabase  # type: ignore

# ===== 学院 → 专业池（示例贴近 BUPT，可根据官方专业目录再增减）=====
COLLEGE_CATALOG = [
    # (college_code, college_name, [majors...])
    ("2021001", "计算机学院", [
        "计算机科学与技术", "软件工程", "数据科学与大数据技术"
    ]),
    ("2021002", "信息与通信工程学院", [
        "信息工程", "通信工程", "空间信息与数字技术"
    ]),
    ("2021003", "网络空间安全学院", [
        "网络空间安全", "信息安全", "密码科学与技术"
    ]),
    ("2021004", "电子工程学院", [
        "电子信息工程", "电子科学与技术", "光电信息科学与工程"
    ]),
    ("2021005", "现代邮政学院", [
        "物流工程", "邮政管理"
    ]),
    ("2021006", "人工智能学院", [
        "人工智能", "生物医学工程", "自动化"
    ]),
    ("2021007", "国际学院", [
        "电子信息工程（国际）", "计算机科学与技术（国际）", "电信工程及管理（国际）", "智能科学与技术（国际）"
    ]),
]

def build_course_pool() -> Dict[str, Dict[str, Any]]:
    """
    构建一个较大规模的课程池（约 150~200 门），
    覆盖：公共基础课 / 通识选修 / 信息类基础 / 各学院专业课。
    """
    pool: Dict[str, Dict[str, Any]] = {}

    # 一个小工具，减少重复写字段
    def add(cid, name, credits, hours, ctype, dept, is_public=0):
        pool[cid] = {
            "name": name,
            "credits": credits,
            "hours": hours,
            "type": ctype,
            "dept": dept,
            "is_public": is_public,
        }

    # === 一、公共基础课（公共必修） ===
    # 数学
    add("MA101", "高等数学A(上)",       4.0, 64, "公共必修", "理学院")
    add("MA102", "高等数学A(下)",       4.0, 64, "公共必修", "理学院")
    add("MA201", "线性代数",           3.0, 48, "公共必修", "理学院")
    add("MA202", "概率论与数理统计",   3.0, 48, "公共必修", "理学院")

    # 物理
    add("PH101", "大学物理A(上)",      3.5, 56, "公共必修", "理学院")
    add("PH102", "大学物理A(下)",      3.5, 56, "公共必修", "理学院")

    # 英语（1~4）
    add("EN101", "大学英语1",          3.0, 48, "公共必修", "外语学院")
    add("EN102", "大学英语2",          3.0, 48, "公共必修", "外语学院")
    add("EN103", "大学英语3",          2.0, 32, "公共必修", "外语学院")
    add("EN104", "大学英语4",          2.0, 32, "公共必修", "外语学院")

    # 体育（1~4）
    add("PE101", "大学体育1",          1.0, 32, "公共必修", "体育部")
    add("PE102", "大学体育2",          1.0, 32, "公共必修", "体育部")
    add("PE103", "大学体育3",          0.5, 16, "公共必修", "体育部")
    add("PE104", "大学体育4",          0.5, 16, "公共必修", "体育部")

    # 思政 & 其他通识必修
    add("HX101", "中国近现代史纲要",   2.0, 32, "公共必修", "马克思主义学院")
    add("ZX101", "思想道德与法治",     3.0, 48, "公共必修", "马克思主义学院")
    add("ZX102", "马克思主义基本原理", 3.0, 48, "公共必修", "马克思主义学院")
    add("ZX103", "毛泽东思想和中国特色社会主义理论体系概论", 4.0, 64, "公共必修", "马克思主义学院")
    add("ML101", "军事理论",           2.0, 32, "公共必修", "军训教研部")
    add("XL101", "大学生心理健康教育", 2.0, 32, "公共必修", "学生工作部")
    add("YW101", "大学语文",           2.0, 32, "公共必修", "人文学院")

    # === 二、通识选修（全校公选，is_public=1） ===
    general_electives = [
        ("GE101", "艺术欣赏"),
        ("GE102", "经济学原理"),
        ("GE103", "摄影基础"),
        ("GE104", "影视鉴赏"),
        ("GE105", "管理学基础"),
        ("GE106", "心理学导论"),
        ("GE107", "统计学基础"),
        ("GE108", "哲学与人生"),
        ("GE109", "逻辑思维训练"),
        ("GE110", "创新创业基础"),
        ("GE111", "书法艺术"),
        ("GE112", "音乐鉴赏"),
        ("GE113", "世界文明史"),
        ("GE114", "环境与可持续发展"),
        ("GE115", "法律基础与法治思维"),
        ("GE116", "公共演讲与表达"),
        ("GE117", "职业生涯规划"),
        ("GE118", "项目管理基础"),
        ("GE119", "城市与社会发展"),
        ("GE120", "人工智能与社会"),
    ]
    for cid, name in general_electives:
        add(cid, name, 2.0, 32, "通识选修", "人文学院", is_public=1)

    # === 三、通用信息类基础课（多学院共用） ===
    add("CM201", "C语言程序设计",         3.0, 48, "学科基础", "计算机学院")
    add("CM202", "C++程序设计基础",       3.0, 48, "学科基础", "计算机学院")
    add("CM203", "Python程序设计基础",    2.0, 32, "学科基础", "计算机学院")
    add("CM204", "数据结构与算法设计",   4.0, 64, "学科基础", "计算机学院")
    add("CM205", "离散数学",             3.0, 48, "学科基础", "计算机学院")
    add("CM206", "计算机组成原理",       3.0, 48, "学科基础", "计算机学院")
    add("CM207", "操作系统原理",         3.0, 48, "学科基础", "计算机学院")
    add("CM208", "数据库系统基础",       3.0, 48, "学科基础", "计算机学院")
    add("CM209", "计算机网络基础",       3.5, 56, "学科基础", "计算机学院")
    add("CM210", "软件工程导论",         2.0, 32, "学科基础", "计算机学院")

    # === 四、计算机学院专业课 ===
    add("CS301", "数据库系统原理",     3.0, 48, "专业必修", "计算机学院")
    add("CS302", "操作系统",           4.0, 64, "专业必修", "计算机学院")
    add("CS303", "编译原理",           3.0, 48, "专业必修", "计算机学院")
    add("CS304", "计算机体系结构",     3.0, 48, "专业必修", "计算机学院")
    add("CS305", "软件测试与质量保证", 2.0, 32, "专业选修", "计算机学院")
    add("CS306", "Web应用开发",        2.0, 32, "专业选修", "计算机学院")
    add("CS307", "移动互联网开发",     2.0, 32, "专业选修", "计算机学院")
    add("CS401", "人工智能基础",       3.0, 48, "专业选修", "计算机学院")
    add("CS402", "大数据处理技术",     3.0, 48, "专业选修", "计算机学院")
    add("CS403", "云计算与虚拟化",     2.0, 32, "专业选修", "计算机学院")
    add("SE401", "软件工程实践",       3.0, 48, "专业必修", "计算机学院")
    add("SE402", "需求工程",           2.0, 32, "专业必修", "计算机学院")
    add("SE403", "软件项目管理",       2.0, 32, "专业选修", "计算机学院")

    # === 五、信息与通信工程学院 ===
    add("TC201", "电路分析基础",       4.0, 64, "学科基础", "信息与通信工程学院")
    add("TC202", "模拟电子技术基础",   4.0, 64, "学科基础", "信息与通信工程学院")
    add("TC203", "数字电子技术基础",   4.0, 64, "学科基础", "信息与通信工程学院")
    add("TC301", "信号与系统",         4.0, 64, "专业必修", "信息与通信工程学院")
    add("TC302", "通信原理",           4.0, 64, "专业必修", "信息与通信工程学院")
    add("TC303", "信息论与编码",       3.0, 48, "专业必修", "信息与通信工程学院")
    add("TC401", "移动通信原理",       3.0, 48, "专业必修", "信息与通信工程学院")
    add("TC402", "数字通信系统",       3.0, 48, "专业选修", "信息与通信工程学院")
    add("TC403", "光纤通信技术",       2.0, 32, "专业选修", "信息与通信工程学院")

    # === 六、网络空间安全学院 ===
    add("SC201", "密码学基础",         3.0, 48, "学科基础", "网络空间安全学院")
    add("SC202", "安全数学基础",       3.0, 48, "学科基础", "网络空间安全学院")
    add("SC301", "网络安全技术",       3.0, 48, "专业必修", "网络空间安全学院")
    add("SC302", "操作系统安全",       2.0, 32, "专业选修", "网络空间安全学院")
    add("SC303", "Web安全",            2.0, 32, "专业选修", "网络空间安全学院")
    add("SC304", "恶意代码分析",       2.0, 32, "专业选修", "网络空间安全学院")
    add("SC401", "密码学",             3.0, 48, "专业必修", "网络空间安全学院")
    add("SC402", "安全攻防实践",       3.0, 48, "专业选修", "网络空间安全学院")

    # === 七、电子工程学院 ===
    add("EE201", "电路原理",           4.0, 64, "学科基础", "电子工程学院")
    add("EE202", "模拟电子技术",       4.0, 64, "学科基础", "电子工程学院")
    add("EE203", "数字电子技术",       4.0, 64, "学科基础", "电子工程学院")
    add("EE301", "电磁场与电磁波",     4.0, 64, "专业必修", "电子工程学院")
    add("EE302", "数字信号处理",       3.0, 48, "专业必修", "电子工程学院")
    add("EE303", "单片机原理与接口技术", 3.0, 48, "专业必修", "电子工程学院")
    add("EE304", "嵌入式系统设计",     3.0, 48, "专业选修", "电子工程学院")
    add("EE401", "射频电路设计",       3.0, 48, "专业选修", "电子工程学院")
    add("EE402", "集成电路设计基础",   3.0, 48, "专业选修", "电子工程学院")

    # === 八、现代邮政学院 ===
    add("MP201", "管理学原理",         3.0, 48, "学科基础", "现代邮政学院")
    add("MP202", "运筹学基础",         3.0, 48, "学科基础", "现代邮政学院")
    add("MP301", "现代物流学",         3.0, 48, "专业必修", "现代邮政学院")
    add("MP302", "供应链管理",         3.0, 48, "专业必修", "现代邮政学院")
    add("MP303", "电子商务概论",       2.0, 32, "专业选修", "现代邮政学院")
    add("MP401", "快递服务管理",       3.0, 48, "专业选修", "现代邮政学院")
    add("MP402", "物流系统规划与设计", 3.0, 48, "专业选修", "现代邮政学院")

    # === 九、人工智能学院 ===
    add("AI201", "人工智能导论",       2.0, 32, "学科基础", "人工智能学院")
    add("AI202", "概率图模型基础",     2.0, 32, "学科基础", "人工智能学院")
    add("AI301", "机器学习",           3.0, 48, "专业必修", "人工智能学院")
    add("AI302", "深度学习",           3.0, 48, "专业必修", "人工智能学院")
    add("AI303", "计算机视觉",         3.0, 48, "专业选修", "人工智能学院")
    add("AI304", "自然语言处理",       3.0, 48, "专业选修", "人工智能学院")
    add("AI401", "模式识别",           3.0, 48, "专业必修", "人工智能学院")
    add("AI402", "强化学习",           3.0, 48, "专业选修", "人工智能学院")

    # === 十、国际学院（示例用信息类 & 英语强化） ===
    add("IC201", "学术英语写作",       3.0, 48, "学科基础", "国际学院")
    add("IC202", "产品开发与项目管理",         2.0, 32, "学科基础", "国际学院")
    add("IC301", "人工智能法律",   2.0, 32, "专业选修", "国际学院")

    return pool


# 用新的构造函数替换原来的 COURSE_POOL
COURSE_POOL: Dict[str, Dict[str, Any]] = build_course_pool()


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

Logger.info("使用 data.database.Database 作为数据库后端（已移除兼容导入）")
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


# data 目录（项目根/data）
data_dir = project_root / "data"
data_dir.mkdir(parents=True, exist_ok=True)


def gen_student_id(year: int, idx: int) -> str:
    return f"{year}{idx:06d}"[:10]


def random_major() -> str:
    majors = ["计算机科学与技术", "软件工程", "通信工程", "信息安全", "人工智能", "电子信息工程"]
    return random.choice(majors)


def ensure_core_tables(db):
    """兼容旧调用：统一调用 Database.init_tables()"""
    try:
        if hasattr(db, "_impl") and hasattr(db._impl, "init_tables"):
            db._impl.init_tables()
        elif hasattr(db, "init_tables"):
            db.init_tables()
        else:
            # 最后兜底：自己新建一个数据库实例建表
            Database("data/bupt_teaching.db").init_tables()
        Logger.info("✅ 表结构初始化完成（由 Database.init_tables() 统一创建）")
    except Exception as e:
        Logger.error(f"表结构初始化失败: {e}", exc_info=True)


# ---------- 以下为合成数据生成逻辑（使用 DBAdapter 作为抽象后端） ----------
def create_teachers(db: DBAdapter, n: int = 10):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 学院池（可继续扩展）
    departments = [
        "国际学院", "计算机学院", "现代邮政学院", "电子工程学院",
        "人工智能学院", "信息与通信工程学院", "未来学院", "人文学院"
    ]

    # 职称、岗位类型、职级映射（保留你之前的增强）
    title_weights = {
        "教授": 5, "副教授": 10, "讲师": 40, "助教": 10,
        "研究员": 5, "副研究员": 8, "助理研究员": 10,
        "实验师": 5, "高级实验师": 5,
        "辅导员": 2, "教学秘书": 2, "教务员": 2, "行政主管": 3
    }
    job_type_map = {
        "教授": "教学科研岗", "副教授": "教学科研岗", "讲师": "教学科研岗", "助教": "教学科研岗",
        "研究员": "科研岗", "副研究员": "科研岗", "助理研究员": "科研岗",
        "实验师": "实验技术岗", "高级实验师": "实验技术岗",
        "辅导员": "学生管理岗", "教学秘书": "教务管理岗", "教务员": "教务管理岗", "行政主管": "行政管理岗"
    }
    hire_level_map = {
        "教授": "正高级", "副教授": "副高级", "讲师": "中级", "助教": "初级",
        "研究员": "正高级", "副研究员": "副高级", "助理研究员": "中级",
        "实验师": "中级", "高级实验师": "副高级",
        "辅导员": "中级", "教学秘书": "中级", "教务员": "中级", "行政主管": "副高级"
    }

    faker_en = Faker("en_US")

    for i in range(1, n + 1):
        # 1) 先决定 hire_year，再映射工号前缀
        hire_year = random.choice(list(range(2005, 2022)))  # 可调年份范围
        if 2000 <= hire_year <= 2009:
            prefix = "200"      # 200???????
            serial_width = 7
        elif 2010 <= hire_year <= 2019:
            prefix = "201"      # 201???????
            serial_width = 7
        else:  # 2020~2021
            prefix = "2021"     # 2021??????
            serial_width = 6

        # 2) 按前缀+随机序列，生成 10 位合法教职工工号
        dept = random.choice(departments)
        c_idx = departments.index(dept) + 1
        m_idx = random.randint(1, 3) 
        college_code = f"{c_idx:02d}{m_idx}" 
        tid = _gen_teacher_id(hire_year, college_code, i)

        # 3) 学院处理
        is_international = (dept == "国际学院")
        title = random.choices(list(title_weights.keys()), weights=list(title_weights.values()), k=1)[0]
        name_zh = faker.name() if 'faker' in globals() and faker else f"教师{i:03d}"
        name_en = (faker_en.name() if faker_en else f"Prof.{i:03d}")
        display_name = name_en if is_international else name_zh
        email_domain = "ic.bupt.edu.cn" if is_international else "bupt.edu.cn"

        rec = {
            "teacher_id": tid,
            "name": display_name,
            "password": CryptoUtil.hash_password("teacher123"),
            "gender": random.choice(["男", "女"]),
            "title": title,
            "job_type": job_type_map.get(title),
            "hire_level": hire_level_map.get(title),
            "department": dept,
            "email": f"{tid}@{email_domain}",
            "phone": f"010-{random.randint(10000000, 99999999)}",
            "hire_date": f"{hire_year}-09-01",
            "status": "active",
            "created_at": now,
            "updated_at": now
        }
        try:
            db.insert_data("teachers", rec)
        except Exception:
            pass


def _gen_student_id(grade_year: int, college_code: str, seq_in_major: int) -> str:
    """
    生成学号: xxxxyyyzzz
    xxxx=入学年份；yyy=学院+专业序号；zzz=学生序号
    """
    return f"{grade_year}{college_code}{seq_in_major:03d}"

def _gen_teacher_id(hire_year: int, college_code: str, seq: int) -> str:
    """工号=xxxxyyyzzz；xxxx=入职年份；yyy=学院(前两位)+专业(第3位)；zzz=院内/处室/专业序号"""
    return f"{hire_year}{college_code}{seq:03d}"

def _gen_class_name(grade_year: int, college_serial: int, class_serial: int) -> str:
    """
    班级号：xxxxyyyzzz
    xxxx=年级；yyy=学院序号；zzz=班级序号
    """
    return f"{grade_year}{college_serial:03d}{class_serial:03d}"

def _college_serial_from_code(college_code: str) -> int:
    """从 202mxxx 提取学院序号 xxx -> int"""
    return int(college_code[-3:])

def create_students(db: DBAdapter, total_count: int = 4000):
    """
    生成 2022~2025 四届学生；不同学院用自身专业池；学号/班级号按规范生成。
    total_count 将大致平均分到（年级 × 学院）。
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    grade_years = [2022, 2023, 2024, 2025]

    # 每届每院大约多少人
    per_college_per_grade = max(1, total_count // (len(COLLEGE_CATALOG) * len(grade_years)))

    # 出生年分布（示例）
    min_birth, max_birth = 2001, 2006
    mu, sigma = 2003.0, 1.2

    for grade in grade_years:
        for c_idx, (college_code, college_name, major_pool) in enumerate(COLLEGE_CATALOG, start=1):
            # c_idx: 学院序号（1..N）
            # 为每个学院至少两个专业：我们按专业循环，确保第3位是“专业序号”
            for m_idx, major_name in enumerate(major_pool, start=1):
                # 3位 yyy = 前两位学院序号 + 第三位专业序号
                college_code = f"{c_idx:02d}{m_idx}"  # e.g. 学院01 专业1 => "011"
                # 每专业分配若干名学生
                # 学院内学生累计序号，用于 yyy
                for seq in range(1, per_college_per_grade + 1):
                    # 学号
                    sid = _gen_student_id(grade, college_code, seq)
                    # 班级号（每10人一个班：001,002,... 可按需调整）
                    class_serial = (seq - 1) // 10 + 1
                    class_name = _gen_class_name(grade, c_idx, class_serial)
                    # 专业从“本学院专业池”抽
                    major = random.choice(major_pool)

                    # 随机生日
                    birth_year = int(max(min_birth, min(max_birth, round(np.random.normal(mu, sigma)))))
                    start = datetime(birth_year, 1, 1)
                    birth_date = (start + timedelta(days=random.randint(0, 364))).strftime("%Y-%m-%d")

                    rec = {
                        "student_id": sid,
                        "name": faker.name() if 'faker' in globals() and faker else f"学生{sid[-4:]}",
                        "password": CryptoUtil.hash_password("student123"),
                        "gender": random.choice(["男", "女"]),
                        "birth_date": birth_date,
                        "major": major,                      # 专业=文本字段（保留）
                        "grade": grade,                      # 年级=2022~2025
                        "class_name": class_name,            # 班级号=xxxx yyy zzz
                        "college_code": college_code,        # 学院码=202mxxx（与学号前7位一致）
                        "enrollment_date": f"{grade}-09-01",
                        "batch_no": grade - 2020,
                        "status": "active",
                        "email": f"{sid}@bupt.edu.cn",
                        "phone": str(random.randint(13000000000, 19999999999))[:11],
                        "created_at": now,
                        "updated_at": now
                    }
                    try:
                        db.insert_data("students", rec)
                    except Exception as e:
                        Logger.warning(f"插入学生失败 {sid}: {e}")


def create_courses(db: DBAdapter):
    """扩充课程库，覆盖更多专业和类型"""
    
    global COURSE_POOL
    courses_to_insert = []
    
    for course_id, data in COURSE_POOL.items():
        course_data = {
            "course_id": course_id,
            "course_name": data["name"],
            "credits": data["credits"],
            "hours": data["hours"],
            "course_type": data["type"],
            "department": data["dept"],
            "description": f"本科生{data['dept']}课程：{data['name']}",
            "prerequisite": None,
            "max_students": random.choice([60, 80, 100, 120]),
            "is_public_elective": data.get("is_public", 0),
            "credit_type": "学位课" if data["type"] == "专业必修" else "任选课",
        }
        courses_to_insert.append(course_data)

    inserted_count = 0
    for c in courses_to_insert:
        try:
            # 使用 INSERT OR IGNORE 确保重复运行时不失败
            db.execute_update(
                "INSERT OR IGNORE INTO courses(course_id, course_name, credits, hours, course_type, department, description, max_students, is_public_elective, credit_type) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (c['course_id'], c['course_name'], c['credits'], c['hours'], c['course_type'], c['department'], c['description'], c['max_students'], c['is_public_elective'], c['credit_type'])
            )
            inserted_count += 1
        except Exception:
            pass # 忽略已存在的课程插入失败

    Logger.info(f"课程库创建/更新完成，共 {len(COURSE_POOL)} 门课程。")



def assign_tas_for_offering(db: DBAdapter, offering_id: int, teacher_id: str, course_id: str):
    """
    自动为课程分配 2 名助教：
    - 同学院优先
    - 若是国际学院老师，则从 计算机学院 + AI学院 分配
    """
    # 1. 找出教师的学院
    teacher_row = db.execute_query(
        "SELECT department FROM teachers WHERE teacher_id=?",
        (teacher_id,)
    )
    if not teacher_row:
        return
    dept = teacher_row[0]["department"]

    # 2. 国际学院：助教从 计算机学院 + 人工智能学院
    if dept == "国际学院":
        ta_candidates = db.execute_query(
            "SELECT teacher_id FROM teachers WHERE department IN ('计算机学院','人工智能学院') AND job_type IN ('教学科研岗','科研岗','助教')"
        )
    else:
        # 普通学院：助教从同学院选
        ta_candidates = db.execute_query(
            "SELECT teacher_id FROM teachers WHERE department=? AND job_type IN ('教学科研岗','科研岗','助教')",
            (dept,)
        )

    if len(ta_candidates) < 2:
        return

    ta_ids = random.sample(ta_candidates, 2)

    # 3. 写入到 teacher_course_rel（你的 models 里已经设计了这个表）
    for t in ta_ids:
        try:
            db.insert_data("teacher_major_course", {
                "teacher_id": t["teacher_id"],
                "course_id": course_id,
                "role": "助教"         # 角色字段
            })
        except:
            pass


def create_offerings(db: DBAdapter, semester: str = "2024-2025-2"):
    """改进开课逻辑，使用 offering_sessions 关联时间和教室"""
    teachers = db.execute_query("SELECT teacher_id FROM teachers")
    teaching_teachers = db.execute_query(
        "SELECT teacher_id FROM teachers WHERE job_type IN ('教学科研岗', '科研岗')"
    )
    teacher_ids = [t["teacher_id"] for t in teaching_teachers] if teaching_teachers else []

    
    courses = db.execute_query("SELECT course_id, is_public_elective, department FROM courses")
    if not courses:
        return

    # 获取所有可用的时间段和教室
    time_slots = db.execute_query("SELECT slot_id, session FROM time_slots")
    classrooms = db.execute_query("SELECT classroom_id FROM classrooms")
    
    if not time_slots or not classrooms:
        Logger.error("无法创建开课计划，因为时间段或教室数据为空。")
        return

    # 将时间段按 AM/PM/EVENING 分类
    slots_by_session = {"AM": [], "PM": [], "EVENING": []}
    for slot in time_slots:
        if slot['session'] in slots_by_session:
            slots_by_session[slot['session']].append(slot['slot_id'])

    for course in courses:
        # 1. 创建 course_offerings 记录
        dept = course["department"]
        teachers = db.execute_query(
            "SELECT teacher_id FROM teachers WHERE department=?", (dept,)
        )
        if not teachers:
            continue
        teacher_id = random.choice(teachers)["teacher_id"]
        offering_data = {
            "course_id": course["course_id"],
            "teacher_id": teacher_id,
            "semester": semester,
            "max_students": random.choice([40, 60, 120]),
            "status": "open"
        }
        # 这里不再写入 class_time 和 classroom 文本
        offering_id = db.insert_data("course_offerings", offering_data)

        if not offering_id:
            continue

        assign_tas_for_offering(db, offering_id, teacher_id, course["course_id"])

        # 2. 为开课计划安排具体的时间和教室，并插入到 offering_sessions
        try:
            # 根据课程类型选择时间段
            if course["is_public_elective"] == 1:
                # 公选课，只在晚上安排
                available_slots = slots_by_session["EVENING"]
            else:
                # 普通课程，在上午或下午安排
                available_slots = slots_by_session["AM"] + slots_by_session["PM"]
            
            if not available_slots:
                continue

            # 随机选择一个时间段ID和一个教室ID
            slot_id_to_assign = random.choice(available_slots)
            classroom_id_to_assign = random.choice(classrooms)["classroom_id"]

            # 插入到关联表
            db.insert_data("offering_sessions", {
                "offering_id": offering_id,
                "slot_id": slot_id_to_assign,
                "classroom_id": classroom_id_to_assign
            })
        except Exception as e:
            Logger.warning(f"为课程 {course['course_id']} (Offering ID: {offering_id}) 安排时间教室失败: {e}")

    Logger.info("开课计划（course_offerings & offering_sessions）生成完成。")


def _get_academic_year(student_grade: int, semester: str) -> int:
    """
    根据入学年份 + 学期(如 '2025-2026-1') 推导学生当前是大几：
    例如：semester='2025-2026-1'
        2025级 -> 大一
        2024级 -> 大二
        2023级 -> 大三
        2022级 -> 大四
    """
    try:
        start_year = int(semester.split("-")[0])
    except Exception:
        # 兜底：解析失败默认按入学年份算大一
        return 1

    diff = start_year - student_grade
    # 大一=1，大二=2，大三=3，大四=4
    year = diff + 1
    if year < 1:
        year = 1
    if year > 4:
        year = 4
    return year


def enroll_students(db: DBAdapter, semester: str = "2024-2025-2", max_public_electives_per_student: int = 2):
    """
    新版选课逻辑：
    - 每个学生只从【本专业必修 + 公共基础课 + 公选课】中选
    - 公共基础课只在大一学年修读（基于 _get_academic_year 计算）
    - 每个学生的公选课数量限制为 max_public_electives_per_student（默认最多 2 门）
    """

    # 1. 预取学生、专业、课程、开课信息
    students = db.execute_query("SELECT student_id, grade, major FROM students")
    if not students:
        Logger.warning("没有学生数据，跳过选课")
        return

    majors = db.execute_query("SELECT major_id, name, college_code FROM majors")
    if not majors:
        Logger.warning("没有专业数据，跳过选课")
        return

    # 专业名 -> major_id 映射
    major_name_to_id = {m["name"]: m["major_id"] for m in majors}

    # 课程开课（本学期）
    offerings = db.execute_query(
        "SELECT offering_id, course_id, max_students, "
        "COALESCE(current_students, 0) AS current_students "
        "FROM course_offerings WHERE semester=?",
        (semester,)
    )
    if not offerings:
        Logger.warning("没有开课记录，跳过选课")
        return

    # course_id -> 该课程所有开课实例列表
    offerings_by_course: Dict[str, List[Dict]] = {}
    for o in offerings:
        offerings_by_course.setdefault(o["course_id"], []).append(o)

    # 在内存里维护每个 offering 的当前人数，避免频繁查询数据库
    offering_current_counts: Dict[int, int] = {}
    for o in offerings:
        offering_current_counts[o["offering_id"]] = int(o.get("current_students", 0))

    # 辅助函数：给某个课程挑一个有余量的开课实例
    def pick_offering_for_course(cid: str) -> Optional[int]:
        offs = offerings_by_course.get(cid, [])
        random.shuffle(offs)
        for o in offs:
            oid = o["offering_id"]
            cap = o.get("max_students") or 60
            cur = offering_current_counts.get(oid, 0)
            if cur < cap:
                return oid
        return None

    # 为提高效率，预取 program_courses + 课程类型信息
    program_rows = db.execute_query(
        "SELECT pc.major_id, pc.course_id, pc.course_category, "
        "pc.grade_recommendation, "
        "c.course_type, c.is_public_elective "
        "FROM program_courses pc "
        "JOIN courses c ON pc.course_id = c.course_id"
    )
    # 按 major_id 分组
    programs_by_major: Dict[int, List[Dict]] = {}
    for row in program_rows:
        programs_by_major.setdefault(row["major_id"], []).append(row)

    # 2. 逐个学生进行选课
    for s in students:
        sid = s["student_id"]
        grade = int(s["grade"])
        major_name = s["major"]

        mid = major_name_to_id.get(major_name)
        if not mid:
            # 找不到对应的专业 id，跳过
            continue

        academic_year = _get_academic_year(grade, semester)  # 大一=1，大二=2...

        # 该专业的课程配置
        pc_list = programs_by_major.get(mid, [])
        if not pc_list:
            continue

        required_courses: List[str] = []
        public_elective_courses: List[str] = []

        for row in pc_list:
            cid = row["course_id"]
            cat = row["course_category"]            # '必修' / '选修'
            rec_year = row["grade_recommendation"]  # 建议修读年级 1~4
            ctype = row["course_type"]              # '公共必修' / '专业必修' / ...
            is_pub_elect = row.get("is_public_elective", 0)

            # ① 公共基础课：只在大一学年修读（忽略原来的推荐年级设置）
            if ctype == "公共必修":
                if academic_year == 1 and cat == "必修":
                    required_courses.append(cid)
                continue  # 非大一不再修公共基础课

            # ② 正常的专业必修：按推荐年级匹配
            if cat == "必修" and rec_year == academic_year:
                required_courses.append(cid)
                continue

            # ③ 公选课（通识选修 is_public_elective=1）：作为公选候选
            if is_pub_elect == 1:
                public_elective_courses.append(cid)

        # 去重
        required_courses = list(dict.fromkeys(required_courses))
        public_elective_courses = list(dict.fromkeys(public_elective_courses))

        # 对每个学生：所有必修课都选择
        to_take_courses: List[str] = list(required_courses)

        # 公选课：最多从候选中随机选若干门
        if public_elective_courses and max_public_electives_per_student > 0:
            k = min(max_public_electives_per_student, len(public_elective_courses))
            extra = random.sample(public_elective_courses, k=k)
            to_take_courses.extend(extra)

        # 3. 把 “课程ID” 映射成 “开课实例 offering_id”，并写入 enrollments
        for cid in to_take_courses:
            oid = pick_offering_for_course(cid)
            if not oid:
                # 本学期该课程没开，或者满员了
                continue

            try:
                db.insert_data("enrollments", {
                    "student_id": sid,
                    "offering_id": oid,
                    "semester": semester
                })
                offering_current_counts[oid] = offering_current_counts.get(oid, 0) + 1
            except Exception as e:
                Logger.warning(f"学生 {sid} 选课 {cid} (offering {oid}) 失败: {e}")

    # 4. 最后统一刷新 course_offerings.current_students
    try:
        db.execute_update(
            "UPDATE course_offerings SET current_students = "
            "(SELECT COUNT(*) FROM enrollments WHERE enrollments.offering_id = course_offerings.offering_id)"
        )
    except Exception as e:
        Logger.warning(f"更新 course_offerings.current_students 失败: {e}")

    Logger.info("✅ 新版选课逻辑执行完成：按专业+年级+公共课/公选课分配。")


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


def bind_evening_public_offerings(db, semester: str="2024-2025-2"):
    try:
        # 查 CS301 的 offering
        offs = db.execute_query(
            "SELECT o.offering_id FROM course_offerings o "
            "JOIN courses c ON c.course_id=o.course_id "
            "WHERE c.is_public_elective=1 AND o.semester=?", (semester,)
        )
        if not offs:
            return

        # 找一个晚间节次与教室
        slot = db.execute_query("SELECT slot_id FROM time_slots WHERE session='EVENING' ORDER BY slot_id LIMIT 1")
        room = db.execute_query("SELECT classroom_id FROM classrooms ORDER BY classroom_id LIMIT 1")
        if not slot or not room:
            return
        sid = slot[0]['slot_id']
        cid = room[0]['classroom_id']

        for o in offs:
            try:
                db.execute_update(
                    "INSERT OR IGNORE INTO offering_sessions(offering_id,slot_id,classroom_id) VALUES(?,?,?)",
                    (o['offering_id'], sid, cid)
                )
            except Exception as e:
                Logger.warning(f"绑定晚间节次失败 offering={o['offering_id']}: {e}")
    except Exception:
        pass


def seed_colleges_and_majors(db: DBAdapter):
    """根据 COLLEGE_CATALOG 插入学院和其下的专业（每院≥2）。"""
    for code, name, majors in COLLEGE_CATALOG:
        try:
            db.insert_data("colleges", {"college_code": code, "name": name})
        except Exception:
            pass
        for m in majors:
            try:
                db.insert_data("majors", {"college_code": code, "name": m})
            except Exception:
                pass


def seed_classrooms(db):
    rooms = [
        ('教一-101','1',64,'普通教室'),
        ('教三-201','3',64,'普通教室'),
        ('主-报告厅','主',128,'智慧教室'),
        ('体-馆-1','体育馆',64,'体育馆'),
        ('体-场-1','体育场',128,'体育场')
    ]
    for n, loc, seat, t in rooms:
        try:
            db.execute_update(
                "INSERT OR IGNORE INTO classrooms(name,location_type,seat_count,room_type) VALUES(?,?,?,?)",
                (n,loc,seat,t)
            )
        except Exception:
            pass


def seed_timeslots(db):
    # AM：08:00 起每 45min 一节，休息 5min（节次与休息在业务层体现）
    def add(day, sec, start, end, session):
        try:
            db.execute_update(
                "INSERT INTO time_slots(day_of_week,section_no,starts_at,ends_at,session) VALUES(?,?,?,?,?)",
                (day, sec, start, end, session)
            )
        except Exception:
            pass

    # 一周 1~5 天示例
    for d in range(1, 6):
        # AM 两节（示例）
        add(d, 1, '08:00', '08:45', 'AM')
        add(d, 2, '08:50', '09:35', 'AM')
        # PM 两节（示例）
        add(d, 1, '13:00', '13:45', 'PM')
        add(d, 2, '13:50', '14:35', 'PM')
        # EVENING 两节（公选课）
        add(d, 1, '19:20', '20:05', 'EVENING')
        add(d, 2, '20:10', '20:55', 'EVENING')


def seed_program_courses(db: DBAdapter):
    """
    根据学院、专业和年级，生成详细的培养方案（program_courses）。
    确保不同学院、不同专业、不同学年都有不同的课程安排。
    """
    
    # 获取所有专业及其 ID 和所属学院代码
    majors = db.execute_query("SELECT major_id, college_code, name FROM majors ORDER BY major_id")
    if not majors:
        Logger.warning("未找到任何专业数据，跳过 program_courses 生成。")
        return

    # 全局课程分类，用于定义通用培养方案
    GLOBAL_COURSE_MAP = {
        # 1. 公共必修课（按年级推荐）
        "PUBLIC_REQUIRED": [
            # 大一：秋/春主要公共基础
            ("MA101", 1),   # 高数上
            ("MA102", 1),   # 高数下
            ("PH101", 1),   # 物理上
            ("EN101", 1),
            ("EN102", 1),
            ("PE101", 1),
            ("PE102", 1),
            ("ZX101", 1),   # 思修
            ("ML101", 1),   # 军事理论
            ("XL101", 1),   # 心理健康

            # 大二：高数后续 & 线代、概统、英语3/4 等
            ("MA201", 2),
            ("MA202", 2),
            ("PH102", 2),
            ("EN103", 2),
            ("EN104", 2),
            ("PE103", 2),
            ("PE104", 2),
            ("HX101", 2),   # 近代史纲要
            ("ZX102", 2),   # 马原
        ],

        # 2. 信息/通信类基础课（大二~大三）
        "INFO_CORE_REQUIRED": [
            ("CM201", 2),  # C语言
            ("CM202", 2),  # C++
            ("CM203", 2),  # Python
            ("CM204", 2),  # 数据结构
            ("CM205", 2),  # 离散数学
            ("CM206", 3),  # 组成原理
            ("CM207", 3),  # 操作系统
            ("CM208", 3),  # 数据库基础
            ("CM209", 3),  # 计网基础
            ("CM210", 3),  # 软件工程导论
        ],

        # 3. 公共选修/通识课（所有学院选修，大二/大三为主）
        "GENERAL_ELECTIVE": [
            ("GE101", 2),
            ("GE102", 2),
            ("GE103", 2),
            ("GE104", 2),
            ("GE105", 2),
            ("GE106", 2),
            ("GE107", 2),
            ("GE108", 3),
            ("GE109", 3),
            ("GE110", 3),
            ("GE111", 3),
            ("GE112", 3),
            ("GE113", 3),
            ("GE114", 3),
            ("GE115", 3),
            ("GE116", 3),
            ("GE117", 3),
            ("GE118", 3),
            ("GE119", 3),
            ("GE120", 3),
        ],
    }

    # 学院代码到课程ID的专业特色映射（专业核心课/高年级选修）
    COLLEGE_SPECIALTY_MAP = {
        # 计算机学院 2021001
        "2021001": [
            ("CS301", 3, '必修'),
            ("CS302", 3, '必修'),
            ("CS303", 3, '必修'),
            ("CS304", 3, '必修'),
            ("CS305", 4, '选修'),
            ("CS306", 4, '选修'),
            ("CS307", 4, '选修'),
            ("CS401", 4, '选修'),
            ("CS402", 4, '选修'),
            ("CS403", 4, '选修'),
            ("SE401", 4, '必修'),
            ("SE402", 3, '必修'),
            ("SE403", 4, '选修'),
        ],

        # 信息与通信工程学院 2021002
        "2021002": [
            ("TC201", 2, '必修'),
            ("TC202", 2, '必修'),
            ("TC203", 2, '必修'),
            ("TC301", 3, '必修'),
            ("TC302", 3, '必修'),
            ("TC303", 3, '必修'),
            ("TC401", 4, '必修'),
            ("TC402", 4, '选修'),
            ("TC403", 4, '选修'),
        ],

        # 网络空间安全学院 2021003
        "2021003": [
            ("SC201", 2, '必修'),
            ("SC202", 2, '必修'),
            ("SC301", 3, '必修'),
            ("SC302", 3, '选修'),
            ("SC303", 3, '选修'),
            ("SC304", 4, '选修'),
            ("SC401", 4, '必修'),
            ("SC402", 4, '选修'),
            # 共享 CS/CM 部分课程作为选修
            ("CM209", 3, '选修'),
            ("CS305", 4, '选修'),
        ],

        # 电子工程学院 2021004
        "2021004": [
            ("EE201", 2, '必修'),
            ("EE202", 2, '必修'),
            ("EE203", 2, '必修'),
            ("EE301", 3, '必修'),
            ("EE302", 3, '必修'),
            ("EE303", 3, '必修'),
            ("EE304", 4, '选修'),
            ("EE401", 4, '选修'),
            ("EE402", 4, '选修'),
        ],

        # 现代邮政学院 2021005
        "2021005": [
            ("MP201", 2, '必修'),
            ("MP202", 2, '必修'),
            ("MP301", 3, '必修'),
            ("MP302", 3, '必修'),
            ("MP303", 3, '选修'),
            ("MP401", 4, '选修'),
            ("MP402", 4, '选修'),
        ],

        # 人工智能学院 2021006
        "2021006": [
            ("AI201", 1, '必修'),
            ("AI202", 2, '选修'),
            ("AI301", 3, '必修'),
            ("AI302", 3, '必修'),
            ("AI303", 3, '选修'),
            ("AI304", 3, '选修'),
            ("AI401", 4, '必修'),
            ("AI402", 4, '选修'),
            # 共享计算机学院的一些课程
            ("CS301", 3, '必修'),
            ("CM204", 2, '必修'),
        ],

        # 国际学院 2021007
        "2021007": [
            ("IC201", 1, '必修'),
            ("IC202", 2, '必修'),
            ("IC301", 3, '选修'),
            # 国际计算机 / 电信等引入信息类基础
            ("CM201", 1, '必修'),
            ("CM202", 1, '必修'),
            ("CM204", 2, '必修'),
            ("CM209", 3, '必修'),
        ],
    }

    # 迭代所有专业进行绑定
    for major in majors:
        mid = major['major_id']
        ccode = major['college_code']
        mname = major['name']

        # --- 1. 公共必修课绑定 (所有专业) ---
        for course_id, grade_rec in GLOBAL_COURSE_MAP["PUBLIC_REQUIRED"]:
            db.execute_update("INSERT OR IGNORE INTO program_courses(major_id,course_id,course_category,grade_recommendation) VALUES(?,?,?,?)",
                              (mid, course_id, '必修', grade_rec))

        # --- 2. 信息类核心基础课绑定 (特定学院) ---
        if ccode in ["2021001", "2021002", "2021003", "2021004", "2021006", "2021007"]:
            for course_id, grade_rec in GLOBAL_COURSE_MAP["INFO_CORE_REQUIRED"]:
                # 国际学院的非信息类专业可以设为选修，这里简化为必修
                db.execute_update("INSERT OR IGNORE INTO program_courses(major_id,course_id,course_category,grade_recommendation) VALUES(?,?,?,?)",
                                  (mid, course_id, '必修', grade_rec))
                
        # --- 3. 专业特色课和高年级选修绑定 (按学院或专业名) ---
        if ccode in COLLEGE_SPECIALTY_MAP:
            for course_id, grade_rec, category in COLLEGE_SPECIALTY_MAP[ccode]:
                # 检查专业名，对同学院不同专业进行微调 (例如软件工程和计算机科学与技术)
                current_category = category
                quota = 0
                
                if "软件工程" in mname and course_id == "CS302":
                    # 软件工程专业把操作系统设为选修，计算机科学与技术专业设为必修
                    current_category = '选修'
                    quota = 10 # 软件工程可选修
                
                # 插入专业课程
                db.execute_update("INSERT OR IGNORE INTO program_courses(major_id,course_id,course_category,cross_major_quota,grade_recommendation) VALUES(?,?,?,?,?)",
                                  (mid, course_id, current_category, quota, grade_rec))

        # --- 4. 公共选修课绑定 (所有专业) ---
        for course_id, grade_rec in GLOBAL_COURSE_MAP["GENERAL_ELECTIVE"]:
             # 公选课：对所有专业都是选修，允许跨专业，设置名额
            db.execute_update("INSERT OR IGNORE INTO program_courses(major_id,course_id,course_category,cross_major_quota,grade_recommendation) VALUES(?,?,?,?,?)",
                              (mid, course_id, '选修', 50, grade_rec))
            
    # 最后：确保课程表中的公选标记与程序课程保持一致（防止在 create_courses 中未正确设置）
    db.execute_update("UPDATE courses SET is_public_elective=1 WHERE course_id IN ('GE101', 'GE102')")
    
    Logger.info("✅ 培养方案（program_courses）绑定完成，已区分学院、专业和学年推荐。")


def seed_all(db: DBAdapter, students: int = 200, teachers: int = 10, semester: str = "2024-2025-2"):
    """
    主流程：初始化表 -> 插入学院/专业 -> 教师 -> 学生 -> 课程 -> 开课 -> 选课 -> 成绩
    """
    try:
        # 若已有学生则提示跳过
        existing = db.execute_query("SELECT COUNT(*) as c FROM students")
        if existing and existing[0].get("c", 0) > 0:
            Logger.info("检测到已有学生数据，若需重新生成请先清空表或删除数据库文件。")
            return
    except Exception:
        pass

    # 1. 初始化数据库表结构（由 Database.init_tables() 统一创建）
    ensure_core_tables(db)

    # 2. 插入学院与专业（必须在学生之前）
    seed_colleges_and_majors(db)

    # 3. 教师
    create_teachers(db, teachers)

    # 4. 学生（依赖学院/专业）
    create_students(db, students)

    # 5. 课程
    create_courses(db)

    # 6. 教室
    seed_classrooms(db)

    # 7. 节次（AM/PM/EVENING）
    seed_timeslots(db)

    # 8. 专业-课程培养方案（必修/选修/公选）
    seed_program_courses(db)

    # === 9~11. 自动生成四个年级的完整学年（秋季 + 春季） ===
    start_year = int(semester.split("-")[0])

    SEMESTERS = [
        # 大一：秋+春
        f"{start_year}-{start_year+1}-1",
        f"{start_year}-{start_year+1}-2",

        # 大二：秋+春
        f"{start_year-1}-{start_year}-1",
        f"{start_year-1}-{start_year}-2",

        # 大三：秋+春
        f"{start_year-2}-{start_year-1}-1",
        f"{start_year-2}-{start_year-1}-2",

        # 大四：秋+春
        f"{start_year-3}-{start_year-2}-1",
        f"{start_year-3}-{start_year-2}-2",
    ]

    # 清空之前的 offering 、选课、成绩
    db.execute_update("DELETE FROM course_offerings")
    db.execute_update("DELETE FROM enrollments")
    db.execute_update("DELETE FROM grades")

    for sem in SEMESTERS:
        Logger.info(f"🟦 正在生成学期 {sem} 的开课 与 选课数据...")

        create_offerings(db, sem)
        enroll_students(db, sem)
        assign_grades(db)

    Logger.info("🎉 四个年级（秋季 + 春季）完整 8 个学期数据生成完毕！")


    # 12. 晚上公选课节次绑定
    bind_evening_public_offerings(db, semester=semester)

    Logger.info("✅ 合成数据生成完成。")


def import_students_from_csv(db: DBAdapter, csv_file: str = None) -> tuple[int, int]:
    """从 CSV 导入学生（存在则替换），返回 (成功数, 失败数)"""
    csv_path = Path(csv_file or data_dir / "students.csv")
    if not csv_path.exists():
        Logger.error(f"学生CSV文件不存在: {csv_path}")
        return 0, 0

    Logger.info(f"开始从 CSV 导入学生: {csv_path}")
    success = 0
    fail = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    sid = row.get('student_id', '').strip()
                    if not sid:
                        fail += 1
                        Logger.warning("跳过无学号行")
                        continue

                    student_data = {
                        'student_id': sid,
                        'name': row.get('name', '').strip(),
                        'password': row.get('password', '').strip(),
                        'gender': row.get('gender', '').strip(),
                        'birth_date': row.get('birth_date', '').strip() or None,
                        'major': row.get('major', '').strip(),
                        'grade': int(row.get('grade')) if row.get('grade') else None,
                        'class_name': row.get('class_name', '').strip(),
                        'enrollment_date': row.get('enrollment_date', '').strip() or None,
                        'status': row.get('status', 'active').strip(),
                        'email': row.get('email', '').strip(),
                        'phone': row.get('phone', '').strip(),
                        'created_at': row.get('created_at', now) or now,
                        'updated_at': row.get('updated_at', now) or now
                    }

                    # 如果密码看起来不是 bcrypt 哈希，则进行哈希（宽松检测）
                    pwd = student_data['password'] or ''
                    if pwd and not (pwd.startswith("$2") and len(pwd) > 50):
                        student_data['password'] = CryptoUtil.hash_password(pwd)

                    # 若已存在则先删除再插入（避免 update 方法不可用的适配问题）
                    existing = db.execute_query("SELECT student_id FROM students WHERE student_id=?", (sid,))
                    if existing:
                        try:
                            db.execute_update("DELETE FROM students WHERE student_id=?", (sid,))
                        except Exception:
                            Logger.debug(f"删除旧学生记录失败: {sid}，尝试直接覆盖")

                    db.insert_data('students', student_data)
                    success += 1

                except Exception as e:
                    fail += 1
                    Logger.error(f"导入学生失败: {row.get('student_id', 'unknown')} - {e}", exc_info=True)
                    continue

    except Exception as e:
        Logger.error(f"读取学生CSV失败: {e}", exc_info=True)
        return success, fail

    Logger.info(f"学生导入完成: 成功 {success} 条，失败 {fail} 条")
    return success, fail


def import_teachers_from_csv(db: DBAdapter, csv_file: str = None) -> tuple[int, int]:
    """从 CSV 导入教师（存在则替换），返回 (成功数, 失败数)"""
    csv_path = Path(csv_file or data_dir / "teachers.csv")
    if not csv_path.exists():
        Logger.error(f"教师CSV文件不存在: {csv_path}")
        return 0, 0

    Logger.info(f"开始从 CSV 导入教师: {csv_path}")
    success = 0
    fail = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    tid = row.get('teacher_id', '').strip()
                    if not tid:
                        fail += 1
                        Logger.warning("跳过无工号行")
                        continue

                    teacher_data = {
                        'teacher_id': tid,
                        'name': row.get('name', '').strip(),
                        'password': row.get('password', '').strip(),
                        'gender': row.get('gender', '').strip(),
                        'title': row.get('title', '').strip(),
                        'department': row.get('department', '').strip(),
                        'email': row.get('email', '').strip(),
                        'phone': row.get('phone', '').strip(),
                        'hire_date': row.get('hire_date', '').strip() or None,
                        'status': row.get('status', 'active').strip(),
                        'created_at': row.get('created_at', now) or now,
                        'updated_at': row.get('updated_at', now) or now
                    }

                    # 密码哈希检测
                    pwd = teacher_data['password'] or ''
                    if pwd and not (pwd.startswith("$2") and len(pwd) > 50):
                        teacher_data['password'] = CryptoUtil.hash_password(pwd)

                    existing = db.execute_query("SELECT teacher_id FROM teachers WHERE teacher_id=?", (tid,))
                    if existing:
                        try:
                            db.execute_update("DELETE FROM teachers WHERE teacher_id=?", (tid,))
                        except Exception:
                            Logger.debug(f"删除旧教师记录失败: {tid}，尝试直接覆盖")

                    db.insert_data('teachers', teacher_data)
                    success += 1

                except Exception as e:
                    fail += 1
                    Logger.error(f"导入教师失败: {row.get('teacher_id', 'unknown')} - {e}", exc_info=True)
                    continue

    except Exception as e:
        Logger.error(f"读取教师CSV失败: {e}", exc_info=True)
        return success, fail

    Logger.info(f"教师导入完成: 成功 {success} 条，失败 {fail} 条")
    return success, fail


def export_csv_files(db: DBAdapter, students_file: str = None, teachers_file: str = None,
                     mask_password: bool = False, exclude_password: bool = False):
    import csv
    from datetime import datetime

    students_file = students_file or str(data_dir / "students.csv")
    teachers_file = teachers_file or str(data_dir / "teachers.csv")

    Logger.info(f"导出 CSV: students -> {students_file}, teachers -> {teachers_file} (mask={mask_password}, exclude={exclude_password})")

    try:
        students = db.execute_query("SELECT * FROM students ORDER BY student_id")
        if students:
            fieldnames = [
                'student_id', 'name', 'password', 'gender', 'birth_date',
                'major', 'grade', 'class_name', 'enrollment_date', 'status',
                'email', 'phone', 'created_at', 'updated_at'
            ]
            if exclude_password and 'password' in fieldnames:
                fieldnames.remove('password')

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for s in students:
                if not s.get('created_at'):
                    s['created_at'] = now
                if not s.get('updated_at'):
                    s['updated_at'] = now

            with open(students_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for s in students:
                    row = {k: s.get(k, '') for k in fieldnames}
                    if mask_password and 'password' in row:
                        row['password'] = '***'  # 脱敏占位符
                    writer.writerow(row)
            Logger.info(f"已导出学生 CSV: {students_file}")

        teachers = db.execute_query("SELECT * FROM teachers ORDER BY teacher_id")
        if teachers:
            fieldnames = [
                'teacher_id', 'name', 'password', 'gender', 'title', 'department',
                'email', 'phone', 'hire_date', 'status', 'created_at', 'updated_at'
            ]
            if exclude_password and 'password' in fieldnames:
                fieldnames.remove('password')

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for t in teachers:
                if not t.get('created_at'):
                    t['created_at'] = now
                if not t.get('updated_at'):
                    t['updated_at'] = now

            with open(teachers_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for t in teachers:
                    row = {k: t.get(k, '') for k in fieldnames}
                    if mask_password and 'password' in row:
                        row['password'] = '***'
                    writer.writerow(row)
            Logger.info(f"已导出教师 CSV: {teachers_file}")

    except Exception as e:
        Logger.error(f"导出 CSV 失败: {e}", exc_info=True)

def export_course_summary(db: DBAdapter, filepath: str = "data/course_summary.csv"):
    """
    导出课程-教师-助教-学院的综合表格
    每一门课程一行
    """
    import csv

    # 查询所有课程
    courses = db.execute_query("""
        SELECT course_id, course_name, credits, hours, course_type, department
        FROM courses
        ORDER BY course_id
    """)

    if not courses:
        Logger.warning("没有课程数据，无法生成课程总表")
        return

    result = []

    for c in courses:
        cid = c["course_id"]

        # 查询主讲教师
        main_teachers = db.execute_query("""
            SELECT t.name
            FROM teacher_major_course r
            JOIN teachers t ON r.teacher_id = t.teacher_id
            WHERE r.course_id=? AND r.role='主讲'
        """, (cid,))

        # 查询助教
        ta_list = db.execute_query("""
            SELECT t.name
            FROM teacher_major_course r
            JOIN teachers t ON r.teacher_id = t.teacher_id
            WHERE r.course_id=? AND r.role='助教'
        """, (cid,))

        main_teacher_names = "、".join([t["name"] for t in main_teachers]) if main_teachers else ""
        ta_names = "、".join([t["name"] for t in ta_list]) if ta_list else ""

        result.append({
            "course_id": cid,
            "course_name": c["course_name"],
            "credits": c["credits"],
            "hours": c["hours"],
            "course_type": c["course_type"],
            "department": c["department"],  # 课程开设学院
            "teachers": main_teacher_names,
            "TAs": ta_names
        })

    # 写入 CSV
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "course_id", "course_name", "credits", "hours",
            "course_type", "department",
            "teachers", "TAs"
        ])
        writer.writeheader()
        for row in result:
            writer.writerow(row)

    Logger.info(f"课程汇总文件已生成 -> {filepath}")


def export_program_curriculum(db: DBAdapter, filepath: str = None):
    """
    导出每个专业的课程体系表（可理解为“课程体系图”的原始数据）
    字段示例：
    - 学院代码 / 学院名称
    - 专业名称
    - 建议年级（大一/大二/大三/大四）
    - 课程类别（必修/选修/公选）
    - 课程编号 / 课程名称 / 课程类型 / 开课学院 / 是否公选
    """
    import csv
    from pathlib import Path

    filepath = filepath or str(data_dir / "program_curriculum.csv")
    Logger.info(f"导出培养方案/课程体系 -> {filepath}")

    rows = db.execute_query(
        "SELECT pc.major_id, pc.course_id, pc.course_category, pc.cross_major_quota, pc.grade_recommendation, "
        "m.name AS major_name, m.college_code, "
        "co.name AS college_name, "
        "c.course_name, c.course_type, c.department, c.is_public_elective "
        "FROM program_courses pc "
        "JOIN majors m ON pc.major_id = m.major_id "
        "JOIN colleges co ON m.college_code = co.college_code "
        "JOIN courses c ON pc.course_id = c.course_id "
        "ORDER BY m.college_code, m.name, pc.grade_recommendation, pc.course_id"
    )

    if not rows:
        Logger.warning("没有 program_courses 数据，无法导出课程体系")
        return

    fieldnames = [
        "college_code", "college_name",
        "major_name",
        "grade_recommendation",   # 建议年级：1=大一, 2=大二...
        "course_category",        # 培养方案类别：必修/选修
        "course_id", "course_name",
        "course_type",            # 课程类型：公共必修/专业必修/通识选修...
        "department",             # 开课学院
        "is_public_elective",     # 是否公选课
        "cross_major_quota"       # 跨专业容量（如果有）
    ]

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({
                "college_code": r["college_code"],
                "college_name": r["college_name"],
                "major_name": r["major_name"],
                "grade_recommendation": r["grade_recommendation"],
                "course_category": r["course_category"],
                "course_id": r["course_id"],
                "course_name": r["course_name"],
                "course_type": r["course_type"],
                "department": r["department"],
                "is_public_elective": r["is_public_elective"],
                "cross_major_quota": r.get("cross_major_quota"),
            })

    Logger.info("✅ 课程体系表导出完成。")


def generate_curriculum_matrix(csv_path="data/program_curriculum.csv",
                               out_dir="data/curriculum_matrix"):
    """
    基于 program_curriculum.csv，为每个专业生成四年（8 学期）的课程矩阵图
    - 输出 Markdown 文件
    - 同时可导出 Excel 版本
    """

    if not os.path.exists(csv_path):
        print(f"❌ 未找到文件: {csv_path}")
        return

    os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(csv_path, encoding="utf-8")

    # 映射关系：建议年级 → 8 学期
    # 你的 grade_recommendation 是 1~4，我们映射成 2 学期
    grade_to_semesters = {
        1: ["大一（秋）", "大一（春）"],
        2: ["大二（秋）", "大二（春）"],
        3: ["大三（秋）", "大三（春）"],
        4: ["大四（秋）", "大四（春）"],
    }

    # 取得所有专业
    majors = df["major_name"].unique()

    for major in majors:
        df_major = df[df["major_name"] == major].copy()

        # ---- 初始化 8 学期的空列 ----
        sem_cols = [
            "大一（秋）", "大一（春）",
            "大二（秋）", "大二（春）",
            "大三（秋）", "大三（春）",
            "大四（秋）", "大四（春）"
        ]
        matrix = {col: [] for col in sem_cols}

        # ---- 填入课程 ----
        for _, row in df_major.iterrows():
            cid = row["course_id"]
            cname = row["course_name"]
            cat = row["course_category"]     # 必修/选修
            rec = int(row["grade_recommendation"])

            entry = f"{cid} {cname}（{cat}）"

            for sem in grade_to_semesters[rec]:
                matrix[sem].append(entry)

        # ---- 生成 Markdown 表格 ----
        md_path = os.path.join(out_dir, f"{major}_课程矩阵.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 🎓 {major} 四年课程矩阵图\n\n")

            for sem in sem_cols:
                f.write(f"## {sem}\n\n")
                if matrix[sem]:
                    for course in matrix[sem]:
                        f.write(f"- {course}\n")
                else:
                    f.write("> （无课程）\n")
                f.write("\n")

        # ---- 生成 Excel 文件 ----
        excel_path = os.path.join(out_dir, f"{major}_课程矩阵.xlsx")
        df_excel = pd.DataFrame(dict([(col, pd.Series(matrix[col])) for col in sem_cols]))
        df_excel.to_excel(excel_path, index=False)

    print("✅ 所有专业的 四年课程矩阵图 已生成完成！")


def main():
    """主函数"""
    Logger.init()
    if len(sys.argv) < 2:
        cmd = "all"
    else:
        cmd = sys.argv[1].lower()

    students = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    teachers = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    db_file = sys.argv[4] if len(sys.argv) > 4 else "bupt_teaching.db"
    semester = sys.argv[5] if len(sys.argv) > 5 else "2024-2025-2"
    mask_pwd = '--mask-password' in sys.argv
    exclude_pwd = '--exclude-password' in sys.argv

    db_path = data_dir / db_file
    db = DBAdapter(str(db_path))
    try:
        ensure_core_tables(db)

        if cmd in ("seed", "all"):
            seed_all(db, students=students, teachers=teachers, semester=semester)

        if cmd in ("export", "all"):
            export_csv_files(db,
                     students_file=str(data_dir / "students.csv"),
                     teachers_file=str(data_dir / "teachers.csv"),
                     mask_password=mask_pwd,
                     exclude_password=exclude_pwd)
            export_course_summary(db)
            export_program_curriculum(db)
            generate_curriculum_matrix()

        if cmd in ("import", "all"):
            # 从 CSV 导入数据库（会替换同学号/工号的记录）
            s_ok, s_fail = import_students_from_csv(db, str(data_dir / "students.csv"))
            t_ok, t_fail = import_teachers_from_csv(db, str(data_dir / "teachers.csv"))
            Logger.info(f"CSV 导入结果 - 学生 成功:{s_ok} 失败:{s_fail}；教师 成功:{t_ok} 失败:{t_fail}")

    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()