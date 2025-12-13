import sqlite3
import csv
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "bupt_teaching.db"
OUT_DIR = PROJECT_ROOT / "data"

def export_table_to_csv(db_path: Path, table: str, out_file: Path, preferred_order: list = None) -> bool:
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {table};")
    except Exception as e:
        print(f"导出表 {table} 失败: {e}")
        conn.close()
        return False

    rows = cur.fetchall()
    if not rows:
        # 获取列名仍然有帮助
        cols = [d[0] for d in cur.description] if cur.description else []
    else:
        cols = rows[0].keys()

    # 如果提供 preferred_order，则按该顺序输出，其余列追加在后面
    if preferred_order:
        ordered = [c for c in preferred_order if c in cols]
        ordered += [c for c in cols if c not in ordered]
    else:
        ordered = list(cols)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with out_file.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(ordered)
            for r in rows:
                writer.writerow([r[col] for col in ordered])
        print(f"已导出 {table} -> {out_file} ({len(rows)} 行)")
        return True
    except Exception as e:
        print(f"写入 CSV 失败: {e}")
        return False
    finally:
        conn.close()

def main():
    students_order = [
        "student_id","name","password","gender","birth_date","major","grade",
        "class_name","enrollment_date","status","email","phone","created_at","updated_at"
    ]
    teachers_order = [
        "teacher_id","name","password","gender","title","department",
        "email","phone","created_at","updated_at","status"
    ]

    export_table_to_csv(DB_PATH, "students", OUT_DIR / "students.csv", students_order)
    export_table_to_csv(DB_PATH, "teachers", OUT_DIR / "teachers.csv", teachers_order)

if __name__ == "__main__":
    main()