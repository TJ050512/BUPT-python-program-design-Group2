"""
检查学生学号工具
快速验证数据库中的学号情况
"""

import sys
from pathlib import Path

# 确保项目根在模块搜索路径中
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger


def check_student_ids():
    """检查学生学号"""
    print("=" * 80)
    print("检查数据库中的学生学号")
    print("=" * 80)
    
    Logger.init()
    db = Database()
    
    try:
        # 查询前10个学生
        students = db.execute_query(
            "SELECT student_id, name, class_name, email FROM students ORDER BY student_id LIMIT 10"
        )
        
        if not students:
            print("❌ 数据库中没有学生数据！")
            return
        
        print(f"\n✓ 数据库中共有学生: {db.execute_query('SELECT COUNT(*) as count FROM students')[0]['count']}人\n")
        print("前10个学生的学号:")
        print("-" * 80)
        for s in students:
            print(f"  学号: {s['student_id']:12s}  姓名: {s['name']:8s}  班级: {s['class_name']:8s}  邮箱: {s['email']}")
        print("-" * 80)
        
        # 检查特定学号是否存在
        test_id = "2021210101"
        test_student = db.execute_query(
            "SELECT * FROM students WHERE student_id=?",
            (test_id,)
        )
        
        print(f"\n检查学号 {test_id}:")
        if test_student:
            s = test_student[0]
            print(f"  ✓ 存在！")
            print(f"  姓名: {s['name']}")
            print(f"  班级: {s['class_name']}")
            print(f"  邮箱: {s['email']}")
            print(f"  密码hash: {s['password'][:20]}...")
        else:
            print(f"  ❌ 不存在！")
            print(f"\n提示: 需要运行 python utils/import_csv.py 重新导入数据")
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
    finally:
        db.close()
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    check_student_ids()

