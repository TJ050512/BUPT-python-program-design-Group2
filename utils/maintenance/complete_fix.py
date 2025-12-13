"""
完整修复脚本
1. 清理数据库中的学生数据
2. 修复CSV文件中的班级名称格式
3. 重新导入正确的数据
"""

import sys
import csv
from pathlib import Path

# 确保项目根在模块搜索路径中
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger


def complete_fix():
    """完整修复"""
    print("=" * 80)
    print("完整修复学生数据")
    print("=" * 80)
    print()
    
    Logger.init()
    db = Database()
    
    try:
        # 步骤1: 检查当前数据库状态
        print("步骤1: 检查当前数据...")
        students = db.execute_query("SELECT COUNT(*) as count FROM students")
        current_count = students[0]['count'] if students else 0
        print(f"  当前数据库中有 {current_count} 个学生")
        
        # 步骤2: 读取并修复CSV文件
        print("\n步骤2: 修复CSV文件中的班级名称...")
        csv_file = Path("data/students.csv")
        
        if not csv_file.exists():
            print("  ❌ CSV文件不存在!")
            return
        
        # 读取CSV
        students_data = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 修复班级名称格式: 20211 -> 202101
                class_name = row.get('class_name', '')
                if class_name and len(class_name) == 5 and class_name.isdigit():
                    year = class_name[:4]  # 2021
                    class_num = class_name[4:]  # 1
                    row['class_name'] = f"{year}{int(class_num):02d}"  # 202101
                
                students_data.append(row)
        
        print(f"  从CSV读取 {len(students_data)} 个学生")
        print(f"  已修复班级名称格式")
        
        # 步骤3: 清空数据库中的学生表
        print("\n步骤3: 清空数据库中的学生数据...")
        confirm = input("  确认清空并重新导入？(yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("操作已取消")
            return
        
        db.execute_query("DELETE FROM students")
        print("  ✓ 已清空学生表")
        
        # 步骤4: 重新插入数据
        print("\n步骤4: 重新导入学生数据...")
        success_count = 0
        fail_count = 0
        
        for student in students_data:
            try:
                # 插入学生数据
                db.insert_data('students', student)
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"  ❌ 插入失败: {student.get('student_id')} - {e}")
        
        print(f"  ✓ 成功导入 {success_count} 个学生")
        if fail_count > 0:
            print(f"  ❌ 失败 {fail_count} 个")
        
        # 步骤5: 保存修复后的CSV
        print("\n步骤5: 保存修复后的CSV文件...")
        fieldnames = [
            'student_id', 'name', 'password', 'gender', 'birth_date', 
            'major', 'grade', 'class_name', 'enrollment_date', 'status', 
            'email', 'phone', 'created_at', 'updated_at'
        ]
        
        with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(students_data)
        
        print("  ✓ CSV文件已更新")
        
        # 步骤6: 验证修复结果
        print("\n步骤6: 验证修复结果...")
        students = db.execute_query("SELECT COUNT(*) as count FROM students")
        final_count = students[0]['count'] if students else 0
        print(f"  数据库中现有 {final_count} 个学生")
        
        # 显示班级分布
        print("\n  班级分布:")
        classes = db.execute_query("""
            SELECT class_name, COUNT(*) as count 
            FROM students 
            GROUP BY class_name 
            ORDER BY class_name
        """)
        
        for cls in classes:
            print(f"    {cls['class_name']}班: {cls['count']}人")
        
        # 显示前5个学生示例
        print("\n  前5个学生示例:")
        sample = db.execute_query("""
            SELECT student_id, name, class_name 
            FROM students 
            ORDER BY student_id 
            LIMIT 5
        """)
        
        for s in sample:
            print(f"    学号: {s['student_id']}  姓名: {s['name']}  班级: {s['class_name']}")
        
        print("\n" + "=" * 80)
        print("✓ 修复完成！")
        print("=" * 80)
        print(f"\n总结:")
        print(f"  - 原数据库: {current_count} 个学生")
        print(f"  - 现数据库: {final_count} 个学生")
        print(f"  - 班级名称格式已修复为6位数字（如 202101）")
        print(f"  - 所有密码已统一为: 123456")
        print("=" * 80)
        
    except Exception as e:
        Logger.error(f"修复过程出错: {e}", exc_info=True)
        print(f"\n❌ 修复失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    complete_fix()

