import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import Logger
from .table_drawer import draw_table_structure

DATA_FILE = project_root / "data" / "course_summary.csv"
OUTPUT_DIR = project_root / "analysis_charts"
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    df_courses = pd.read_csv(DATA_FILE)
    draw_table_structure(
        df=df_courses,
        table_name="courses (课程汇总表)",
        pk_column="course_id",
        output_dir=OUTPUT_DIR,
        file_stem="course_table_structure"
    )
except FileNotFoundError:
    Logger.error(f"数据文件未找到: {DATA_FILE}")
except Exception as e:
    Logger.error(f"处理课程表结构图时出错: {e}")