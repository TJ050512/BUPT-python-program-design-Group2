"""
课程矩阵（培养方案）导入工具
解析 curriculum_matrix 文件夹中的 Markdown 文件，导入到数据库

用法:
    python3 utils/import_curriculum_matrix.py
"""

import sqlite3
import re
from pathlib import Path


def parse_semester_name(semester_text: str) -> tuple:
    """
    解析学期名称，返回(年级, 学期)
    
    Args:
        semester_text: 如 "大一（秋）" 或 "大二（春）"
    
    Returns:
        (grade: int, term: str) 如 (1, "秋") 或 (2, "春")
    """
    grade_map = {"一": 1, "二": 2, "三": 3, "四": 4}
    term_map = {"秋": "fall", "春": "spring"}
    
    match = re.search(r'大([一二三四])[（(]([秋春])[）)]', semester_text)
    if match:
        grade_cn = match.group(1)
        term_cn = match.group(2)
        grade = grade_map.get(grade_cn, 1)
        term = term_map.get(term_cn, "fall")
        return grade, term
    return None, None


def parse_course_line(line: str) -> dict:
    """
    解析课程行，提取课程代码、名称和类型
    
    Args:
        line: 如 "- CM201 C语言程序设计（必修）"
    
    Returns:
        {"course_id": "CM201", "course_name": "C语言程序设计", "category": "必修"}
    """
    line = line.strip()
    if not line.startswith('-'):
        return None
    
    # 移除开头的 "- "
    line = line[2:].strip()
    
    # 匹配格式: COURSE_ID 课程名称（类型）
    match = re.match(r'^([A-Z0-9]+)\s+(.+?)\s*[（(]([^）)]+)[）)]', line)
    if match:
        course_id = match.group(1)
        course_name = match.group(2).strip()
        category = match.group(3)
        
        # 标准化类别
        if "必修" in category:
            category = "必修"
        elif "选修" in category:
            category = "选修"
        else:
            category = "选修"
        
        return {
            "course_id": course_id,
            "course_name": course_name,
            "category": category
        }
    
    return None


def parse_markdown_file(file_path: Path) -> list:
    """
    解析 Markdown 文件，提取培养方案数据
    
    Returns:
        [(grade, term, course_id, category), ...]
    """
    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取专业名称
    major_match = re.search(r'#\s*🎓\s*(.+?)\s+四年课程矩阵图', content)
    major_name = major_match.group(1).strip() if major_match else None
    
    if not major_name:
        print(f"  ⚠ 无法提取专业名称: {file_path.name}")
        return []
    
    # 按学期分割
    sections = re.split(r'##\s+', content)
    
    for section in sections[1:]:  # 跳过第一个空部分
        lines = section.split('\n')
        if not lines:
            continue
        
        # 第一行是学期名称
        semester_line = lines[0].strip()
        grade, term = parse_semester_name(semester_line)
        
        if not grade or not term:
            continue
        
        # 解析课程
        for line in lines[1:]:
            course_info = parse_course_line(line)
            if course_info:
                data.append({
                    "major_name": major_name,
                    "grade": grade,
                    "term": term,
                    "course_id": course_info["course_id"],
                    "category": course_info["category"]
                })
    
    return data


def import_curriculum_matrix(db_path: str = "data/bupt_teaching.db"):
    """导入课程矩阵数据"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 60)
    print("导入课程矩阵（培养方案）数据")
    print("=" * 60)
    
    # 创建表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curriculum_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            major_id INTEGER NOT NULL,
            grade INTEGER NOT NULL,
            term TEXT NOT NULL,
            course_id TEXT NOT NULL,
            category TEXT NOT NULL,
            UNIQUE(major_id, grade, term, course_id),
            CHECK (grade BETWEEN 1 AND 4),
            CHECK (term IN ('fall', 'spring')),
            CHECK (category IN ('必修', '选修')),
            FOREIGN KEY (major_id) REFERENCES majors(major_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id)
        )
    """)
    
    # 清空旧数据（可选）
    cursor.execute("DELETE FROM curriculum_matrix")
    print("\n已清空旧数据")
    
    # 获取所有 Markdown 文件
    matrix_dir = Path("data/curriculum_matrix")
    md_files = list(matrix_dir.glob("*_课程矩阵.md"))
    
    print(f"\n找到 {len(md_files)} 个课程矩阵文件\n")
    
    total_records = 0
    success_count = 0
    fail_count = 0
    
    # 专业名称到ID的映射
    major_cache = {}
    
    for md_file in md_files:
        print(f"处理: {md_file.name}")
        
        try:
            # 解析文件
            data = parse_markdown_file(md_file)
            
            if not data:
                print(f"  ⚠ 未解析到数据\n")
                continue
            
            major_name = data[0]["major_name"]
            
            # 获取专业ID
            if major_name not in major_cache:
                cursor.execute(
                    "SELECT major_id FROM majors WHERE name=?",
                    (major_name,)
                )
                result = cursor.fetchone()
                if result:
                    major_cache[major_name] = result['major_id']
                else:
                    print(f"  ✗ 未找到专业: {major_name}\n")
                    fail_count += len(data)
                    continue
            
            major_id = major_cache[major_name]
            
            # 插入数据
            for record in data:
                try:
                    cursor.execute("""
                        INSERT INTO curriculum_matrix 
                        (major_id, grade, term, course_id, category)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        major_id,
                        record["grade"],
                        record["term"],
                        record["course_id"],
                        record["category"]
                    ))
                    success_count += 1
                except sqlite3.IntegrityError:
                    # 已存在，跳过
                    pass
                except Exception as e:
                    print(f"  ✗ 插入失败: {record['course_id']} - {e}")
                    fail_count += 1
            
            total_records += len(data)
            print(f"  ✓ 成功导入 {len(data)} 条记录\n")
            
        except Exception as e:
            print(f"  ✗ 处理失败: {e}\n")
            fail_count += 1
    
    conn.commit()
    
    print("=" * 60)
    print("导入完成")
    print("=" * 60)
    print(f"✓ 成功导入: {success_count} 条记录")
    print(f"✗ 失败: {fail_count} 条记录")
    
    # 验证结果
    cursor.execute("SELECT COUNT(*) as count FROM curriculum_matrix")
    result = cursor.fetchone()
    print(f"\n✓ 数据库中培养方案记录总数: {result['count']}")
    
    # 按专业统计
    cursor.execute("""
        SELECT m.name as major_name, COUNT(*) as count
        FROM curriculum_matrix cm
        JOIN majors m ON cm.major_id = m.major_id
        GROUP BY m.name
        ORDER BY m.name
    """)
    print("\n各专业培养方案统计:")
    for row in cursor.fetchall():
        print(f"  - {row['major_name']}: {row['count']} 门课程")
    
    conn.close()
    print("\n✓ 数据库连接已关闭")


if __name__ == "__main__":
    import_curriculum_matrix()

