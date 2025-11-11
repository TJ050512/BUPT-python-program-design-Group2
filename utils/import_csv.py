"""
CSV数据导入工具
用于将CSV文件中的学生和教师数据导入到系统数据库

用法:
    python utils/import_csv.py
    或
    python -m utils.import_csv
"""

import sys
import csv
from pathlib import Path
from datetime import datetime

# 确保项目根在模块搜索路径中
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger


class CSVImporter:
    """CSV数据导入器"""
    
    def __init__(self, db_path: str = "data/bupt_teaching.db"):
        """初始化导入器"""
        self.db = Database(db_path)
        Logger.info(f"CSV导入器初始化完成，数据库: {db_path}")
    
    def import_students(self, csv_file: str = "data/students.csv") -> tuple[int, int]:
        """
        导入学生数据
        
        Args:
            csv_file: 学生CSV文件路径
        
        Returns:
            (成功数, 失败数)
        """
        csv_path = Path(csv_file)
        if not csv_path.exists():
            Logger.error(f"学生CSV文件不存在: {csv_file}")
            return 0, 0
        
        Logger.info(f"开始导入学生数据: {csv_file}")
        
        success_count = 0
        fail_count = 0
        
        try:
            # 使用 utf-8-sig 自动处理 BOM
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # 准备学生数据
                        student_data = {
                            'student_id': row.get('student_id', '').strip(),
                            'name': row.get('name', '').strip(),
                            'password': row.get('password', '').strip(),
                            'gender': row.get('gender', '').strip(),
                            'birth_date': row.get('birth_date', '').strip(),
                            'major': row.get('major', '').strip(),
                            'grade': int(row.get('grade', 0)) if row.get('grade') else None,
                            'class_name': row.get('class_name', '').strip(),
                            'enrollment_date': row.get('enrollment_date', '').strip(),
                            'status': row.get('status', 'active').strip(),
                            'email': row.get('email', '').strip(),
                            'phone': row.get('phone', '').strip(),
                            'created_at': row.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            'updated_at': row.get('updated_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        }
                        
                        # 检查是否已存在
                        existing = self.db.execute_query(
                            "SELECT student_id FROM students WHERE student_id=?",
                            (student_data['student_id'],)
                        )
                        
                        if existing:
                            # 更新已存在的记录
                            self.db.update_data(
                                'students',
                                student_data,
                                {'student_id': student_data['student_id']}
                            )
                            Logger.debug(f"更新学生: {student_data['student_id']} - {student_data['name']}")
                        else:
                            # 插入新记录
                            self.db.insert_data('students', student_data)
                            Logger.debug(f"插入学生: {student_data['student_id']} - {student_data['name']}")
                        
                        success_count += 1
                        
                    except Exception as e:
                        fail_count += 1
                        Logger.error(f"导入学生失败: {row.get('student_id', 'unknown')} - {e}")
                        continue
        
        except Exception as e:
            Logger.error(f"读取学生CSV文件失败: {e}", exc_info=True)
            return success_count, fail_count
        
        Logger.info(f"学生数据导入完成: 成功 {success_count} 条，失败 {fail_count} 条")
        return success_count, fail_count
    
    def import_teachers(self, csv_file: str = "data/teachers.csv") -> tuple[int, int]:
        """
        导入教师数据
        
        Args:
            csv_file: 教师CSV文件路径
        
        Returns:
            (成功数, 失败数)
        """
        csv_path = Path(csv_file)
        if not csv_path.exists():
            Logger.error(f"教师CSV文件不存在: {csv_file}")
            return 0, 0
        
        Logger.info(f"开始导入教师数据: {csv_file}")
        
        success_count = 0
        fail_count = 0
        
        try:
            # 使用 utf-8-sig 自动处理 BOM
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # 准备教师数据
                        teacher_data = {
                            'teacher_id': row.get('teacher_id', '').strip(),
                            'name': row.get('name', '').strip(),
                            'password': row.get('password', '').strip(),
                            'gender': row.get('gender', '').strip(),
                            'title': row.get('title', '').strip(),
                            'department': row.get('department', '').strip(),
                            'email': row.get('email', '').strip(),
                            'phone': row.get('phone', '').strip(),
                            'hire_date': row.get('hire_date', '').strip() or None,
                            'status': row.get('status', 'active').strip(),
                            'created_at': row.get('created_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                            'updated_at': row.get('updated_at', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        }
                        
                        # 检查是否已存在
                        existing = self.db.execute_query(
                            "SELECT teacher_id FROM teachers WHERE teacher_id=?",
                            (teacher_data['teacher_id'],)
                        )
                        
                        if existing:
                            # 更新已存在的记录
                            self.db.update_data(
                                'teachers',
                                teacher_data,
                                {'teacher_id': teacher_data['teacher_id']}
                            )
                            Logger.debug(f"更新教师: {teacher_data['teacher_id']} - {teacher_data['name']}")
                        else:
                            # 插入新记录
                            self.db.insert_data('teachers', teacher_data)
                            Logger.debug(f"插入教师: {teacher_data['teacher_id']} - {teacher_data['name']}")
                        
                        success_count += 1
                        
                    except Exception as e:
                        fail_count += 1
                        Logger.error(f"导入教师失败: {row.get('teacher_id', 'unknown')} - {e}")
                        continue
        
        except Exception as e:
            Logger.error(f"读取教师CSV文件失败: {e}", exc_info=True)
            return success_count, fail_count
        
        Logger.info(f"教师数据导入完成: 成功 {success_count} 条，失败 {fail_count} 条")
        return success_count, fail_count
    
    def verify_import(self):
        """验证导入结果"""
        Logger.info("=" * 60)
        Logger.info("导入数据验证")
        Logger.info("=" * 60)
        
        # 验证学生数据
        students = self.db.execute_query("SELECT COUNT(*) as count FROM students")
        student_count = students[0]['count'] if students else 0
        Logger.info(f"✓ 学生总数: {student_count}")
        
        # 显示部分学生
        sample_students = self.db.execute_query(
            "SELECT student_id, name, major, grade FROM students LIMIT 5"
        )
        Logger.info("  示例学生:")
        for s in sample_students:
            Logger.info(f"    - {s['student_id']}: {s['name']} ({s['major']}, {s['grade']}级)")
        
        # 验证教师数据
        teachers = self.db.execute_query("SELECT COUNT(*) as count FROM teachers")
        teacher_count = teachers[0]['count'] if teachers else 0
        Logger.info(f"✓ 教师总数: {teacher_count}")
        
        # 显示部分教师
        sample_teachers = self.db.execute_query(
            "SELECT teacher_id, name, title, department FROM teachers LIMIT 5"
        )
        Logger.info("  示例教师:")
        for t in sample_teachers:
            Logger.info(f"    - {t['teacher_id']}: {t['name']} ({t['title']}, {t['department']})")
        
        Logger.info("=" * 60)
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("北京邮电大学教学管理系统 - CSV数据导入工具")
    print("=" * 60)
    print()
    
    # 初始化日志
    Logger.init()
    
    # 创建导入器
    importer = CSVImporter()
    
    try:
        # 导入学生数据
        print("正在导入学生数据...")
        s_success, s_fail = importer.import_students("data/students.csv")
        print(f"✓ 学生数据: 成功 {s_success} 条, 失败 {s_fail} 条")
        print()
        
        # 导入教师数据
        print("正在导入教师数据...")
        t_success, t_fail = importer.import_teachers("data/teachers.csv")
        print(f"✓ 教师数据: 成功 {t_success} 条, 失败 {t_fail} 条")
        print()
        
        # 验证导入
        print("验证导入结果...")
        importer.verify_import()
        print()
        
        print("=" * 60)
        print("✓ CSV数据导入完成！")
        print("=" * 60)
        print()
        print("提示:")
        print("  - 学生默认密码已从CSV文件中读取（bcrypt加密）")
        print("  - 教师默认密码已从CSV文件中读取（bcrypt加密）")
        print("  - 数据已保存到: data/bupt_teaching.db")
        print("  - 现在可以运行 python main.py 启动系统")
        print()
        
    except Exception as e:
        Logger.error(f"导入过程出错: {e}", exc_info=True)
        print(f"\n✗ 导入失败: {e}")
        print("请检查日志文件: logs/app.log")
    
    finally:
        importer.close()


if __name__ == "__main__":
    main()

