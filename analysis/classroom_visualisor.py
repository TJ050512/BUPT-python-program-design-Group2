import sys
from pathlib import Path
import pandas as pd

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import Logger
from .table_drawer import draw_table_structure

DATA_FILE = project_root / "data" / "classrooms.csv"
OUTPUT_DIR = project_root / "analysis_charts"
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    df = pd.read_csv(DATA_FILE)
    draw_table_structure(
        df=df,
        table_name="classrooms (教室表)",
        pk_column="classroom_id",
        output_dir=OUTPUT_DIR,
        file_stem="classroom_table_structure"
    )
except FileNotFoundError:
    Logger.error(f"数据文件未找到: {DATA_FILE}")
except Exception as e:
    Logger.error(f"处理教室表结构图时出错: {e}")