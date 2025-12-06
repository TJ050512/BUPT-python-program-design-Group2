#!/usr/bin/env python3
"""
从课程矩阵Markdown文件中解析学期信息
更新 curriculum_matrix 表的 term 字段
"""
import re
import sqlite3
from pathlib import Path

def parse_markdown_file(md_path):
    """
    解析课程矩阵Markdown文件
    返回: {course_id: {'grade': int, 'term': str, 'category': str}}
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    courses = {}
    current_grade = None
    current_term = None
    
    # 匹配标题：## 大一（秋）、## 大一（春）等
    lines = content.split('\n')
    
    for line in lines:
        # 匹配年级和学期标题
        grade_match = re.match(r'^##\s*大([一二三四])（(秋|春)）', line)
        if grade_match:
            grade_cn = grade_match.group(1)
            term = grade_match.group(2)
            
            # 转换中文数字到阿拉伯数字
            grade_map = {'一': 1, '二': 2, '三': 3, '四': 4}
            current_grade = grade_map.get(grade_cn)
            current_term = term
            continue
        
        # 匹配课程行：- CS101 课程名（必修）或 - CS101 课程名（选修）
        course_match = re.match(r'^-\s+([A-Z]+\d+)\s+(.+?)（(必修|选修)）', line)
        if course_match and current_grade and current_term:
            course_id = course_match.group(1)
            course_name = course_match.group(2)
            category = course_match.group(3)
            
            courses[course_id] = {
                'grade': current_grade,
                'term': current_term,
                'category': category,
                'course_name': course_name
            }
    
    return courses

def update_curriculum_matrix():
    """更新 curriculum_matrix 表的学期信息"""
    db_path = Path(__file__).parent / "bupt_teaching.db"
    matrix_dir = Path(__file__).parent / "curriculum_matrix"
    
    if not matrix_dir.exists():
        print(f"❌ 目录不存在: {matrix_dir}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 获取所有专业
        cursor.execute("SELECT major_id, name FROM majors")
        majors = cursor.fetchall()
        
        total_updated = 0
        major_count = 0
        
        for major_id, major_name in majors:
            # 查找对应的Markdown文件
            md_file = matrix_dir / f"{major_name}_课程矩阵.md"
            
            if not md_file.exists():
                print(f"⚠️  未找到文件: {md_file.name}")
                continue
            
            print(f"\n📖 解析: {major_name}")
            
            # 解析Markdown文件
            courses = parse_markdown_file(md_file)
            print(f"   找到 {len(courses)} 门课程")
            
            # 更新数据库
            updated = 0
            for course_id, info in courses.items():
                cursor.execute("""
                    UPDATE curriculum_matrix
                    SET term = ?, grade = ?
                    WHERE major_id = ? AND course_id = ?
                """, (info['term'], info['grade'], major_id, course_id))
                
                if cursor.rowcount > 0:
                    updated += 1
            
            print(f"   ✅ 更新 {updated} 门课程")
            total_updated += updated
            major_count += 1
        
        conn.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ 更新完成:")
        print(f"   - 处理专业: {major_count} 个")
        print(f"   - 更新课程: {total_updated} 条")
        
        # 验证：检查计算机科学与技术专业的学期分布
        cursor.execute("""
            SELECT grade, term, category, COUNT(*) as count
            FROM curriculum_matrix
            WHERE major_name = '计算机科学与技术'
            GROUP BY grade, term, category
            ORDER BY grade, 
                     CASE term WHEN '秋' THEN 1 WHEN '春' THEN 2 END,
                     category DESC
        """)
        
        print(f"\n🎓 计算机科学与技术专业课程分布:")
        for grade, term, category, count in cursor.fetchall():
            print(f"   大{grade}（{term}）{category}: {count} 门")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    update_curriculum_matrix()
