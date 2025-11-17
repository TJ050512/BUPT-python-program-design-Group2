"""
课程和培养方案数据导入工具（独立版本）
不需要安装额外依赖，直接使用 Python 标准库

用法:
    python3 导入课程数据.py
"""

import sqlite3
import csv
from pathlib import Path
from datetime import datetime


class SimpleCourseImporter:
    """简单的课程数据导入器"""
    
    def __init__(self, db_path: str = "data/bupt_teaching.db"):
        """初始化导入器"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        print(f"✓ 已连接到数据库: {db_path}")
    
    def import_courses(self, csv_file: str = "data/course_summary.csv") -> tuple:
        """导入课程数据"""
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"✗ 课程CSV文件不存在: {csv_file}")
            return 0, 0
        
        print(f"\n正在导入课程数据: {csv_file}")
        
        success_count = 0
        fail_count = 0
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        course_id = row.get('course_id', '').strip()
                        course_name = row.get('course_name', '').strip()
                        
                        if not course_id:
                            continue
                        
                        credits = float(row.get('credits', 0)) if row.get('credits') else 0.0
                        hours = int(row.get('hours', 0)) if row.get('hours') else 0
                        course_type = row.get('course_type', '').strip()
                        department = row.get('department', '').strip()
                        
                        # 检查是否已存在
                        self.cursor.execute(
                            "SELECT course_id FROM courses WHERE course_id=?",
                            (course_id,)
                        )
                        existing = self.cursor.fetchone()
                        
                        if existing:
                            # 更新
                            self.cursor.execute("""
                                UPDATE courses 
                                SET course_name=?, credits=?, hours=?, course_type=?, 
                                    department=?, updated_at=?
                                WHERE course_id=?
                            """, (course_name, credits, hours, course_type, department,
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), course_id))
                        else:
                            # 插入
                            self.cursor.execute("""
                                INSERT INTO courses 
                                (course_id, course_name, credits, hours, course_type, 
                                 department, max_students, is_public_elective, 
                                 created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, ?, 60, 0, ?, ?)
                            """, (course_id, course_name, credits, hours, course_type,
                                  department, 
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        
                        success_count += 1
                        
                    except Exception as e:
                        fail_count += 1
                        print(f"  ✗ 导入失败: {row.get('course_id', 'unknown')} - {e}")
                        continue
            
            self.conn.commit()
            print(f"✓ 课程数据导入完成: 成功 {success_count} 条，失败 {fail_count} 条")
            
        except Exception as e:
            print(f"✗ 读取课程CSV文件失败: {e}")
            self.conn.rollback()
        
        return success_count, fail_count
    
    def import_program_curriculum(self, csv_file: str = "data/program_curriculum.csv") -> tuple:
        """导入培养方案数据"""
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"✗ 培养方案CSV文件不存在: {csv_file}")
            return 0, 0
        
        print(f"\n正在导入培养方案数据: {csv_file}")
        
        success_count = 0
        fail_count = 0
        
        colleges_cache = {}
        majors_cache = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        college_code = row.get('college_code', '').strip()
                        college_name = row.get('college_name', '').strip()
                        major_name = row.get('major_name', '').strip()
                        course_id = row.get('course_id', '').strip()
                        course_category = row.get('course_category', '').strip()
                        
                        # 跳过空行
                        if not college_code or not major_name or not course_id:
                            continue
                        
                        cross_major_quota = int(row.get('cross_major_quota', 0)) if row.get('cross_major_quota') else 0
                        grade_recommendation = int(row.get('grade_recommendation', 1)) if row.get('grade_recommendation') else 1
                        
                        # 1. 确保学院存在
                        if college_code not in colleges_cache:
                            self.cursor.execute(
                                "SELECT college_code FROM colleges WHERE college_code=?",
                                (college_code,)
                            )
                            if not self.cursor.fetchone():
                                try:
                                    self.cursor.execute(
                                        "INSERT INTO colleges (college_code, name) VALUES (?, ?)",
                                        (college_code, college_name)
                                    )
                                except sqlite3.IntegrityError:
                                    pass  # 已存在
                            colleges_cache[college_code] = True
                        
                        # 2. 确保专业存在
                        major_key = f"{college_code}_{major_name}"
                        if major_key not in majors_cache:
                            self.cursor.execute(
                                "SELECT major_id FROM majors WHERE college_code=? AND name=?",
                                (college_code, major_name)
                            )
                            result = self.cursor.fetchone()
                            
                            if result:
                                majors_cache[major_key] = result['major_id']
                            else:
                                try:
                                    self.cursor.execute(
                                        "INSERT INTO majors (college_code, name) VALUES (?, ?)",
                                        (college_code, major_name)
                                    )
                                    majors_cache[major_key] = self.cursor.lastrowid
                                except sqlite3.IntegrityError:
                                    # 如果插入失败，再次查询
                                    self.cursor.execute(
                                        "SELECT major_id FROM majors WHERE college_code=? AND name=?",
                                        (college_code, major_name)
                                    )
                                    result = self.cursor.fetchone()
                                    if result:
                                        majors_cache[major_key] = result['major_id']
                        
                        major_id = majors_cache.get(major_key)
                        if not major_id:
                            fail_count += 1
                            continue
                        
                        # 3. 插入培养方案
                        self.cursor.execute(
                            "SELECT id FROM program_courses WHERE major_id=? AND course_id=?",
                            (major_id, course_id)
                        )
                        existing = self.cursor.fetchone()
                        
                        if existing:
                            # 更新
                            self.cursor.execute("""
                                UPDATE program_courses 
                                SET course_category=?, cross_major_quota=?, grade_recommendation=?
                                WHERE major_id=? AND course_id=?
                            """, (course_category, cross_major_quota, grade_recommendation,
                                  major_id, course_id))
                        else:
                            # 插入
                            try:
                                self.cursor.execute("""
                                    INSERT INTO program_courses 
                                    (major_id, course_id, course_category, cross_major_quota, grade_recommendation)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (major_id, course_id, course_category, cross_major_quota, grade_recommendation))
                            except sqlite3.IntegrityError:
                                pass  # 已存在
                        
                        success_count += 1
                        
                    except Exception as e:
                        fail_count += 1
                        print(f"  ✗ 导入失败: {row.get('course_id', 'unknown')} - {e}")
                        continue
            
            self.conn.commit()
            print(f"✓ 培养方案数据导入完成: 成功 {success_count} 条，失败 {fail_count} 条")
            
        except Exception as e:
            print(f"✗ 读取培养方案CSV文件失败: {e}")
            self.conn.rollback()
        
        return success_count, fail_count
    
    def verify_import(self):
        """验证导入结果"""
        print("\n" + "=" * 60)
        print("导入数据验证")
        print("=" * 60)
        
        # 课程统计
        self.cursor.execute("SELECT COUNT(*) as count FROM courses")
        course_count = self.cursor.fetchone()['count']
        print(f"✓ 课程总数: {course_count}")
        
        # 示例课程
        self.cursor.execute(
            "SELECT course_id, course_name, credits, department FROM courses LIMIT 5"
        )
        print("  示例课程:")
        for row in self.cursor.fetchall():
            print(f"    - {row['course_id']}: {row['course_name']} "
                  f"({row['credits']}学分, {row['department']})")
        
        # 学院统计
        self.cursor.execute("SELECT COUNT(*) as count FROM colleges")
        college_count = self.cursor.fetchone()['count']
        print(f"✓ 学院总数: {college_count}")
        
        # 专业统计
        self.cursor.execute("SELECT COUNT(*) as count FROM majors")
        major_count = self.cursor.fetchone()['count']
        print(f"✓ 专业总数: {major_count}")
        
        # 示例专业
        self.cursor.execute("""
            SELECT m.name as major_name, c.name as college_name 
            FROM majors m 
            JOIN colleges c ON m.college_code = c.college_code 
            LIMIT 5
        """)
        print("  示例专业:")
        for row in self.cursor.fetchall():
            print(f"    - {row['major_name']} ({row['college_name']})")
        
        # 培养方案统计
        self.cursor.execute("SELECT COUNT(*) as count FROM program_courses")
        program_count = self.cursor.fetchone()['count']
        print(f"✓ 培养方案记录总数: {program_count}")
        
        print("=" * 60)
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            print("\n✓ 数据库连接已关闭")


def main():
    """主函数"""
    print("=" * 60)
    print("北京邮电大学教学管理系统")
    print("课程和培养方案数据导入工具")
    print("=" * 60)
    
    importer = SimpleCourseImporter()
    
    try:
        # 导入课程
        c_success, c_fail = importer.import_courses()
        
        # 导入培养方案
        p_success, p_fail = importer.import_program_curriculum()
        
        # 验证结果
        importer.verify_import()
        
        print("\n" + "=" * 60)
        print("✓ 所有数据导入完成！")
        print("=" * 60)
        print("\n数据导入情况:")
        print(f"  • 课程: 成功 {c_success} 条, 失败 {c_fail} 条")
        print(f"  • 培养方案: 成功 {p_success} 条, 失败 {p_fail} 条")
        print("\n数据已保存到: data/bupt_teaching.db")
        print()
        
    except Exception as e:
        print(f"\n✗ 导入过程出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        importer.close()


if __name__ == "__main__":
    main()

