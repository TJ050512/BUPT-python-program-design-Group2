"""
修复班级名称格式
将班级名称从 20211 改为 202101（年份+两位数班级号）
"""

import sys
from pathlib import Path

# 确保项目根在模块搜索路径中
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger


def fix_class_names():
    """修复班级名称格式"""
    print("=" * 80)
    print("修复班级名称格式")
    print("=" * 80)
    print("将班级名称从 20211 改为 202101（年份+两位数班级号）")
    print()
    
    Logger.init()
    db = Database()
    
    try:
        # 获取所有学生
        students = db.execute_query("SELECT student_id, name, class_name FROM students ORDER BY student_id")
        
        if not students:
            print("❌ 没有找到学生数据")
            return
        
        print(f"共有 {len(students)} 名学生")
        print()
        
        # 统计需要更新的班级
        updates = {}
        for student in students:
            old_class = student['class_name']
            # 如果班级名称是5位数字（如 20211），需要改为6位数字（如 202101）
            if old_class and len(old_class) == 5 and old_class.isdigit():
                # 从 20211 -> 202101
                year = old_class[:4]  # 2021
                class_num = old_class[4:]  # 1
                new_class = f"{year}{int(class_num):02d}"  # 202101
                
                if old_class not in updates:
                    updates[old_class] = {
                        'new_class': new_class,
                        'count': 0
                    }
                updates[old_class]['count'] += 1
        
        if not updates:
            print("✓ 所有班级名称格式已正确，无需更新")
            return
        
        # 显示更新预览
        print("将进行以下更新:")
        print("-" * 80)
        for old_class, info in sorted(updates.items()):
            print(f"  {old_class} -> {info['new_class']} ({info['count']} 名学生)")
        print("-" * 80)
        
        confirm = input("\n确认更新？(yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("操作已取消")
            return
        
        # 执行更新
        print("\n开始更新...")
        success_count = 0
        
        for old_class, info in updates.items():
            new_class = info['new_class']
            try:
                db.execute_query(
                    "UPDATE students SET class_name = ? WHERE class_name = ?",
                    (new_class, old_class)
                )
                success_count += info['count']
                print(f"  ✓ {old_class} -> {new_class} ({info['count']} 名学生)")
            except Exception as e:
                print(f"  ❌ 更新失败 {old_class}: {e}")
        
        # 导出更新后的CSV
        print("\n正在导出更新后的CSV文件...")
        import csv
        students = db.execute_query("SELECT * FROM students ORDER BY student_id")
        
        fieldnames = [
            'student_id', 'name', 'password', 'gender', 'birth_date', 
            'major', 'grade', 'class_name', 'enrollment_date', 'status', 
            'email', 'phone', 'created_at', 'updated_at'
        ]
        
        with open('data/students.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for student in students:
                writer.writerow({k: student.get(k, '') for k in fieldnames})
        
        print("\n" + "=" * 80)
        print("✓ 班级名称修复完成！")
        print("=" * 80)
        print(f"✓ 成功更新 {success_count} 名学生的班级名称")
        print(f"✓ 已导出更新后的 CSV 文件: data/students.csv")
        print("=" * 80)
        
        # 显示示例
        print("\n更新后的班级情况:")
        print("-" * 80)
        sample = db.execute_query(
            "SELECT student_id, name, class_name FROM students ORDER BY student_id LIMIT 10"
        )
        for s in sample:
            print(f"  学号: {s['student_id']}  姓名: {s['name']}  班级: {s['class_name']}")
        print("-" * 80)
        
    except Exception as e:
        Logger.error(f"修复过程出错: {e}", exc_info=True)
        print(f"\n❌ 修复失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    fix_class_names()

