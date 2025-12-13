import sys
from pathlib import Path
import pprint

# 确保项目根在模块搜索路径中
project_root = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(project_root))

PP = pprint.PrettyPrinter(indent=2)

# 兼容两种 DB 实现：database_module.DatabaseManager OR data.database.Database
Adapter = None
try:
    from database_module import DatabaseManager  # type: ignore

    class Adapter:
        def __init__(self, db_path: str):
            cfg = {'type': 'sqlite', 'path': str(db_path)}
            self._db = DatabaseManager(cfg)

        def query(self, sql, params=None):
            return self._db.query(sql, params)

        def execute(self, sql, params=None):
            return self._db.execute(sql, params)

        def insert(self, table, data):
            return self._db.insert(table, data)

        def close(self):
            return self._db.close()

    print("使用 database_module.DatabaseManager 测试")
except Exception:
    try:
        from data.database import Database  # type: ignore

        class Adapter:
            def __init__(self, db_path: str):
                self._db = Database(str(db_path))

            def query(self, sql, params=None):
                return self._db.execute_query(sql, params)

            def execute(self, sql, params=None):
                return self._db.execute_update(sql, params)

            def insert(self, table, data):
                return self._db.insert_data(table, data)

            def close(self):
                return self._db.close()

        print("回退使用 data.database.Database 测试")
    except Exception as e:
        print("未找到可用的数据库模块（database_module 或 data.database）:", e)
        sys.exit(2)

def main():
    db_file = Path("data") / "bupt_teaching.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db = Adapter(str(db_file))

    try:
        print("\n=== 表列表 ===")
        try:
            tables = db.query("SELECT name FROM sqlite_master WHERE type='table';")
            PP.pprint(tables)
        except Exception as e:
            print("查询表失败:", e)

        print("\n=== 查询 users 表（前5条） ===")
        try:
            users = db.query("SELECT * FROM users LIMIT 5;")
            PP.pprint(users)
        except Exception as e:
            print("查询 users 失败（表可能不存在）:", e)

        print("\n=== 插入并查询 test 数据记录 ===")
        try:
            rec = {
                "title": "测试记录",
                "content": "这是由 test_database.py 插入的测试内容",
                "category": "测试",
                "source": "unittest",
            }
            inserted_id = db.insert("data_records", rec)
            print("插入ID:", inserted_id)
            rows = db.query("SELECT id, title, category, source FROM data_records WHERE title=? LIMIT 5;", (rec["title"],))
            PP.pprint(rows)
        except Exception as e:
            print("插入或查询 data_records 失败:", e)

        print("\n=== students / teachers 行数统计 ===")
        for t in ("students", "teachers"):
            try:
                r = db.query(f"SELECT COUNT(*) as c FROM {t};")
                cnt = r[0].get("c") if r else None
                print(f"{t}: {cnt}")
            except Exception:
                print(f"{t}: 表不存在或查询失败")
    finally:
        try:
            db.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()