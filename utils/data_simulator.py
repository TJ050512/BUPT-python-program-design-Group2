"""
合成数据生成脚本（写入项目 data 目录下的 SQLite 文件）
用法:
    python -m utils.data_simulator <command> [students] [teachers] [dbfile] [base_semester]
    command: seed（仅生成 db 数据）, export（仅导出 CSV）, import（仅从 data/*.csv 导入）, all（seed->export->import）
    
    注意：base_semester 参数仅用于确定起始年份，系统会自动为所有学期（4个年级 × 2个学期 = 8个学期）
    生成开课计划、选课和成绩数据。
    
    示例:
    >> python -m utils.data_simulator all 3000 200 bupt_teaching.db 2024-2025-2
"""
import sys
import os
import re
import csv
import random
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, List, Dict, Set, Tuple
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

DEPT_NORMALIZE_MAP = {
    "理学院": "理学院",
    "马克思主义学院": "马克思主义学院",
    "体育部": "体育部",
    "外语学院": "外语学院",
    "人文学院": "人文学院",

    "计算机学院": "计算机学院",
    "信息与通信工程学院": "信息与通信工程学院",
    "电子工程学院": "电子工程学院",
    "现代邮政学院": "现代邮政学院",
    "网络空间安全学院": "网络空间安全学院",
    "人工智能学院": "人工智能学院",
    "国际学院": "国际学院",
}

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
            "dept": DEPT_NORMALIZE_MAP.get(dept, dept),
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
    # 精简后的公共选修课列表，保留更合适的课程
    general_electives = [
        # 人文艺术类
        ("GE101", "艺术欣赏"),
        ("GE102", "影视鉴赏"),
        ("GE103", "音乐鉴赏"),
        ("GE104", "书法艺术"),
        ("GE105", "中国传统文化"),
        ("GE106", "西方文化概论"),
        # 社会科学类
        ("GE107", "经济学原理"),
        ("GE108", "心理学导论"),
        ("GE109", "法律基础与法治思维"),
        ("GE110", "管理学基础"),
        ("GE111", "社会心理学"),
        # 思维与方法类
        ("GE112", "逻辑思维训练"),
        ("GE113", "批判性思维"),
        ("GE114", "哲学与人生"),
        ("GE115", "公共演讲与表达"),
        # 创新创业类
        ("GE116", "创新创业基础"),
        ("GE117", "职业生涯规划"),
        ("GE118", "项目管理基础"),
        # 科技与未来类
        ("GE119", "人工智能与社会"),
        ("GE120", "数据可视化"),
        ("GE121", "科技写作"),
        # 跨文化类
        ("GE122", "跨文化交际"),
        ("GE123", "世界文明史"),
        # 环境与可持续发展
        ("GE124", "环境与可持续发展"),
        ("GE125", "城市与社会发展"),
    ]
    for cid, name in general_electives:
        add(cid, name, 2.0, 32, "通识选修", "人文学院", is_public=1)
    # 各学院特色公共选修课
    add("AI310", "人工智能创新与实践",    2.0, 32, "通识选修", "人工智能学院", is_public=1)
    add("CS410", "大模型工业应用及实践",  2.0, 32, "通识选修", "计算机学院",   is_public=1)
    add("EE410", "小程序设计与开发",      2.0, 32, "通识选修", "电子工程学院", is_public=1)
    add("TC410", "5G通信技术概论",        2.0, 32, "通识选修", "信息与通信工程学院", is_public=1)
    add("SC410", "网络安全意识与防护",    2.0, 32, "通识选修", "网络空间安全学院", is_public=1)

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
    # 大二必修
    add("CS201", "面向对象程序设计",   3.0, 48, "专业必修", "计算机学院")
    add("CS202", "算法设计与分析",     3.0, 48, "专业必修", "计算机学院")
    # 大三必修
    add("CS301", "数据库系统原理",     3.0, 48, "专业必修", "计算机学院")
    add("CS302", "操作系统",           4.0, 64, "专业必修", "计算机学院")
    add("CS303", "编译原理",           3.0, 48, "专业必修", "计算机学院")
    add("CS304", "计算机体系结构",     3.0, 48, "专业必修", "计算机学院")
    # 大二选修
    add("CS203", "Java程序设计",      2.0, 32, "专业选修", "计算机学院")
    add("CS204", "Python高级编程",    2.0, 32, "专业选修", "计算机学院")
    add("CS205", "Linux系统管理",     2.0, 32, "专业选修", "计算机学院")
    # 大三选修
    add("CS305", "软件测试与质量保证", 2.0, 32, "专业选修", "计算机学院")
    add("CS306", "Web应用开发",        2.0, 32, "专业选修", "计算机学院")
    add("CS307", "移动互联网开发",     2.0, 32, "专业选修", "计算机学院")
    add("CS308", "分布式系统",         3.0, 48, "专业选修", "计算机学院")
    add("CS309", "计算机图形学",       3.0, 48, "专业选修", "计算机学院")
    add("CS310", "人机交互",           2.0, 32, "专业选修", "计算机学院")
    # 大四必修
    add("SE401", "软件工程实践",       3.0, 48, "专业必修", "计算机学院")
    add("SE402", "需求工程",           2.0, 32, "专业必修", "计算机学院")
    # 大四选修
    add("CS401", "人工智能基础",       3.0, 48, "专业选修", "计算机学院")
    add("CS402", "大数据处理技术",     3.0, 48, "专业选修", "计算机学院")
    add("CS403", "云计算与虚拟化",     2.0, 32, "专业选修", "计算机学院")
    add("CS404", "区块链技术",         2.0, 32, "专业选修", "计算机学院")
    add("CS405", "边缘计算",           2.0, 32, "专业选修", "计算机学院")
    add("SE403", "软件项目管理",       2.0, 32, "专业选修", "计算机学院")
    add("SE404", "软件架构设计",       3.0, 48, "专业选修", "计算机学院")

    # === 五、信息与通信工程学院 ===
    # 大二基础
    add("TC201", "电路分析基础",       4.0, 64, "学科基础", "信息与通信工程学院")
    add("TC202", "模拟电子技术基础",   4.0, 64, "学科基础", "信息与通信工程学院")
    add("TC203", "数字电子技术基础",   4.0, 64, "学科基础", "信息与通信工程学院")
    # 大二选修
    add("TC204", "高频电子线路",       3.0, 48, "专业选修", "信息与通信工程学院")
    add("TC205", "电磁场与微波技术",   3.0, 48, "专业选修", "信息与通信工程学院")
    # 大三必修
    add("TC301", "信号与系统",         4.0, 64, "专业必修", "信息与通信工程学院")
    add("TC302", "通信原理",           4.0, 64, "专业必修", "信息与通信工程学院")
    add("TC303", "信息论与编码",       3.0, 48, "专业必修", "信息与通信工程学院")
    # 大三选修
    add("TC304", "数字信号处理",       3.0, 48, "专业选修", "信息与通信工程学院")
    add("TC305", "通信网络基础",       3.0, 48, "专业选修", "信息与通信工程学院")
    add("TC306", "无线通信技术",       3.0, 48, "专业选修", "信息与通信工程学院")
    # 大四必修
    add("TC401", "移动通信原理",       3.0, 48, "专业必修", "信息与通信工程学院")
    # 大四选修
    add("TC402", "数字通信系统",       3.0, 48, "专业选修", "信息与通信工程学院")
    add("TC403", "光纤通信技术",       2.0, 32, "专业选修", "信息与通信工程学院")
    add("TC404", "卫星通信",           2.0, 32, "专业选修", "信息与通信工程学院")
    add("TC405", "物联网通信技术",     2.0, 32, "专业选修", "信息与通信工程学院")

    # === 六、网络空间安全学院 ===
    # 大二基础
    add("SC201", "密码学基础",         3.0, 48, "学科基础", "网络空间安全学院")
    add("SC202", "安全数学基础",       3.0, 48, "学科基础", "网络空间安全学院")
    # 大二选修
    add("SC203", "信息安全导论",       2.0, 32, "专业选修", "网络空间安全学院")
    add("SC204", "网络协议分析",       2.0, 32, "专业选修", "网络空间安全学院")
    # 大三必修
    add("SC301", "网络安全技术",       3.0, 48, "专业必修", "网络空间安全学院")
    # 大三选修
    add("SC302", "操作系统安全",       2.0, 32, "专业选修", "网络空间安全学院")
    add("SC303", "Web安全",            2.0, 32, "专业选修", "网络空间安全学院")
    add("SC304", "恶意代码分析",       2.0, 32, "专业选修", "网络空间安全学院")
    add("SC305", "安全编程",           2.0, 32, "专业选修", "网络空间安全学院")
    add("SC306", "数字取证技术",       2.0, 32, "专业选修", "网络空间安全学院")
    # 大四必修
    add("SC401", "密码学",             3.0, 48, "专业必修", "网络空间安全学院")
    # 大四选修
    add("SC402", "安全攻防实践",       3.0, 48, "专业选修", "网络空间安全学院")
    add("SC403", "区块链安全",         2.0, 32, "专业选修", "网络空间安全学院")
    add("SC404", "云安全技术",         2.0, 32, "专业选修", "网络空间安全学院")

    # === 七、电子工程学院 ===
    # 大二基础
    add("EE201", "电路原理",           4.0, 64, "学科基础", "电子工程学院")
    add("EE202", "模拟电子技术",       4.0, 64, "学科基础", "电子工程学院")
    add("EE203", "数字电子技术",       4.0, 64, "学科基础", "电子工程学院")
    # 大二选修
    add("EE204", "电子测量技术",       2.0, 32, "专业选修", "电子工程学院")
    add("EE205", "EDA技术",            2.0, 32, "专业选修", "电子工程学院")
    # 大三必修
    add("EE301", "电磁场与电磁波",     4.0, 64, "专业必修", "电子工程学院")
    add("EE302", "数字信号处理",       3.0, 48, "专业必修", "电子工程学院")
    add("EE303", "单片机原理与接口技术", 3.0, 48, "专业必修", "电子工程学院")
    # 大三选修
    add("EE304", "嵌入式系统设计",     3.0, 48, "专业选修", "电子工程学院")
    add("EE305", "FPGA设计",           3.0, 48, "专业选修", "电子工程学院")
    add("EE306", "传感器技术",         2.0, 32, "专业选修", "电子工程学院")
    # 大四选修
    add("EE401", "射频电路设计",       3.0, 48, "专业选修", "电子工程学院")
    add("EE402", "集成电路设计基础",   3.0, 48, "专业选修", "电子工程学院")
    add("EE403", "功率电子技术",       3.0, 48, "专业选修", "电子工程学院")
    add("EE404", "光电子技术",         2.0, 32, "专业选修", "电子工程学院")

    # === 八、现代邮政学院 ===
    add("MP201", "管理学原理",         3.0, 48, "学科基础", "现代邮政学院")
    add("MP202", "运筹学基础",         3.0, 48, "学科基础", "现代邮政学院")
    add("MP301", "现代物流学",         3.0, 48, "专业必修", "现代邮政学院")
    add("MP302", "供应链管理",         3.0, 48, "专业必修", "现代邮政学院")
    add("MP303", "电子商务概论",       2.0, 32, "专业选修", "现代邮政学院")
    add("MP401", "快递服务管理",       3.0, 48, "专业选修", "现代邮政学院")
    add("MP402", "物流系统规划与设计", 3.0, 48, "专业选修", "现代邮政学院")

    # === 九、人工智能学院 ===
    # 大二基础
    add("AI201", "人工智能导论",       2.0, 32, "学科基础", "人工智能学院")
    add("AI202", "概率图模型基础",     2.0, 32, "学科基础", "人工智能学院")
    # 大二选修
    add("AI203", "Python数据分析",    2.0, 32, "专业选修", "人工智能学院")
    add("AI204", "数据挖掘基础",      2.0, 32, "专业选修", "人工智能学院")
    # 大三必修
    add("AI301", "机器学习",           3.0, 48, "专业必修", "人工智能学院")
    add("AI302", "深度学习",           3.0, 48, "专业必修", "人工智能学院")
    # 大三选修
    add("AI303", "计算机视觉",         3.0, 48, "专业选修", "人工智能学院")
    add("AI304", "自然语言处理",       3.0, 48, "专业选修", "人工智能学院")
    add("AI305", "知识图谱",           2.0, 32, "专业选修", "人工智能学院")
    add("AI306", "推荐系统",           2.0, 32, "专业选修", "人工智能学院")
    # 大四必修
    add("AI401", "模式识别",           3.0, 48, "专业必修", "人工智能学院")
    # 大四选修
    add("AI402", "强化学习",           3.0, 48, "专业选修", "人工智能学院")
    add("AI403", "生成对抗网络",       2.0, 32, "专业选修", "人工智能学院")
    add("AI404", "多智能体系统",       2.0, 32, "专业选修", "人工智能学院")

    # === 十、国际学院（示例用信息类 & 英语强化） ===
    add("IC201", "学术英语写作",       3.0, 48, "学科基础", "国际学院")
    add("IC202", "产品开发与项目管理",         2.0, 32, "学科基础", "国际学院")
    add("IC301", "人工智能法律",   2.0, 32, "专业选修", "国际学院")

     # ============================
    # 🔥 统一调整课程学分分布：
    #    - 98% = 2 学分
    #    - 2% = 随机 1 或 3 学分
    # ============================
    import random
    for cid, info in pool.items():
        # 98% → 两连节
        if random.random() < 0.98:
            info["credits"] = 2.0
            info["hours"] = 32   # 2 节 * 45 分钟 ~= 32 学时
        else:
            # 2% → 1 或 3
            c = random.choice([1, 3])
            info["credits"] = float(c)
            info["hours"] = 16 if c == 1 else 48   # 1节=16学时，3节=48学时

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
    """统一调用 init_tables，并自动升级 course_offerings 表结构"""
    try:
        # 1. 初始化表结构
        if hasattr(db, "_impl") and hasattr(db._impl, "init_tables"):
            db._impl.init_tables()
        elif hasattr(db, "init_tables"):
            db.init_tables()
        else:
            Database("data/bupt_teaching.db").init_tables()

        # 2. 自动升级 course_offerings 表结构
        cols = db.execute_query(
            "PRAGMA table_info(course_offerings)"
        )
        col_names = [c["name"] for c in cols]

        def add_column_if_missing(col_name, col_def):
            if col_name not in col_names:
                try:
                    db.execute_update(
                        f"ALTER TABLE course_offerings ADD COLUMN {col_def}"
                    )
                    Logger.info(f"已自动添加字段 {col_name} 至 course_offerings")
                except Exception as e:
                    Logger.warning(f"添加字段 {col_name} 失败：{e}")

        # 需要添加的字段
        add_column_if_missing("ta1_id", "ta1_id TEXT")
        add_column_if_missing("ta2_id", "ta2_id TEXT")
        add_column_if_missing("department", "department TEXT")
        add_column_if_missing("class_time", "class_time TEXT")
        add_column_if_missing("classroom", "classroom TEXT")
        add_column_if_missing("max_students", "max_students INTEGER DEFAULT 60")
        add_column_if_missing("current_students", "current_students INTEGER DEFAULT 0")
        add_column_if_missing("status", "status TEXT DEFAULT 'open'")

        Logger.info("表结构检查完毕（自动升级完成）")

    except Exception as e:
        Logger.error(f"表结构初始化失败: {e}", exc_info=True)


def upgrade_course_offerings_table(db):
    """自动升级 course_offerings 表结构，缺字段则添加"""
    try:
        # 读取表结构
        rows = db.execute_query("PRAGMA table_info(course_offerings)")
        cols = [r["name"] for r in rows]

        # 需要确保的字段
        needed = {
            "ta1_id": "TEXT",
            "ta2_id": "TEXT",
            "department": "TEXT",
            "class_time": "TEXT",
            "classroom": "TEXT",
            "max_students": "INTEGER DEFAULT 60",
            "current_students": "INTEGER DEFAULT 0",
            "status": "TEXT DEFAULT 'open'"
        }
        for col, typ in needed.items():
            if col not in cols:
                try:
                    db.execute_update(f"ALTER TABLE course_offerings ADD COLUMN {col} {typ}")
                    print(f"已自动添加字段: {col}")
                except Exception as e:
                    print(f"添加字段 {col} 失败（可能已存在）: {e}")

    except Exception as e:
        print("检查/升级 course_offerings 失败：", e)


# ---------- 以下为合成数据生成逻辑（使用 DBAdapter 作为抽象后端） ----------
def create_teachers(db: DBAdapter, n: int = 10):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 学院池（可继续扩展）
    departments = [
        "理学院",
        "马克思主义学院",
        "体育部",
        "外语学院",
        "人文学院",
        "计算机学院",
        "信息与通信工程学院",
        "电子工程学院",
        "现代邮政学院",
        "网络空间安全学院",
        "人工智能学院",
        "国际学院",
    ]

    # 职称、岗位类型、职级映射（保留你之前的增强）
    title_weights = {
        "讲师": 18,
        "研究员": 3,
        "副研究员": 3,
        "副教授": 3,
        "教授": 1,
    }
    job_type_map = {
        "教授": "教学科研岗", "副教授": "教学科研岗", "讲师": "教学科研岗", "助教": "教学科研岗",
        "研究员": "科研岗", "副研究员": "科研岗", "助理研究员": "科研岗",
        "实验师": "实验技术岗", "高级实验师": "实验技术岗",
        "辅导员": "学生管理岗", "教学秘书": "教务管理岗", "教务员": "教务管理岗", "行政主管": "行政管理岗", "后勤主管": "后勤管理岗"
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

    majors_rows = db.execute_query("SELECT major_id, name FROM majors")
    major_name_to_id = {m["name"]: m["major_id"] for m in majors_rows} if majors_rows else {}

    # 1. 计算每届每院的基础人数
    num_colleges = len(COLLEGE_CATALOG)
    num_grades = len(grade_years)
    # per_college_per_grade_base 成为每个【年级 x 学院】的学生人数上限
    per_college_per_grade_base = max(1, total_count // (num_colleges * num_grades))

    # 出生年分布（示例）
    min_birth, max_birth = 2001, 2006
    mu, sigma = 2003.0, 1.2
    
    students_created_count = 0

    for grade in grade_years:
        # college_code_full 是 COLLEGE_CATALOG 中的 7 位学院代码 (如: 2021001)
        for c_idx, (college_code_full, college_name, major_pool) in enumerate(COLLEGE_CATALOG, start=1):
            
            # 2. 确定该【学院 x 年级】的实际学生人数 (略微浮动)
            students_in_college_grade = per_college_per_grade_base + random.randint(-1, 1)
            students_in_college_grade = max(1, students_in_college_grade)
            
            # 3. 在这个学院和年级内生成学生
            # seq 是学生序号，用于生成学号的最后三位 zzz
            for seq in range(1, students_in_college_grade + 1):
                
                # 确定该学生分配到的专业 (按序号循环分配到专业，确保分布均匀)
                major_index = (seq - 1) % len(major_pool)
                major = major_pool[major_index] # 专业名称
                m_idx = major_index + 1
                
                # 3位 yyy = 前两位学院序号 + 第三位专业序号
                # 这部分代码用于生成学号中间的 yyy 部分，并写入 college_code 字段
                college_code_yyy = f"{c_idx:02d}{m_idx}" 

                # 学号：xxxx (年级) + yyy (学院+专业) + zzz (序号)
                sid = _gen_student_id(grade, college_code_yyy, seq)
                
                # 班级号（每10人一个班）
                class_serial = (seq - 1) // 10 + 1
                class_name = _gen_class_name(grade, c_idx, class_serial)
                
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
                    "major": major,                      # 专业=文本字段（使用循环确定的专业）
                    "major_id": major_name_to_id.get(major),
                    "grade": grade,                      # 年级=2022~2025
                    "class_name": class_name,            # 班级号=xxxx yyy zzz
                    "college_code": college_code_full,    # 学院码=yyy（与学号 yyy 部分一致）
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
                    students_created_count += 1
                except Exception as e:
                    Logger.warning(f"插入学生失败 {sid}: {e}")
                    
    Logger.info(f"✅ 学生数据生成完成，共创建 {students_created_count} 条记录。")


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


# ===========================================
# 🔥 学期开课系数表：不同学期 → 不同课程数量倍数
# ===========================================
SEMESTER_FACTOR = {
    # 大一（通常课程最多）
    "-1": 1.4,   # 秋季（如 2024-2025-1）
    "-2": 1.2,   # 春季（如 2024-2025-2）

    # 大二（核心课多）
    "-3": 1.3,
    "-4": 1.3,

    # 大三（专业课为主）
    "-5": 1.1,
    "-6": 1.1,

    # 大四（最少）
    "-7": 0.8,
    "-8": 0.6,
}


def _calc_offering_count_by_attr(course_row: Dict[str, Any], semester: str) -> int:
    """
    模式 B：根据课程属性 + 学期系数决定开课数量
    """
    ctype = course_row.get("course_type", "") or ""
    is_public = int(course_row.get("is_public_elective", 0) or 0)

    # 基础数量（不考虑学期）
    if ctype == "公共必修":
        base = 10
    elif ctype == "学科基础":
        base = 8
    elif ctype == "专业必修":
        base = 4
    elif is_public == 1:
        base = 3
    else:
        base = 2

    # 学期系数：根据 -1 / -2 / -3 / ... 获取
    idx = semester.split("-")[-1]              # "1" 或 "2"
    year = semester.split("-")[0]              # "2024"
    sem_key = f"-{idx}"                        # "-1" 或 "-2"

    # 找到在 SEMESTER_FACTOR 中的位置
    # seed_all 本身就是按 8 个学期顺序生成 → 可以修改为：
    factor = SEMESTER_FACTOR.get(sem_key, 1.0)

    return max(1, int(base * factor))


# ================= 讲师优先级排序 =================
TITLE_ORDER = {"讲师": 0, "副教授": 1, "教授": 2}

# ================= 课程 → 哪个学院上课 =================
def resolve_teacher_dept(course_row):
    """
    返回课程应该由哪个学院授课（直接使用课程的 department）
    """
    return course_row.get("department")


# 年级到学期索引的映射（用于多学期模式）
# 年级1对应索引0-1，年级2对应索引2-3，年级3对应索引4-5，年级4对应索引6-7
GRADE_TO_SEM_INDEX = {1: 0, 2: 2, 3: 4, 4: 6}


def _get_course_term(db: DBAdapter, course_id: str) -> str:
    """
    返回课程的季节属性："秋" 或 "春"
    优先按课程名判断，上/下/1/2；再兜底按编号奇偶。
    """
    row = db.execute_query(
        "SELECT course_name FROM courses WHERE course_id=?",
        (course_id,)
    )
    cname = row[0]["course_name"] if row else ""

    # 1) 名称里带"上 / I / 1 / (上)" → 秋
    if any(k in cname for k in ["上", "Ⅰ", "I", "（上）", "(上)", "1"]):
        return "秋"

    # 2) 名称里带"下 / II / 2 / (下)" → 春
    if any(k in cname for k in ["下", "Ⅱ", "II", "（下）", "(下)", "2"]):
        return "春"

    # 3) 特殊规则：大学英语和大学体育系列
    # 大学英语系列：EN101(秋), EN102(春), EN103(秋), EN104(春)
    if course_id.startswith('EN10'):
        last_digit = int(course_id[-1])
        return "春" if last_digit % 2 == 0 else "秋"
    
    # 大学体育系列：PE101(秋), PE102(春), PE103(秋), PE104(春)
    if course_id.startswith('PE10'):
        last_digit = int(course_id[-1])
        return "春" if last_digit % 2 == 0 else "秋"

    # 4) 兜底：取编号数字部分奇偶
    digits = re.findall(r"\d+", course_id)
    if digits:
        num = int(digits[-1])
        return "秋" if num % 2 == 1 else "春"

    # 5) 最后兜底：默认秋
    return "秋"


def build_unique_course_semester_plan(db: DBAdapter, SEM_LIST: List[str]) -> Dict[str, str]:
    """
    返回 dict: course_id -> semester（唯一）
    规则：
    - 多学期：按 program_courses.grade_recommendation 映射到对应学年秋季学期，并随机偏移到春季
    - 单学期：只把"与当前学期季节匹配"的课程映射到该学期
    """
    if not SEM_LIST:
        return {}

    # 使用全局的 _get_course_term 函数
    def get_term(course_id: str) -> str:
        return _get_course_term(db, course_id)

    # ============================================================
    # ✅ 单学期模式：只开当前季节的课程（不把春季塞到秋季）
    # ============================================================
    if len(SEM_LIST) == 1:
        only_sem = SEM_LIST[0]
        sem_idx = only_sem.split("-")[-1]  # "1" or "2"
        current_term = "秋" if sem_idx == "1" else "春"

        rows = db.execute_query("SELECT course_id FROM courses")
        plan = {}
        for r in rows:
            cid = r["course_id"]
            if get_term(cid) == current_term:
                plan[cid] = only_sem
        return plan

    # ============================================================
    # 多学期模式：根据课程季节属性和年级推荐分配学期
    # ============================================================
    # 使用全局的 GRADE_TO_SEM_INDEX 常量

    # 获取所有课程及其年级推荐（如果有多个专业，取最常见的年级推荐）
    rows = db.execute_query("""
        SELECT course_id, grade_recommendation, COUNT(*) as cnt
        FROM program_courses
        WHERE grade_recommendation IS NOT NULL
        GROUP BY course_id, grade_recommendation
        ORDER BY course_id, cnt DESC
    """)
    
    # 对于每门课程，选择最常见的年级推荐
    course_grade_map = {}
    for r in rows:
        cid = r["course_id"]
        if cid not in course_grade_map:
            course_grade_map[cid] = int(r.get("grade_recommendation") or 1)

    plan = {}
    for cid, gr in course_grade_map.items():
        idx_base = GRADE_TO_SEM_INDEX.get(gr, 0)
        
        # 根据课程本身的季节属性决定偏移，而不是随机
        # 这样可以确保春季课程（如EN102, MA102, PE102, PH102）在春季学期开课
        course_term = get_term(cid)
        sem_offset = 1 if course_term == "春" else 0  # 春=1(春季学期), 秋=0(秋季学期)
        
        idx = idx_base + sem_offset

        if idx < len(SEM_LIST):
            plan[cid] = SEM_LIST[idx]
            # 调试：记录关键课程的分配
            if cid in ["EN102", "MA102", "PE102", "PH102"]:
                Logger.debug(f"课程 {cid} (年级推荐={gr}, 季节={course_term}) 分配到学期: {SEM_LIST[idx]} (索引={idx})")

    return plan


def create_offerings(db: DBAdapter, semester: str, all_semesters: List[str]) -> list[int]:
    """
    开课 + 排课（连续节次版本）：
    - 每门课本学期开设若干个班（数量由 _calc_offering_count_by_attr 决定）
    - 每个班：
        * 每周节次数 = 学分 (int)
        * 所有节次安排在同一天、同一教室、连续的 section_no
        * 公选课只排在晚上 (EVENING)
    """
    # 维护冲突状态（跨所有学期，避免不同学期之间的冲突检查）
    schedule_state_room: Set[Tuple[int, int]] = set()    # (slot_id, classroom_id)
    schedule_state_teacher: Set[Tuple[str, int]] = set() # (teacher_id, slot_id)

    # 把已存在的排课读进内存状态（读取所有学期的排课，避免跨学期冲突）
    # 注意：这里只读取当前学期的排课，因为不同学期的排课不应该冲突
    occupied_sessions = db.execute_query("""
        SELECT os.slot_id, os.classroom_id, o.teacher_id
        FROM offering_sessions os
        JOIN course_offerings o ON os.offering_id = o.offering_id
        WHERE o.semester = ?
    """, (semester,))
    for s in occupied_sessions:
        schedule_state_room.add((s["slot_id"], s["classroom_id"]))
        schedule_state_teacher.add((s["teacher_id"], s["slot_id"]))

    # 唯一学期开课计划（每门课在哪个学期开）
    course_sem_plan = build_unique_course_semester_plan(db, all_semesters)

    # 所有课程
    courses = db.execute_query(
        "SELECT course_id, course_name, course_type, department, credits, "
        "COALESCE(is_public_elective,0) AS is_public_elective "
        "FROM courses"
    )
    if not courses:
        Logger.warning("⚠️ courses 表为空，无法生成开课记录。")
        return []

    # 教师按学院分组
    teacher_rows = db.execute_query(
        "SELECT teacher_id, name, department, title FROM teachers WHERE status='active'"
    )
    teacher_by_dept: Dict[str, List[Dict[str, Any]]] = {}
    for t in teacher_rows:
        teacher_by_dept.setdefault(t["department"], []).append(t)

    all_teachers = list(teacher_rows)
    if not all_teachers:
        Logger.warning("⚠️ 没有教师数据，无法生成开课记录。")
        return []

    # 所有教室、节次
    classrooms = db.execute_query("SELECT classroom_id, name, room_type FROM classrooms")
    timeslots = db.execute_query("SELECT slot_id, day_of_week, section_no, session FROM time_slots")
    if not classrooms or not timeslots:
        Logger.warning("⚠️ 教室或节次数据缺失，无法排课。")
        return []

    # 按 day_of_week + session 分组节次，方便找连续 section_no
    # timeslots_by_day_session[day][session] = [slot_row,...] 已按 section_no 排序
    timeslots_by_day_session: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
    for ts in timeslots:
        d = ts["day_of_week"]
        sess = ts["session"]
        timeslots_by_day_session.setdefault(d, {}).setdefault(sess, []).append(ts)
    for d in timeslots_by_day_session:
        for sess in timeslots_by_day_session[d]:
            timeslots_by_day_session[d][sess].sort(key=lambda x: x["section_no"])

    offering_ids: List[int] = []

    # 小工具：根据课程属性选择可用教室
    def find_valid_rooms(course_type: str, cid: str, is_public: int) -> List[Dict[str, Any]]:
        general_rooms = [r for r in classrooms if r.get("room_type") in ("普通教室", "智慧教室")]
        if course_type == "公共必修" and cid.startswith("PE"):
            rooms = [r for r in classrooms if r.get("room_type") == "体育馆"]
        elif course_type in ("学科基础", "专业必修") and cid.startswith(("CM", "CS")):
            rooms = [r for r in classrooms if r.get("room_type") in ("机房", "普通教室", "智慧教室")]
        elif course_type == "通识选修" and is_public == 1:
            rooms = [r for r in classrooms if r.get("room_type") in ("报告厅", "普通教室", "智慧教室")]
        else:
            rooms = general_rooms
        if not rooms:
            rooms = general_rooms
        return rooms

    # 维护公选课已使用的晚上时间段，确保每个公选课有不同的时间段
    public_elective_used_slots: Set[Tuple[int, int]] = set()  # (day, section_no) 已使用的组合
    
    # 核心：为一个班找"同一天、同一 session、连续 N 节"的时段 + 一个教室
    def assign_continuous_block(
        teacher_id: str,
        needed: int,
        is_public: int,
        valid_rooms: List[Dict[str, Any]],
        course_id: str = ""  # 新增参数：用于公选课区分
    ) -> List[Tuple[int, int, str]]:
        """
        返回 [(slot_id, classroom_id, room_name), ...] 长度 = needed
        如果找不到则返回空列表。
        """
        # 公选课只排晚上（13-14节）
        if is_public == 1:
            session_pool = ["EVENING"]
            # 公选课必须使用13-14节（section_no 13, 14）
            evening_sections = [13, 14]
        else:
            session_pool = ["AM", "PM"]
            evening_sections = None

        days = list(range(1, 6))  # 周一到周五
        random.shuffle(days)

        for day in days:
            for sess in random.sample(session_pool, len(session_pool)):
                slot_list = timeslots_by_day_session.get(day, {}).get(sess, [])
                if not slot_list:
                    continue

                # 公选课：只考虑13-14节
                if is_public == 1 and evening_sections:
                    slot_list = [s for s in slot_list if s["section_no"] in evening_sections]

                # 过滤掉教师已经占用的节次
                available_slots = [
                    s for s in slot_list
                    if (teacher_id, s["slot_id"]) not in schedule_state_teacher
                ]
                
                # 公选课：还要过滤掉已经使用的时间段（确保每个公选课时间不同）
                if is_public == 1:
                    available_slots = [
                        s for s in available_slots
                        if (day, s["section_no"]) not in public_elective_used_slots
                    ]
                
                if len(available_slots) < needed:
                    continue

                # 找连续 section_no 的长度为 needed 的窗口
                available_slots.sort(key=lambda x: x["section_no"])

                for i in range(0, len(available_slots) - needed + 1):
                    cand = available_slots[i:i+needed]
                    # 检查是否 section_no 连续
                    ok = True
                    for j in range(1, len(cand)):
                        if cand[j]["section_no"] != cand[j-1]["section_no"] + 1:
                            ok = False
                            break
                    if not ok:
                        continue

                    # 为这一组连续节次挑一个"全程都空"的教室
                    random.shuffle(valid_rooms)
                    for room in valid_rooms:
                        room_id = room["classroom_id"]
                        room_name = room["name"]

                        # 检查该教室在所有候选 slot 上是否都空闲
                        conflict = False
                        for s in cand:
                            if (s["slot_id"], room_id) in schedule_state_room:
                                conflict = True
                                break
                        if conflict:
                            continue

                        # 可以使用这个教室：记录所有节次，并更新冲突状态
                        assigned: List[Tuple[int, int, str]] = []
                        for s in cand:
                            sid = s["slot_id"]
                            assigned.append((sid, room_id, room_name))
                            schedule_state_room.add((sid, room_id))
                            schedule_state_teacher.add((teacher_id, sid))
                            # 公选课：记录已使用的时间段
                            if is_public == 1:
                                public_elective_used_slots.add((day, s["section_no"]))
                        return assigned

        # 所有 day/session 都尝试过仍然失败
        return []

    # ==== 正式为每门课开课 + 排课 ====
    for c in courses:
        cid = c["course_id"]
        dept = c.get("department") or ""
        course_type = c.get("course_type") or ""
        is_public = int(c.get("is_public_elective", 0) or 0)
        credits = c.get("credits", 0)

        # 检查这门课是否应该在当前学期开课
        # 对于公共必修课程，应该在每个年级的对应学期都开课
        # 例如：EN102（大一春季）应该在所有年级的大一春季学期都开课
        should_offer = False
        
        # 获取课程的季节属性
        course_term = _get_course_term(db, cid)
        # 获取当前学期是秋季还是春季rrent_sem_term = "秋" if semester.endswith("-1") else "春
        current_sem_term = "秋" if semester.endswith("-1") else "春"
        
        # ✅ 公选/通识选修：每学期都开，不做秋春匹配
        is_public = int(c.get("is_public_elective", 0) or 0)
        course_type = c.get("course_type") or ""

        if is_public == 1 or course_type == "通识选修":
            course_term = current_sem_term  # 强制认为匹配
        else:
            course_term = _get_course_term(db, cid)
            if course_term != current_sem_term:
                continue
        
        # 从 program_courses 中查找该课程的年级推荐
        course_grade_rows = db.execute_query("""
            SELECT DISTINCT grade_recommendation
            FROM program_courses
            WHERE course_id = ?
            LIMIT 1
        """, (cid,))
        
        if not course_grade_rows:
            # 调试：记录没有年级推荐的课程
            if cid in ["ML101", "PH101", "XL101", "EN101", "MA101", "PE101"]:
                Logger.warning(f"课程 {cid} 在 program_courses 表中没有记录，跳过开课")
            # ✅ 公选/通识没写 program_courses 也照常开
            if is_public == 1 or course_type == "通识选修":
                gr = 1
            else:
                continue
        else:
        
            gr = int(course_grade_rows[0].get("grade_recommendation") or 1)
        
        # 计算当前学期在 SEM_LIST 中的索引
        try:
            sem_idx = all_semesters.index(semester)
        except ValueError:
            continue
        
        # 计算该课程应该开课的学期索引
        # GRADE_TO_SEM_INDEX: {1: 0, 2: 2, 3: 4, 4: 6}
        # 这个映射表示：年级1对应索引0-1，年级2对应索引2-3，年级3对应索引4-5，年级4对应索引6-7
        expected_idx_base = GRADE_TO_SEM_INDEX.get(gr, 0)
        expected_idx = expected_idx_base + (1 if course_term == "春" else 0)
        
        # 检查当前学期索引是否与期望索引匹配，或者相差2的倍数（不同年级的同一学期）
        # 例如：大一春季课程（索引1）应该在索引1, 3, 5, 7都开课
        # 索引模式：1, 3, 5, 7（都是奇数，且相差2）
        # 大二春季课程（索引3）应该在索引3, 5, 7都开课（但通常大二课程不会在大三、大四开）
        # 为了简化，我们让每个年级的课程只在对应年级开课，但允许跨年级重复
        # 实际上，公共必修课程（如EN102）应该只在索引1开课（大一春季），但为了支持不同年级的学生，
        # 我们需要在每个年级的对应学期都开课
        
        # 检查当前学期索引是否与期望索引匹配
        # 对于公共必修课程，应该在每个年级的对应学期都开课
        # 
        # SEMESTERS列表的结构（当 base_semester = "2025-2026-2" 时）：
        # - 索引0-1: 2025级的大一（2025-2026-1, 2025-2026-2）
        # - 索引2-3: 2024级的大一（2024-2025-1, 2024-2025-2）
        # - 索引4-5: 2023级的大一（2023-2024-1, 2023-2024-2）
        # - 索引6-7: 2022级的大一（2022-2023-1, 2022-2023-2）
        #
        # 注意：SEMESTERS列表实际上包含的是"每个年级的大一"学期，而不是"当前学期所在学年及其前3个学年"。
        # 这是因为系统需要为所有年级的学生生成选课数据，而每个年级的学生都需要在大一、大二、大三、大四选课。
        #
        # 所以，EN102（年级推荐=1，季节=春，期望索引=1）应该：
        # - 在索引1开课（2025级大一春）
        # - 在索引3开课（2024级大一春）
        # - 在索引5开课（2023级大一春）
        # - 在索引7开课（2022级大一春）
        #
        # 索引模式：期望索引=1（大一春），则索引1, 3, 5, 7都开课（都是奇数，且 >= 期望索引）
        # 期望索引=0（大一秋），则索引0, 2, 4, 6都开课（都是偶数，且 >= 期望索引）
        #
        # 所以，如果当前学期索引与期望索引的奇偶性相同，且索引 >= 期望索引，则开课
        should_offer = True
        if not should_offer:
            continue
        
        # 调试：记录关键课程的开课决策
        if cid in ["ML101", "PH101", "XL101", "EN101", "MA101", "PE101"]:
            Logger.debug(f"课程 {cid} 将在学期 {semester} 开课：年级推荐={gr}, 季节={course_term}, 期望索引={expected_idx}, 当前索引={sem_idx}")

        n_off = _calc_offering_count_by_attr(c, semester)
        if n_off <= 0:
            continue

        # 找授课老师（同学院）
        assigned_dept = resolve_teacher_dept(c)
        if assigned_dept not in teacher_by_dept:
            Logger.warning(f"{cid} 找不到该学院教师：{assigned_dept}")
            continue
        candidates = teacher_by_dept[assigned_dept]
        if not candidates:
            continue
        random.shuffle(candidates)

        for i in range(n_off):
            teacher = candidates[i % len(candidates)]
            teacher_id = teacher["teacher_id"]

            # 先插入开课记录（暂不填 class_time/classroom）
            offering_id = db.insert_data("course_offerings", {
                "course_id": cid,
                "teacher_id": teacher_id,
                "semester": semester,
                "max_students": 120 if course_type == "公共必修" else 60,
                "status": "open",
                "department": dept,
                "class_time": None,
                "classroom": None,
            })
            if not offering_id:
                continue
            offering_ids.append(int(offering_id))

            # 分配助教（可选）
            try:
                assign_tas_for_offering(db, offering_id, teacher_id, cid)
            except Exception as e:
                Logger.debug(f"为开课 {offering_id} 分配助教失败：{e}")

            # ==== 连续节次排课 ====
            weekly_sessions_needed = int(credits)
            if weekly_sessions_needed <= 0:
                Logger.debug(f"课程 {cid} 学分为 0，跳过排课。")
                db.execute_update(
                    "UPDATE course_offerings SET class_time=?, classroom=?, status='pending' WHERE offering_id=?",
                    ("未排课", None, offering_id)
                )
                continue

            valid_rooms = find_valid_rooms(course_type, cid, is_public)
            if not valid_rooms:
                Logger.warning(f"课程 {cid} 找不到可用教室，排课失败。")
                db.execute_update(
                    "UPDATE course_offerings SET class_time=?, classroom=?, status='pending' WHERE offering_id=?",
                    ("未排课", None, offering_id)
                )
                continue

            assigned_sessions = assign_continuous_block(
                teacher_id=teacher_id,
                needed=weekly_sessions_needed,
                is_public=is_public,
                valid_rooms=valid_rooms,
                course_id=cid  # 传递课程ID用于公选课区分
            )

            if assigned_sessions:
                # 写入 offering_sessions
                for slot_id, room_id, room_name in assigned_sessions:
                    db.execute_update(
                        "INSERT OR IGNORE INTO offering_sessions(offering_id, slot_id, classroom_id) VALUES(?,?,?)",
                        (offering_id, slot_id, room_id)
                    )
                # 构造 “周X1-2节” 这样的字符串
                assigned_slot_ids = [s[0] for s in assigned_sessions]
                room_name = assigned_sessions[0][2]
                session_str = _build_session_string(db, assigned_slot_ids, room_name)

                db.execute_update(
                    "UPDATE course_offerings SET class_time=?, classroom=? WHERE offering_id=?",
                    (session_str, room_name, offering_id)
                )
            else:
                Logger.warning(f"课程 {cid} 在学期 {semester} 排课失败（没有连续 {weekly_sessions_needed} 节可用时段）。")
                db.execute_update(
                    "UPDATE course_offerings SET class_time=?, classroom=?, status='pending' WHERE offering_id=?",
                    ("未排课", None, offering_id)
                )

    Logger.info(f"✅ 连续节次排课：学期 {semester} 共生成 {len(offering_ids)} 个开课班级。")
    return offering_ids


# 全局变量，用于缓存 time_slots 详情
_TIMESLOT_CACHE: Optional[Dict[int, Dict]] = None

def _get_timeslot_details(db: DBAdapter) -> Dict[int, Dict]:
    """从数据库加载 time_slots 详情并缓存"""
    global _TIMESLOT_CACHE
    if _TIMESLOT_CACHE is None:
        slots = db.execute_query("SELECT slot_id, day_of_week, starts_at, ends_at, section_no FROM time_slots")
        _TIMESLOT_CACHE = {s['slot_id']: s for s in slots}
    return _TIMESLOT_CACHE


def _build_session_string(db: DBAdapter, assigned_slots: List[int], classroom_name: str) -> str:
    """
    根据分配的 slot_id 列表，生成前端所需的简化的节次文本格式（例如：周一1-2节, 周三5-6节）。
    """
    # 获取节次详情
    slot_details = _get_timeslot_details(db) 
    
    # 将分配到的 slot_id 映射到 (day, section_no)
    day_section_map: Dict[int, List[int]] = {} # key: day_of_week, value: [section_no]
    
    for slot_id in assigned_slots:
        details = slot_details.get(slot_id)
        if details:
            day = details['day_of_week']
            section = details['section_no']
            day_section_map.setdefault(day, []).append(section)

    result_parts = []
    day_map = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五"}
    
    for day in sorted(day_section_map.keys()):
        sections = sorted(day_section_map[day])
        
        # 聚合连续的节次 (例如：[1, 2, 5, 6] -> '1-2节', '5-6节')
        
        # 找出连续范围的起始和结束
        ranges = []
        if sections:
            start = sections[0]
            end = sections[0]
            for i in range(1, len(sections)):
                if sections[i] == end + 1:
                    end = sections[i]
                else:
                    ranges.append((start, end))
                    start = sections[i]
                    end = sections[i]
            ranges.append((start, end)) # 添加最后一个范围

        day_text = day_map.get(day, f"周{day}")
        
        for start_sec, end_sec in ranges:
            if start_sec == end_sec:
                # 单节课，例如 周一1节
                result_parts.append(f"{day_text}{start_sec}节")
            else:
                # 连续多节课，例如 周一1-2节
                result_parts.append(f"{day_text}{start_sec}-{end_sec}节")
                
    # 使用英文逗号分隔，这是前端最常见的解析格式
    return ", ".join(result_parts)


def _get_academic_year(student_grade: int, semester: str) -> int:
    """
    根据入学年份 + 学期推导学生当前是大几：
    
    学期与年级对应关系：
    - 2022级（2022年入学）：
      * 大一：2022-2023-1, 2022-2023-2
      * 大二：2023-2024-1, 2023-2024-2
      * 大三：2024-2025-1, 2024-2025-2
      * 大四：2025-2026-1, 2025-2026-2
    - 2023级（2023年入学）：
      * 大一：2023-2024-1, 2023-2024-2
      * 大二：2024-2025-1, 2024-2025-2
      * 大三：2025-2026-1, 2025-2026-2
      * 大四：2026-2027-1, 2026-2027-2
    - 2024级、2025级以此类推
    
    例如：semester='2024-2025-2'
        2022级 -> 大三（year = (2024-2022)+1 = 3）
        2023级 -> 大二（year = (2024-2023)+1 = 2）
        2024级 -> 大一（year = (2024-2024)+1 = 1）
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
        year = 1  # 还未入学，按大一处理（实际上不应该选课）
    if year > 4:
        year = 4  # 已毕业，按大四处理
    return year


def enroll_students(db: DBAdapter, semester: str = "2024-2025-2", max_public_electives_per_student: int = 2):
    """
    新版选课逻辑：
    - 每个学生只从【本专业必修 + 公共基础课 + 公选课】中选
    - 只把“合格成绩(>=60 或 A~D)”视为已修
    - ✅ 所有课程选课时都做时间冲突检查，保证学生个人课表无冲突
    - ✅ 公共必修按推荐年级分配，不会出现大三还在修《大学英语1》的情况
    """

    # 1. 预取学生、专业、课程、开课信息
    students = db.execute_query("SELECT student_id, grade, major FROM students")
    if not students:
        Logger.warning("没有学生数据，跳过选课")
        return

    # 1.1 只将“合格”成绩的课程视为已修 (防止历史重复选课问题)
    qualified_grades = db.execute_query("""
        SELECT e.student_id, o.course_id
        FROM enrollments e
        JOIN course_offerings o ON e.offering_id = o.offering_id
        LEFT JOIN grades g ON e.enrollment_id = g.enrollment_id
        -- 筛选合格成绩：分数 >= 60 或等级为 A~D
        WHERE g.score >= 60 OR g.grade_level IN ('A', 'B', 'C', 'D')
    """)
    # 集合中只包含合格的 (sid, cid) 对
    taken_courses = {(row["student_id"], row["course_id"]) for row in qualified_grades}

    # 预取专业列表
    majors = db.execute_query("SELECT major_id, name, college_code FROM majors")
    if not majors:
        Logger.warning("没有专业数据，跳过选课")
        return

    # 专业名 -> major_id 映射
    major_name_to_id = {m["name"]: m["major_id"] for m in majors}

    # 课程开课（本学期，且已经排好课的）
    offerings = db.execute_query(
        "SELECT offering_id, course_id, max_students, "
        "COALESCE(current_students, 0) AS current_students "
        "FROM course_offerings "
        "WHERE semester=? "
        "  AND class_time IS NOT NULL "
        "  AND class_time <> '未排课' "
        "  AND status = 'open'",
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

    # 🎯 辅助函数：获取一个 offering 的所有 slot_id
    def get_offering_slots(oid: int) -> Set[int]:
        slots = db.execute_query(
            "SELECT slot_id FROM offering_sessions WHERE offering_id=?",
            (oid,)
        )
        return {s["slot_id"] for s in slots}

    # 辅助函数：检查新课程是否与已选课程时间冲突
    def check_conflict(new_offering_slots: Set[int], existing_slots: Set[int]) -> bool:
        """有交集返回 True = 冲突"""
        return bool(new_offering_slots.intersection(existing_slots))

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

    # 统计信息：记录每个年级有多少学生参与选课
    grade_counts = {2022: 0, 2023: 0, 2024: 0, 2025: 0}
    skipped_early = 0  # 未入学的学生数
    skipped_graduated = 0  # 已毕业的学生数
    
    # 2. 逐个学生进行选课
    for s in students:
        sid = s["student_id"]
        grade = int(s["grade"])
        major_name = s["major"]

        mid = major_name_to_id.get(major_name)
        if not mid:
            continue

        # 当前学期，这个年级是大几（1~4）
        # 计算学生在当前学期应该是大几
        try:
            start_year = int(semester.split("-")[0])
        except Exception:
            continue  # 学期格式错误，跳过该学生
        
        diff = start_year - grade
        academic_year = diff + 1
        
        # 如果学生还未入学（academic_year < 1）或已毕业（academic_year > 4），跳过选课
        if academic_year < 1:
            skipped_early += 1
            continue  # 学生还未入学，不应该选课
        if academic_year > 4:
            skipped_graduated += 1
            continue  # 学生已毕业，不应该选课
        
        # 记录参与选课的学生年级
        if grade in grade_counts:
            grade_counts[grade] += 1
        
        # 判断当前学期是秋季还是春季
        sem_idx = semester.split("-")[-1]  # "1" or "2"
        is_autumn = (sem_idx == "1")
        current_term = "秋" if is_autumn else "春"

        # 🎯 获取该学生当前学期所有已选 slot_id (用于时间冲突检查)
        current_enrollments = db.execute_query("""
            SELECT os.slot_id
            FROM enrollments e
            JOIN course_offerings o ON e.offering_id = o.offering_id
            JOIN offering_sessions os ON o.offering_id = os.offering_id
            WHERE e.student_id = ? AND e.semester = ?
        """, (sid, semester))

        current_slots: Set[int] = {row["slot_id"] for row in current_enrollments}

        # 2.1 确定 required_courses, public_elective_courses
        # 优先使用 curriculum_matrix 表（包含学期信息），如果没有则回退到 program_courses
        required_courses: List[str] = []
        public_elective_courses: List[str] = []
        
        # 首先尝试从 curriculum_matrix 获取必修课程（包含学期匹配）
        curriculum_rows = db.execute_query("""
            SELECT DISTINCT cm.course_id 
            FROM curriculum_matrix cm
            WHERE cm.major_id = ? 
            AND cm.category = '必修'
            AND cm.grade = ?
            AND cm.term = ?
        """, (mid, academic_year, current_term))
        
        if curriculum_rows:
            # 使用 curriculum_matrix 的结果
            required_courses = [row["course_id"] for row in curriculum_rows]
            Logger.debug(f"学生 {sid} 学期 {semester} 从 curriculum_matrix 获取 {len(required_courses)} 门必修课程")
        else:
            # 回退到 program_courses，但需要手动判断学期
            pc_list = programs_by_major.get(mid, [])
            
            # 判断课程应该在哪一学期（秋/春）的函数
            def get_course_term(cid: str) -> str:
                """判断课程应该在哪一学期（秋/春）"""
                # 大学英语系列：EN101(秋), EN102(春), EN103(秋), EN104(春)
                if cid.startswith('EN10'):
                    last_digit = int(cid[-1])
                    return '春' if last_digit % 2 == 0 else '秋'
                
                # 大学体育系列：PE101(秋), PE102(春), PE103(秋), PE104(春)
                if cid.startswith('PE10'):
                    last_digit = int(cid[-1])
                    return '春' if last_digit % 2 == 0 else '秋'
                
                # 其他课程：尾号2是春季课，其他是秋季课
                return '春' if cid.endswith('2') and len(cid) == 5 else '秋'
            
            for row in pc_list:
                cid = row["course_id"]
                cat = row["course_category"]              # 必修 / 选修
                rec_year = row["grade_recommendation"]    # 推荐年级 (1~4)
                ctype = row["course_type"]                # 公共必修 / 专业必修 / 通识选修 等
                is_pub_elect = row.get("is_public_elective", 0)

                # ✅ 公共必修：只在推荐年级那一年算作必修，且学期匹配
                #    例如 EN101 推荐年级=1 → 只给大一秋季当必修；EN102 推荐年级=1 → 只给大一春季当必修
                if ctype == "公共必修":
                    if cat == "必修" and rec_year == academic_year:
                        course_term = get_course_term(cid)
                        if course_term == current_term:
                            required_courses.append(cid)
                    continue

                # ✅ 专业课等：推荐年级 == 当前年级，且是"必修"，且学期匹配
                if cat == "必修" and rec_year == academic_year:
                    course_term = get_course_term(cid)
                    if course_term == current_term:
                        required_courses.append(cid)
                    continue

                # ✅ 公选 / 通识选修：只放到"可选公选课池"，后面按数量随机选
                if is_pub_elect == 1:
                    public_elective_courses.append(cid)

        # 去重
        required_courses = list(dict.fromkeys(required_courses))
        public_elective_courses = list(dict.fromkeys(public_elective_courses))

        # 组装本学期“打算给这个学生修的课程列表”
        to_take_courses: List[str] = list(required_courses)

        # 公选课按上限加几门
        if public_elective_courses and max_public_electives_per_student > 0:
            k = min(max_public_electives_per_student, len(public_elective_courses))
            extra = random.sample(public_elective_courses, k=k)
            to_take_courses.extend(extra)

        # 过滤掉“已经合格修过”的课程
        to_take_courses = [
            cid for cid in to_take_courses
            if (sid, cid) not in taken_courses
        ]
        to_take_courses = list(dict.fromkeys(to_take_courses))

        # 2.2 把 “课程ID” 映射成 “开课实例 offering_id”，并写入 enrollments
        # 区分必修课程和选修课程，必修课程必须被选上
        required_course_set = set(required_courses)
        
        for cid in to_take_courses:
            is_required = cid in required_course_set

            # 🎯 嵌套函数：给某个课程挑一个不冲突、有余量的开课实例
            # 对于必修课程，如果都冲突则选择冲突最少的
            def pick_non_conflicting_offering(cid: str, is_required: bool) -> Optional[int]:
                offs = offerings_by_course.get(cid, [])
                
                # 如果没有开课实例，记录详细信息
                if not offs:
                    Logger.warning(f"学生 {sid} 的{'必修' if is_required else '选修'}课程 {cid} 在本学期没有开课实例")
                    return None
                
                random.shuffle(offs)

                best_offering = None
                min_conflict_count = float('inf')
                all_full = True  # 标记是否所有开课实例都满员

                for o in offs:
                    oid = o["offering_id"]
                    cap = o.get("max_students") or 60
                    cur = offering_current_counts.get(oid, 0)

                    # 已满员，跳过
                    if cur >= cap:
                        continue
                    
                    all_full = False  # 至少有一个未满员

                    # 取出该开课实例的所有节次
                    new_slots = get_offering_slots(oid)

                    # 计算冲突数量
                    conflict_count = len(new_slots.intersection(current_slots))

                    # 如果没有冲突，直接返回
                    if conflict_count == 0:
                        return oid

                    # 如果有冲突，记录冲突最少的（用于必修课程）
                    if is_required and conflict_count < min_conflict_count:
                        min_conflict_count = conflict_count
                        best_offering = oid

                # 如果所有开课实例都满员
                if all_full:
                    Logger.warning(f"学生 {sid} 的{'必修' if is_required else '选修'}课程 {cid} 所有开课实例都已满员")
                    return None

                # 如果是必修课程且都冲突，返回冲突最少的
                if is_required and best_offering is not None:
                    Logger.warning(f"学生 {sid} 的必修课程 {cid} 所有开课实例都有时间冲突，选择冲突最少的 (offering {best_offering}, 冲突 {min_conflict_count} 个时间段)")
                    return best_offering

                # 选修课程如果有冲突则不选
                return None

            oid = pick_non_conflicting_offering(cid, is_required)

            if not oid:
                if is_required:
                    # 必修课程必须被选上，如果找不到则记录警告
                    Logger.warning(f"学生 {sid} 的必修课程 {cid} 无法选课：本学期该课程没开，或者都满员")
                # 无论是必修还是选修，如果找不到 offering_id，都应该跳过
                continue

            try:
                db.insert_data("enrollments", {
                    "student_id": sid,
                    "offering_id": oid,
                    "semester": semester
                })
                offering_current_counts[oid] = offering_current_counts.get(oid, 0) + 1

                # 🎯 选课成功后，将新课程的 slot_id 加入当前学生的 current_slots 集合
                new_slots = get_offering_slots(oid)
                current_slots.update(new_slots)

            except Exception as e:
                # 如果数据库触发器阻止了，会在这里报错
                Logger.warning(f"学生 {sid} 选课 {cid} (offering {oid}) 失败: {e}")

    # 3. 最后统一刷新 course_offerings.current_students
    try:
        db.execute_update(
            "UPDATE course_offerings SET current_students = "
            "(SELECT COUNT(*) FROM enrollments WHERE enrollments.offering_id = course_offerings.offering_id)"
        )
    except Exception as e:
        Logger.warning(f"更新 course_offerings.current_students 失败: {e}")

    # 输出统计信息
    active_grades = [g for g, count in grade_counts.items() if count > 0]
    Logger.info("✅ 新版选课逻辑执行完成：按专业+年级+公共课/公选课分配，且学生课表无时间冲突。")
    Logger.info(f"   学期 {semester} 选课统计：")
    if active_grades:
        Logger.info(f"   - 参与选课的年级：{', '.join([f'{g}级({grade_counts[g]}人)' for g in active_grades])}")
    else:
        Logger.warning(f"   - ⚠️ 警告：本学期没有任何学生参与选课！")
    if skipped_early > 0:
        Logger.debug(f"   - 跳过未入学学生：{skipped_early}人")
    if skipped_graduated > 0:
        Logger.debug(f"   - 跳过已毕业学生：{skipped_graduated}人")


def assign_grades(db: DBAdapter):
    """
    生成成绩，成绩分布：
    - 大部分学生的大部分成绩在 85~95 之间（约70-80%）
    - 少部分学生的部分成绩在 60~85 之间（约15-20%）
    - 少部分学生的部分成绩在 95~100 之间（约5-10%）
    
    实现方式：按学生分组，为每个学生生成成绩时，确保大部分成绩在85~95之间
    """
    enrolls = db.execute_query("SELECT enrollment_id, student_id, offering_id FROM enrollments")
    
    # 按学生分组
    enrollments_by_student = {}
    for e in enrolls:
        student_id = e["student_id"]
        if student_id not in enrollments_by_student:
            enrollments_by_student[student_id] = []
        enrollments_by_student[student_id].append(e)
    
    # 为每个学生生成成绩
    for student_id, student_enrolls in enrollments_by_student.items():
        total_courses = len(student_enrolls)
        
        # 计算每个区间应该有多少门课程
        # 大部分（70-80%）在85~95之间
        main_count = int(total_courses * random.uniform(0.7, 0.8))
        # 少部分（15-20%）在60~85之间
        low_count = int(total_courses * random.uniform(0.15, 0.2))
        # 剩余的在95~100之间
        high_count = total_courses - main_count - low_count
        
        # 打乱顺序，随机分配
        random.shuffle(student_enrolls)
        
        for i, e in enumerate(student_enrolls):
            if i < main_count:
                # 大部分成绩在 85~95 之间
                score = round(random.uniform(85, 95), 1)
            elif i < main_count + low_count:
                # 少部分成绩在 60~85 之间
                score = round(random.uniform(60, 85), 1)
            else:
                # 剩余成绩在 95~100 之间
                score = round(random.uniform(95, 100), 1)
            
            # 根据分数计算等级和GPA
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
    """
    为公选课绑定晚上时间段（13-14节）
    注意：这个函数现在主要用于补充绑定，因为 create_offerings 已经会为公选课排课
    但如果 create_offerings 中排课失败，这里会尝试补充绑定
    """
    try:
        # 查本学期所有公选课的 offering_id（只处理未排课的）
        offs = db.execute_query(
            "SELECT o.offering_id, o.course_id FROM course_offerings o "
            "JOIN courses c ON c.course_id=o.course_id "
            "WHERE c.is_public_elective=1 AND o.semester=? "
            "AND (o.class_time IS NULL OR o.class_time='未排课')",
            (semester,)
        )
        if not offs:
            return

        # 获取所有晚上时间段（13-14节）
        # 注意：每个公选课需要连续2节，所以只能使用13-14节
        # 周一13-14, 周二13-14, 周三13-14, 周四13-14, 周五13-14
        # 总共 5天 * 1种组合 = 5个时间段组合
        evening_slots = db.execute_query(
            "SELECT slot_id, day_of_week, section_no FROM time_slots "
            "WHERE session='EVENING' AND section_no IN (13, 14) "
            "ORDER BY day_of_week, section_no"
        )
        
        if not evening_slots:
            Logger.warning(f"未找到晚上时间段（13-14节），无法为公选课排课")
            return
        
        # 获取可用教室
        rooms = db.execute_query(
            "SELECT classroom_id, name FROM classrooms "
            "WHERE room_type IN ('报告厅', '普通教室', '智慧教室') "
            "ORDER BY classroom_id"
        )
        
        if not rooms:
            Logger.warning(f"未找到可用教室，无法为公选课排课")
            return

        # 为每个公选课分配不同的时间段
        # 使用 (day, start_section, room_id) 来标识一个时间段组合（允许同一时间段在不同教室开课）
        # 例如：(1, 12, room_1) 表示周一12-13节在教室1, (1, 12, room_2) 表示周一12-13节在教室2
        used_combinations: Set[Tuple[int, int, int]] = set()  # (day, start_section, room_id)
        
        for idx, o in enumerate(offs):
            oid = o['offering_id']
            cid = o['course_id']
            
            # 获取该公选课的学分，确定需要几节课
            course_info = db.execute_query(
                "SELECT credits FROM courses WHERE course_id=?", (cid,)
            )
            credits = course_info[0]['credits'] if course_info else 2.0
            needed_sessions = int(credits)  # 通常公选课是2学分，需要2节课
            
            # 为这个公选课找一个未使用的连续时间段组合
            assigned = False
            
            # 公选课只能使用13-14节（连续2节）
            for start_section in [13]:
                if start_section + needed_sessions - 1 > 14:
                    continue  # 超出14节，跳过
                
                # 尝试所有5天
                for day in range(1, 6):
                    # 获取这一天的对应slot
                    day_slots = [s for s in evening_slots 
                               if s['day_of_week'] == day 
                               and s['section_no'] >= start_section 
                               and s['section_no'] < start_section + needed_sessions]
                    
                    if len(day_slots) != needed_sessions:
                        continue
                    
                    # 找一个可用教室（检查所有需要的slot）
                    for room in rooms:
                        room_id = room['classroom_id']
                        
                        # 检查这个时间段+教室组合是否已被使用（允许同一时间段在不同教室开课）
                        if (day, start_section, room_id) in used_combinations:
                            continue
                        
                        # 检查这个教室在所有需要的slot上是否都被占用
                        all_available = True
                        for slot in day_slots:
                            conflict = db.execute_query(
                                "SELECT 1 FROM offering_sessions os "
                                "JOIN course_offerings o2 ON os.offering_id = o2.offering_id "
                                "WHERE os.slot_id=? AND os.classroom_id=? AND o2.semester=?",
                                (slot['slot_id'], room_id, semester)
                            )
                            if conflict:
                                all_available = False
                                break
                        
                        if not all_available:
                            continue
                        
                        # 找到可用时间段和教室，插入所有需要的slot
                        try:
                            slot_ids = [s['slot_id'] for s in day_slots]
                            for slot_id in slot_ids:
                                db.execute_update(
                                    "INSERT OR IGNORE INTO offering_sessions(offering_id,slot_id,classroom_id) VALUES(?,?,?)",
                                    (oid, slot_id, room_id)
                                )
                            
                            # 生成时间字符串
                            session_str = _build_session_string(db, slot_ids, room['name'])
                            
                            # 更新 course_offerings
                            db.execute_update(
                                "UPDATE course_offerings SET class_time=?, classroom=?, status='open' WHERE offering_id=?",
                                (session_str, room['name'], oid)
                            )
                            
                            used_combinations.add((day, start_section, room_id))
                            assigned = True
                            break
                        
                        except Exception as e:
                            Logger.warning(f"为公选课 {cid} 绑定时间段失败: {e}")
                            continue
                    
                    if assigned:
                        break
                
                if assigned:
                    break
            
            if not assigned:
                Logger.warning(f"公选课 {cid} (offering {oid}) 无法找到可用的晚上时间段")
                
    except Exception as e:
        Logger.warning(f"bind_evening_public_offerings 执行失败: {e}")


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


def seed_classrooms(db: DBAdapter):
    """
    向数据库 classrooms 表插入全部教学楼的所有教室（一个不少）
    """

    classrooms = []

    # 教三：201–250（增加教室数量以解决排课资源不足）
    for room_no in range(201, 251):
        classrooms.append({
            "name": f"教三-{room_no}",
            "location_type": "3",
            "seat_count": 64,
            "room_type": "普通教室",
            "available_equipment": None
        })

    # 教二：101–150（增加教室数量以解决排课资源不足）
    for room_no in range(101, 151):
        classrooms.append({
            "name": f"教二-{room_no}",
            "location_type": "2",
            "seat_count": 64,
            "room_type": "普通教室",
            "available_equipment": None
        })
    
    # 教一：101–120（新增教学楼）
    for room_no in range(101, 121):
        classrooms.append({
            "name": f"教一-{room_no}",
            "location_type": "1",
            "seat_count": 64,
            "room_type": "普通教室",
            "available_equipment": None
        })
    
    # 智慧教室：增加更多智慧教室
    for i in range(1, 21):
        classrooms.append({
            "name": f"智慧教室-{i}",
            "location_type": "主",
            "seat_count": 80,
            "room_type": "智慧教室",
            "available_equipment": "智能黑板"
        })

    # 机房 1–10（增加机房数量）
    for i in range(1, 11):
        classrooms.append({
            "name": f"机房-{i}",
            "location_type": "实验楼",
            "seat_count": 80,
            "room_type": "机房",
            "available_equipment": "电脑"
        })

    # 报告厅 1–5（增加报告厅数量）
    for i in range(1, 6):
        classrooms.append({
            "name": f"报告厅-{i}",
            "location_type": "主",
            "seat_count": 128,
            "room_type": "报告厅",
            "available_equipment": "LED大屏"
        })

    # 体育馆
    classrooms.append({
        "name": "体-馆-1",
        "location_type": "体育馆",
        "seat_count": 64,
        "room_type": "体育馆",
        "available_equipment": None
    })

    # === 插入数据库 ===
    for room in classrooms:
        try:
            db.execute_update(
                "INSERT OR IGNORE INTO classrooms(name, location_type, seat_count, room_type, available_equipment) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    room["name"],
                    room["location_type"],
                    room["seat_count"],
                    room["room_type"],
                    room["available_equipment"]
                )
            )
        except Exception as e:
            Logger.warning(f"插入教室失败: {room['name']} - {e}")


def seed_timeslots(db: DBAdapter):
    """
    根据学校精确时间要求生成 time_slots (14节)。
    """
    from datetime import datetime, timedelta
    
    def time_add(start_time: str, minutes: int) -> str:
        t = datetime.strptime(start_time, "%H:%M")
        t += timedelta(minutes=minutes)
        return t.strftime("%H:%M")

    # [节次号, 时长(min), 后续break(min), Session类型, 每天的起始时间]
    # 我们根据您的描述重新构造精确时间表：
    TIME_SCHEDULE_DEFINITIONS = [
        # AM:
        (1, 45, '08:00', 5, 'AM'),    # 8:00-8:45, break 5min -> next 8:50
        (2, 45, '08:50', 15, 'AM'),   # 8:50-9:35, break 15min -> next 9:50 (长课间)
        (3, 45, '09:50', 5, 'AM'),    # 9:50-10:35, break 5min -> next 10:40
        (4, 45, '10:40', 5, 'AM'),   # 10:40-11:25, break 5min -> next 11:30
        (5, 45, '11:30', 45, 'AM'),   # 11:30-12:15, break 45min (午休) -> next 13:00

        # PM:
        (6, 45, '13:00', 5, 'PM'),    # 13:00-13:45, break 5min -> next 13:50
        (7, 45, '13:50', 10, 'PM'),   # 13:50-14:35, break 10min (长课间) -> next 14:45
        (8, 45, '14:45', 10, 'PM'),   # 14:45-15:30, break 10min -> next 15:40
        (9, 45, '15:40', 10, 'PM'),   # 15:40-16:25, break 10min -> next 16:35
        (10, 45, '16:35', 5, 'PM'),  # 16:35-17:20, break 5min -> next 17:25
        (11, 45, '17:25', 20, 'PM'), # 17:25-18:10, break 20min (晚饭) -> next 18:30
        
        # EVENING:
        (12, 45, '18:30', 5, 'EVENING'), # 18:30-19:15, break 5min -> next 19:20
        (13, 45, '19:20', 5, 'EVENING'), # 19:20-20:05, break 5min -> next 20:10
        (14, 45, '20:10', 0, 'EVENING'), # 20:10-20:55, 结束
    ]
    
    slots_to_add = []
    
    # 重新计算起始时间，确保精确匹配您的描述
    # 由于您的描述中包含了明确的起始时间，我们使用定义的时间
    
    for section_no, duration, start_time, break_duration, session in TIME_SCHEDULE_DEFINITIONS:
        end_time = time_add(start_time, duration)
        
        slots_to_add.append({
            'section_no': section_no,
            'starts_at': start_time,
            'ends_at': end_time,
            'session': session
        })

    # 插入数据库 (周一到周五)
    for d in range(1, 6):
        for slot_data in slots_to_add:
            try:
                db.execute_update(
                    "INSERT INTO time_slots(day_of_week,section_no,starts_at,ends_at,session) VALUES(?,?,?,?,?)",
                    (d, slot_data['section_no'], slot_data['starts_at'], slot_data['ends_at'], slot_data['session'])
                )
            except Exception:
                pass


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

    # ===== 1) 全校通用课程按年级推荐 =====
    GLOBAL_COURSE_MAP = {
        # 公共必修：严格限定在大一/大二
        "PUBLIC_REQUIRED": [
            # --- 大一必修 ---
            ("MA101", 1),
            ("MA102", 1),
            ("MA201", 1),   # ✅ 线性代数必须是大一
            ("PH101", 1),
            ("PH102", 1),
            ("EN101", 1),
            ("EN102", 1),
            ("PE101", 1),
            ("PE102", 1),
            ("ZX101", 1),
            ("ML101", 1),
            ("XL101", 1),
            ("YW101", 1),

            # --- 大二必修 ---
            ("MA202", 2),   # 概统放大二
            ("EN103", 2),
            ("EN104", 2),
            ("PE103", 2),
            ("PE104", 2),
            ("HX101", 2),
            ("ZX102", 2),
            ("ZX103", 2),
        ],

        # 信息/通信类基础：大二~大三
        "INFO_CORE_REQUIRED": [
            ("CM201", 2),
            ("CM202", 2),
            ("CM203", 2),
            ("CM204", 2),
            ("CM205", 2),
            ("CM206", 3),
            ("CM207", 3),
            ("CM208", 3),
            ("CM209", 3),
            ("CM210", 3),
        ],

        # 通识/公选：所有年级都可以选（grade_recommendation 设为 NULL）
        "GENERAL_ELECTIVE": [
            # 所有公共选修课对所有年级开放
            ("GE101", None), ("GE102", None), ("GE103", None), ("GE104", None),
            ("GE105", None), ("GE106", None), ("GE107", None),
            ("GE108", None), ("GE109", None), ("GE110", None), ("GE111", None),
            ("GE112", None), ("GE113", None), ("GE114", None), ("GE115", None),
            ("GE116", None), ("GE117", None), ("GE118", None), ("GE119", None),
            ("GE120", None), ("GE121", None), ("GE122", None), ("GE123", None),
            ("GE124", None), ("GE125", None),
            ("AI310", None),
            ("CS410", None),
            ("EE410", None),
            ("TC410", None),
            ("SC410", None),
        ],
    }

    # ===== 2) 学院专业课按成长顺序（2->3->4） =====
    COLLEGE_SPECIALTY_MAP = {
        # 计算机学院
        "2021001": [
            # 大二必修
            ("CS201", 2, '必修'),
            ("CS202", 2, '必修'),
            # 大二选修
            ("CS203", 2, '选修'),
            ("CS204", 2, '选修'),
            ("CS205", 2, '选修'),
            # 大三主干必修
            ("CS301", 3, '必修'),
            ("CS302", 3, '必修'),
            ("CS303", 3, '必修'),
            ("CS304", 3, '必修'),
            ("SE402", 3, '必修'),
            # 大三选修
            ("CS305", 3, '选修'),
            ("CS306", 3, '选修'),
            ("CS307", 3, '选修'),
            ("CS308", 3, '选修'),
            ("CS309", 3, '选修'),
            ("CS310", 3, '选修'),
            # 大四方向/实践/选修
            ("SE401", 4, '必修'),
            ("SE403", 4, '选修'),
            ("CS401", 4, '选修'),
            ("CS402", 4, '选修'),
            ("CS403", 4, '选修'),
            ("CS404", 4, '选修'),
            ("CS405", 4, '选修'),
            ("SE404", 4, '选修'),
        ],

        # 信息与通信工程学院
        "2021002": [
            # 大二基础
            ("TC201", 2, '必修'),
            ("TC202", 2, '必修'),
            ("TC203", 2, '必修'),
            # 大二选修
            ("TC204", 2, '选修'),
            ("TC205", 2, '选修'),
            # 大三主干
            ("TC301", 3, '必修'),
            ("TC302", 3, '必修'),
            ("TC303", 3, '必修'),
            # 大三选修
            ("TC304", 3, '选修'),
            ("TC305", 3, '选修'),
            ("TC306", 3, '选修'),
            # 大四高阶/方向
            ("TC401", 4, '必修'),
            ("TC402", 4, '选修'),
            ("TC403", 4, '选修'),
            ("TC404", 4, '选修'),
            ("TC405", 4, '选修'),
        ],

        # 网络空间安全学院
        "2021003": [
            # 大二基础
            ("SC201", 2, '必修'),
            ("SC202", 2, '必修'),
            # 大二选修
            ("SC203", 2, '选修'),
            ("SC204", 2, '选修'),
            # 大三主干
            ("SC301", 3, '必修'),
            # 大三选修
            ("SC302", 3, '选修'),
            ("SC303", 3, '选修'),
            ("SC304", 3, '选修'),
            ("SC305", 3, '选修'),
            ("SC306", 3, '选修'),
            # 大四高阶/实践
            ("SC401", 4, '必修'),
            ("SC402", 4, '选修'),
            ("SC403", 4, '选修'),
            ("SC404", 4, '选修'),
        ],

        # 电子工程学院
        "2021004": [
            # 大二基础
            ("EE201", 2, '必修'),
            ("EE202", 2, '必修'),
            ("EE203", 2, '必修'),
            # 大二选修
            ("EE204", 2, '选修'),
            ("EE205", 2, '选修'),
            # 大三主干
            ("EE301", 3, '必修'),
            ("EE302", 3, '必修'),
            ("EE303", 3, '必修'),
            # 大三选修
            ("EE304", 3, '选修'),
            ("EE305", 3, '选修'),
            ("EE306", 3, '选修'),
            # 大四方向
            ("EE401", 4, '选修'),
            ("EE402", 4, '选修'),
            ("EE403", 4, '选修'),
            ("EE404", 4, '选修'),
        ],

        # 现代邮政学院
        "2021005": [
            # 大二基础
            ("MP201", 2, '必修'),
            ("MP202", 2, '必修'),

            # 大三主干
            ("MP301", 3, '必修'),
            ("MP302", 3, '必修'),
            ("MP303", 3, '选修'),

            # 大四方向
            ("MP401", 4, '选修'),
            ("MP402", 4, '选修'),
        ],

        # 人工智能学院（按你要求修正）
        "2021006": [
            # 大一导论
            ("AI201", 1, '必修'),

            # 大二基础
            ("AI202", 2, '必修'),  # ✅ 关键：从大二选修改为大二必修
            ("CM204", 2, '必修'),  # 数据结构是 AI 学院合理前置
            # 大二选修
            ("AI203", 2, '选修'),
            ("AI204", 2, '选修'),

            # 大三主干
            ("AI301", 3, '必修'),
            ("AI302", 3, '必修'),
            # 大三选修
            ("AI303", 3, '选修'),
            ("AI304", 3, '选修'),
            ("AI305", 3, '选修'),
            ("AI306", 3, '选修'),

            # 大四方向/高阶
            ("AI401", 4, '必修'),
            # 大四选修
            ("AI402", 4, '选修'),
            ("AI403", 4, '选修'),
            ("AI404", 4, '选修'),

            # 共享计算机课程：只做大三选修
            ("CS301", 3, '选修'),
        ],

        # 国际学院：本科培养顺序
        "2021007": [
            ("IC201", 1, '必修'),
            ("CM201", 1, '必修'),
            ("CM202", 1, '必修'),

            ("IC202", 2, '必修'),
            ("CM204", 2, '必修'),

            ("CM209", 3, '必修'),
            ("IC301", 3, '选修'),
        ],
    }


    # ===== 3) 写入 program_courses =====
    for major in majors:
        mid = major['major_id']
        ccode = major['college_code']
        mname = major['name']

        # 3.1 公共必修（所有专业）
        for course_id, grade_rec in GLOBAL_COURSE_MAP["PUBLIC_REQUIRED"]:
            db.execute_update(
                "INSERT OR IGNORE INTO program_courses(major_id,course_id,course_category,grade_recommendation) "
                "VALUES(?,?,?,?)",
                (mid, course_id, '必修', grade_rec)
            )

        # 3.2 信息类核心基础（信息类学院）
        if ccode in ["2021001", "2021002", "2021003", "2021004", "2021006", "2021007"]:
            for course_id, grade_rec in GLOBAL_COURSE_MAP["INFO_CORE_REQUIRED"]:
                db.execute_update(
                    "INSERT OR IGNORE INTO program_courses(major_id,course_id,course_category,grade_recommendation) "
                    "VALUES(?,?,?,?)",
                    (mid, course_id, '必修', grade_rec)
                )

        # 3.3 学院专业课（按学院绑定）
        if ccode in COLLEGE_SPECIALTY_MAP:
            for course_id, grade_rec, category in COLLEGE_SPECIALTY_MAP[ccode]:

                current_category = category
                quota = 0

                # 软件工程专业微调：CS302 改选修
                if "软件工程" in mname and course_id == "CS302":
                    current_category = '选修'
                    quota = 10

                db.execute_update("""
                    INSERT OR IGNORE INTO program_courses(
                        major_id, course_id, course_category,
                        cross_major_quota, grade_recommendation
                    ) VALUES (?, ?, ?, ?, ?)
                """, (mid, course_id, current_category, quota, grade_rec))

        # 3.4 公选/通识（所有专业，所有年级都可以选）
        # grade_recommendation 为 None 表示所有年级都可以选
        for course_id, grade_rec in GLOBAL_COURSE_MAP["GENERAL_ELECTIVE"]:
            db.execute_update(
                "INSERT OR IGNORE INTO program_courses("
                "major_id,course_id,course_category,cross_major_quota,grade_recommendation"
                ") VALUES(?,?,?,?,?)",
                (mid, course_id, '公选', 50, grade_rec)  # 改为'公选'类别，grade_rec为None表示所有年级可选
            )

    Logger.info("✅ 培养方案 program_courses 生成完成（年级严格合理）。")


def seed_all(db: DBAdapter, students: int = 200, teachers: int = 10, semester: str = "2024-2025-2"):
    """
    主流程：初始化表 -> 插入学院/专业 -> 教师 -> 学生 -> 课程 -> 开课 -> 选课 -> 成绩
    
    注意：semester 参数仅用于确定起始年份，系统会为所有学期（4个年级 × 2个学期 = 8个学期）
    生成开课计划、选课和成绩数据。
    """
    # 允许重新生成：清空旧数据
    Logger.info("🔄 开始重新生成数据库，将清空旧数据...")
    try:
        # 清空所有相关表（按依赖顺序）
        db.execute_update("DELETE FROM grades")
        db.execute_update("DELETE FROM enrollments")
        db.execute_update("DELETE FROM offering_sessions")
        db.execute_update("DELETE FROM course_offerings")
        db.execute_update("DELETE FROM program_courses")
        db.execute_update("DELETE FROM curriculum_matrix")
        db.execute_update("DELETE FROM students")
        db.execute_update("DELETE FROM teachers")
        db.execute_update("DELETE FROM courses")
        Logger.info("✅ 已清空旧数据")
    except Exception as e:
        Logger.warning(f"清空旧数据时出现警告（可能表不存在）: {e}")
        pass

    # 1. 初始化数据库表结构（由 Database.init_tables() 统一创建）
    ensure_core_tables(db)
    upgrade_course_offerings_table(db)

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

    # 9. 写入课程矩阵到数据库
    seed_curriculum_matrix(db)

    # === 10~12. 自动生成四个年级的完整学年（秋季 + 春季） ===
    # 学期与年级对应关系说明：
    # 
    # 当 semester = "2025-2026-2" 时（start_year = 2025），生成的学期列表：
    #   * 大一：2025-2026-1, 2025-2026-2（2025级学生的大一）
    #   * 大二：2024-2025-1, 2024-2025-2（2024级学生的大二）
    #   * 大三：2023-2024-1, 2023-2024-2（2023级学生的大三）
    #   * 大四：2022-2023-1, 2022-2023-2（2022级学生的大四）
    # 
    # 这样会生成从 2022-2023-1 到 2025-2026-2 的所有8个学期。
    # 运行程序时，可以从这8个学期中任选其一进行查询。
    # 
    # 对于不同年级的学生，在同一个学期会有不同的年级（通过 _get_academic_year 计算）：
    #   - 在 2024-2025-2 学期：
    #     * 2024级学生 -> 大一（(2024-2024)+1 = 1）
    #     * 2023级学生 -> 大二（(2024-2023)+1 = 2）
    #     * 2022级学生 -> 大三（(2024-2022)+1 = 3）
    # 
    # 注意：这个逻辑生成的是"当前学期所在学年"及其前3个学年的学期。
    # 系统会为所有8个学期生成开课计划和选课数据，确保每个学期都有完整的选课记录。
    start_year = int(semester.split("-")[0])

    # SEMESTERS列表应该包含"每个年级的大一"学期，而不是"当前学期所在学年及其前3个学年"
    # 这样可以为所有年级的学生生成选课数据
    # 例如：当 base_semester = "2025-2026-2" 时，start_year = 2025
    # - 索引0-1: 2025级的大一（2025-2026-1, 2025-2026-2）
    # - 索引2-3: 2024级的大一（2024-2025-1, 2024-2025-2）
    # - 索引4-5: 2023级的大一（2023-2024-1, 2023-2024-2）
    # - 索引6-7: 2022级的大一（2022-2023-1, 2022-2023-2）
    SEMESTERS = [
        # 2025级的大一：秋+春
        f"{start_year}-{start_year+1}-1",
        f"{start_year}-{start_year+1}-2",

        # 2024级的大一：秋+春
        f"{start_year-1}-{start_year}-1",
        f"{start_year-1}-{start_year}-2",

        # 2023级的大一：秋+春
        f"{start_year-2}-{start_year-1}-1",
        f"{start_year-2}-{start_year-1}-2",

        # 2022级的大一：秋+春
        f"{start_year-3}-{start_year-2}-1",
        f"{start_year-3}-{start_year-2}-2",
    ]
    
    # === 10~12. 生成所有学期的开课计划，但只对指定学期进行选课和成绩分配 ===
    # 清空之前的 offering 、选课、成绩、排课
    db.execute_update("DELETE FROM offering_sessions")
    db.execute_update("DELETE FROM course_offerings")
    db.execute_update("DELETE FROM enrollments")
    db.execute_update("DELETE FROM grades")

    Logger.info(f"🟦 正在生成所有学期的开课计划...")
    
    # 为所有学期生成开课计划（但使用所有学期列表，让系统知道完整的学期结构）
    for sem in SEMESTERS:
        Logger.info(f"  生成学期 {sem} 的开课计划...")
        create_offerings(db, sem, SEMESTERS)
    
    Logger.info(f"✅ 所有学期的开课计划生成完成！")
    Logger.info(f"🟦 正在为所有学期生成选课和成绩数据...")

    # 为所有学期生成选课和成绩（保持时间冲突检查逻辑）
    for sem in SEMESTERS:
        Logger.info(f"  为学期 {sem} 生成选课数据...")
        enroll_students(db, sem)
        assign_grades(db)
        # 为每个学期的公选课绑定晚上时间段
        bind_evening_public_offerings(db, semester=sem)

    Logger.info(f"🎉 数据生成完毕！已为所有 {len(SEMESTERS)} 个学期生成开课计划、选课和成绩数据。")

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
                        "major_id": row.get("major_id") or None,        # ✅
                        "college_code": row.get("college_code") or None,# ✅
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


def export_csv_files(db: DBAdapter, students_file: str = None, teachers_file: str = None,courses_file: str = None,
                     mask_password: bool = False, exclude_password: bool = False):
    import csv
    from datetime import datetime

    students_file = students_file or str(data_dir / "students.csv")
    teachers_file = teachers_file or str(data_dir / "teachers.csv")
    courses_file  = courses_file  or str(data_dir / "course_offerings.csv")

    Logger.info(f"导出 CSV: students -> {students_file}, teachers -> {teachers_file} (mask={mask_password}, exclude={exclude_password})")

    try:
        students = db.execute_query("SELECT * FROM students ORDER BY student_id")
        if students:
            fieldnames = [
                "student_id","name","password","gender","birth_date",
                "major","major_id","college_code",   # ✅ 加在这里
                "grade","class_name","enrollment_date",
                "status","email","phone","created_at","updated_at"
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

        # -----------------------------------------
        # ✅ 导出开课计划 course_offerings.csv（单学期简化版）
        # -----------------------------------------
        courses = db.execute_query("""
            SELECT
                c.course_id,
                c.course_name,
                c.credits,
                c.hours,
                c.course_type,
                c.is_public_elective,
                c.credit_type,

                o.offering_id,
                o.department,
                o.class_time,
                o.classroom,
                o.max_students,
                COALESCE(o.current_students,0) AS current_students,
                o.status,

                o.teacher_id,
                t.name AS teacher_name,
                t.title AS teacher_title,
                t.department AS teacher_department,

                o.ta1_id,
                ta1.name AS ta1_name,
                o.ta2_id,
                ta2.name AS ta2_name

            FROM course_offerings o
            JOIN courses c ON c.course_id = o.course_id
            JOIN teachers t ON t.teacher_id = o.teacher_id
            LEFT JOIN teachers ta1 ON ta1.teacher_id = o.ta1_id
            LEFT JOIN teachers ta2 ON ta2.teacher_id = o.ta2_id
            ORDER BY c.course_id, o.offering_id
        """)

        if courses:
            course_fields = [
                "course_id", "course_name", "credits", "hours",
                "course_type", "is_public_elective", "credit_type",

                "offering_id", "department",
                "class_time", "classroom",
                "max_students", "current_students", "status",

                "teacher_id", "teacher_name", "teacher_title", "teacher_department",
                "ta1_id", "ta1_name",
                "ta2_id", "ta2_name",
            ]

            with open(courses_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=course_fields)
                writer.writeheader()
                for row in courses:
                    writer.writerow({k: row.get(k, "") for k in course_fields})

            Logger.info(f"✅ 开课计划已导出 -> {courses_file}")

    except Exception as e:
        Logger.error(f"导出 CSV 失败: {e}", exc_info=True)

def export_classrooms_csv(db: DBAdapter, filepath: str = "data/classrooms.csv"):
    """
    导出教室表到 CSV:
    字段：classroom_id, name, location_type, seat_count, room_type, available_equipment
    """
    import csv
    from pathlib import Path

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    rows = db.execute_query("""
        SELECT classroom_id, name, location_type, seat_count, room_type, available_equipment
        FROM classrooms
        ORDER BY classroom_id
    """)

    if not rows:
        Logger.warning("classrooms 表为空，导出为空 CSV")
    
    fieldnames = ["classroom_id", "name", "location_type", "seat_count", "room_type", "available_equipment"]
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

    Logger.info(f"✅ 教室表已导出 -> {filepath}")

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


def seed_curriculum_matrix(db: DBAdapter):
    """
    基于 program_courses，将课程矩阵数据写入 curriculum_matrix 表
    （替代 generate_curriculum_matrix 的文件导出功能）
    """
    rows = db.execute_query("""
        SELECT 
            pc.major_id, pc.course_id, pc.course_category, pc.grade_recommendation,
            m.name AS major_name, c.course_name, c.credits, c.course_type
        FROM program_courses pc
        JOIN majors m ON pc.major_id = m.major_id
        JOIN courses c ON pc.course_id = c.course_id
    """)

    # 映射关系：用于区分秋/春学期
    def get_term(cid: str) -> str:
        """
        判断课程应该在哪一学期（秋/春）
        规则：
        1. 大学英语和大学体育系列：奇数号（1,3）在秋季，偶数号（2,4）在春季
        2. 其他课程：尾号2是春季课，其他是秋季课
        """
        # 大学英语系列：EN101(秋), EN102(春), EN103(秋), EN104(春)
        if cid.startswith('EN10'):
            last_digit = int(cid[-1])
            return '春' if last_digit % 2 == 0 else '秋'
        
        # 大学体育系列：PE101(秋), PE102(春), PE103(秋), PE104(春)
        if cid.startswith('PE10'):
            last_digit = int(cid[-1])
            return '春' if last_digit % 2 == 0 else '秋'
        
        # 其他课程：尾号2是春季课，其他是秋季课
        return '春' if cid.endswith('2') and len(cid) == 5 else '秋'

    records = []
    for r in rows:
        cid = r["course_id"]
        term = get_term(cid)
        
        # 处理 grade_recommendation 可能为 NULL 的情况（公共选修课）
        grade_rec = r["grade_recommendation"]
        
        # 如果 grade_recommendation 为 NULL，跳过（公共选修课不写入课程矩阵，因为它们对所有年级开放）
        if grade_rec is None:
            continue
        
        # 将 grade_recommendation (1, 2, 3, 4) 和 term (秋/春) 写入数据库
        records.append({
            "major_id": r["major_id"],
            "major_name": r["major_name"],
            "course_id": cid,
            "course_name": r["course_name"],
            "credits": r["credits"],
            "grade": int(grade_rec),  # 确保转换为整数
            "term": term,
            "category": r["course_category"]
        })
        
    for record in records:
        try:
            db.insert_data("curriculum_matrix", record)
        except Exception as e:
            Logger.warning(f"写入课程矩阵失败: {record['major_name']} - {record['course_id']} - {e}")
            
    Logger.info("✅ 课程矩阵数据写入数据库完成。")


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
            cat = row["course_category"]     # 必修/选修/公选
            
            # 处理 grade_recommendation 可能为 None/NaN 的情况（公共选修课）
            grade_rec = row["grade_recommendation"]
            if pd.isna(grade_rec) or grade_rec is None:
                # 公共选修课：所有年级都可以选，显示在所有学期
                entry = f"{cid} {cname}（{cat}）"
                for sem_key in matrix.keys():
                    matrix[sem_key].append(entry)
                continue
            
            rec = int(grade_rec)
            
            # 如果年级推荐不在1-4范围内，跳过
            if rec < 1 or rec > 4:
                continue

            entry = f"{cid} {cname}（{cat}）"

            # 判断是春季还是秋季课程
            def get_term_for_matrix(cid: str) -> str:
                """
                判断课程应该在哪一学期（秋/春）
                规则：
                1. 大学英语和大学体育系列：奇数号（1,3）在秋季，偶数号（2,4）在春季
                2. 其他课程：尾号2是春季课，其他是秋季课
                """
                # 大学英语系列：EN101(秋), EN102(春), EN103(秋), EN104(春)
                if cid.startswith('EN10'):
                    last_digit = int(cid[-1])
                    return '春' if last_digit % 2 == 0 else '秋'
                
                # 大学体育系列：PE101(秋), PE102(春), PE103(秋), PE104(春)
                if cid.startswith('PE10'):
                    last_digit = int(cid[-1])
                    return '春' if last_digit % 2 == 0 else '秋'
                
                # 其他课程：尾号2是春季课，其他是秋季课
                return '春' if cid.endswith('2') and len(cid) == 5 else '秋'
            
            term = get_term_for_matrix(cid)
            is_spring = (term == '春')

            if is_spring:
                # 春季课程
                sem_key = grade_to_semesters[rec][1] # 第二个学期 (春)
                matrix[sem_key].append(entry)
            else:
                # 秋季课程（尾号1, 或其他非偶数尾号）
                sem_key = grade_to_semesters[rec][0] # 第一个学期 (秋)
                matrix[sem_key].append(entry)

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
    # base_semester 仅用于确定起始年份，系统会为所有学期生成数据
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
                     courses_file=str(data_dir / "course_offerings.csv"),
                     mask_password=mask_pwd,
                     exclude_password=exclude_pwd)
            export_course_summary(db)
            export_program_curriculum(db)
            generate_curriculum_matrix()
            export_classrooms_csv(db)

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