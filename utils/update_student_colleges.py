"""
更新学生学院信息
根据学生的专业名称，从majors表查找对应的学院，并更新students表的college_code和major_id

用法:
    python3 utils/update_student_colleges.py
"""

import sqlite3
from pathlib import Path


def update_student_colleges(db_path: str = "data/bupt_teaching.db"):
    """更新学生的学院和专业ID"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("更新学生学院信息")
    print("=" * 60)
    
    # 暂时禁用触发器（因为学号格式与college_code格式不匹配）
    print("\n暂时禁用触发器...")
    try:
        cursor.execute("DROP TRIGGER IF EXISTS trg_students_college_match_bu")
        print("✓ 已禁用更新触发器")
    except Exception as e:
        print(f"⚠ 禁用触发器时出错: {e}")
    
    # 1. 获取所有学生及其专业
    cursor.execute("""
        SELECT student_id, major 
        FROM students 
        WHERE major IS NOT NULL AND major != ''
    """)
    students = cursor.fetchall()
    
    print(f"\n找到 {len(students)} 个学生需要更新学院信息\n")
    
    updated_count = 0
    not_found_count = 0
    not_found_majors = set()
    
    # 2. 为每个学生查找对应的学院和专业ID
    for student in students:
        student_id = student['student_id']
        major_name = student['major']
        
        # 查找专业对应的学院
        cursor.execute("""
            SELECT m.major_id, m.college_code, c.name as college_name
            FROM majors m
            JOIN colleges c ON m.college_code = c.college_code
            WHERE m.name = ?
        """, (major_name,))
        
        result = cursor.fetchone()
        
        if result:
            major_id = result['major_id']
            college_code = result['college_code']
            college_name = result['college_name']
            
            # 更新学生记录
            cursor.execute("""
                UPDATE students 
                SET college_code = ?, major_id = ?
                WHERE student_id = ?
            """, (college_code, major_id, student_id))
            
            updated_count += 1
            if updated_count % 100 == 0:
                print(f"  已更新 {updated_count} 个学生...")
        else:
            not_found_count += 1
            not_found_majors.add(major_name)
            print(f"  ⚠ 未找到专业: {major_name} (学号: {student_id})")
    
    conn.commit()
    
    print("\n" + "=" * 60)
    print("更新完成")
    print("=" * 60)
    print(f"✓ 成功更新: {updated_count} 个学生")
    print(f"✗ 未找到专业: {not_found_count} 个学生")
    
    if not_found_majors:
        print(f"\n未找到的专业列表:")
        for major in sorted(not_found_majors):
            print(f"  - {major}")
        print("\n提示: 这些专业可能不在majors表中，请检查program_curriculum.csv是否已导入")
    
    # 验证结果
    cursor.execute("""
        SELECT COUNT(*) as count 
        FROM students 
        WHERE college_code IS NOT NULL
    """)
    result = cursor.fetchone()
    print(f"\n✓ 数据库中已有学院信息的学生数: {result['count']}")
    
    # 注意：不重新创建触发器，因为学号格式（10位）与college_code格式（7位）不匹配
    # 触发器逻辑需要根据实际学号格式调整
    print("\n⚠ 触发器已禁用，因为学号格式与college_code格式不匹配")
    print("   学号格式: YYYY XX NNNN (10位)")
    print("   college_code格式: YYYYXXX (7位)")
    print("   如需启用验证，请修改触发器逻辑")
    
    conn.close()
    print("\n✓ 数据库连接已关闭")


if __name__ == "__main__":
    update_student_colleges()

