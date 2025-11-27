"""
课程开课计划导入工具
从 course_offerings.csv 导入开课数据到数据库

用法:
    python utils/import_course_offerings.py
    或
    python -m utils.import_course_offerings
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


class CourseOfferingImporter:
    """课程开课计划导入器"""
    
    def __init__(self, db_path: str = "data/bupt_teaching.db"):
        """初始化导入器"""
        self.db = Database(db_path)
        Logger.info(f"课程开课计划导入器初始化完成，数据库: {db_path}")
    
    def clear_existing_offerings(self):
        """清空现有的开课计划数据"""
        try:
            Logger.info("正在清空现有的开课计划数据...")
            self.db.execute_update("DELETE FROM course_offerings")
            Logger.info("✓ 现有开课计划数据已清空")
        except Exception as e:
            Logger.error(f"清空数据失败: {e}", exc_info=True)
            raise
    
    def import_offerings(self, csv_file: str = "data/course_offerings.csv", 
                        clear_existing: bool = True) -> tuple[int, int]:
        """
        导入开课计划数据
        
        Args:
            csv_file: CSV文件路径
            clear_existing: 是否清空现有数据
        
        Returns:
            (成功数, 失败数)
        """
        csv_path = Path(csv_file)
        if not csv_path.exists():
            Logger.error(f"CSV文件不存在: {csv_file}")
            return 0, 0
        
        # 是否清空现有数据
        if clear_existing:
            self.clear_existing_offerings()
        
        Logger.info(f"开始导入开课计划数据: {csv_file}")
        
        success_count = 0
        fail_count = 0
        
        try:
            # 使用 utf-8-sig 自动处理 BOM
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        # 准备开课计划数据
                        offering_data = {
                            'offering_id': int(row.get('offering_id', 0)) if row.get('offering_id') else None,
                            'course_id': row.get('course_id', '').strip(),
                            'teacher_id': row.get('teacher_id', '').strip(),
                            'semester': row.get('semester', '').strip(),
                            'class_time': row.get('class_time', '').strip(),
                            'classroom': row.get('classroom', '').strip(),
                            'max_students': int(row.get('max_students', 60)) if row.get('max_students') else 60,
                            'current_students': int(row.get('current_students', 0)) if row.get('current_students') else 0,
                            'status': row.get('status', 'open').strip(),
                            'department': row.get('department', '').strip(),
                            'is_cross_major_open': 1,  # 默认开放跨专业选课
                            'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # 验证必填字段
                        if not offering_data['course_id'] or not offering_data['teacher_id'] or not offering_data['semester']:
                            Logger.warning(f"跳过无效记录: {row}")
                            fail_count += 1
                            continue
                        
                        # 检查课程是否存在
                        course_exists = self.db.execute_query(
                            "SELECT course_id FROM courses WHERE course_id=?",
                            (offering_data['course_id'],)
                        )
                        
                        if not course_exists:
                            # 如果课程不存在，尝试从CSV中的课程信息创建
                            course_data = {
                                'course_id': offering_data['course_id'],
                                'course_name': row.get('course_name', '').strip(),
                                'credits': float(row.get('credits', 2.0)) if row.get('credits') else 2.0,
                                'hours': int(row.get('hours', 32)) if row.get('hours') else 32,
                                'course_type': row.get('course_type', '').strip(),
                                'department': row.get('department', '').strip(),
                                'max_students': offering_data['max_students'],
                                'is_public_elective': 1 if row.get('is_public_elective') == '1' else 0,
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            try:
                                self.db.insert_data('courses', course_data)
                                Logger.debug(f"创建课程: {course_data['course_id']} - {course_data['course_name']}")
                            except Exception as e:
                                Logger.warning(f"创建课程失败: {course_data['course_id']} - {e}")
                        
                        # 检查教师是否存在
                        teacher_exists = self.db.execute_query(
                            "SELECT teacher_id FROM teachers WHERE teacher_id=?",
                            (offering_data['teacher_id'],)
                        )
                        
                        if not teacher_exists:
                            # 如果教师不存在，创建教师记录
                            teacher_data = {
                                'teacher_id': offering_data['teacher_id'],
                                'name': row.get('teacher_name', '未知教师').strip(),
                                'password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxKCqyuZK',  # 默认密码
                                'title': row.get('teacher_title', '').strip(),
                                'department': row.get('teacher_department', '').strip() or row.get('department', '').strip(),
                                'status': 'active',
                                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            try:
                                self.db.insert_data('teachers', teacher_data)
                                Logger.debug(f"创建教师: {teacher_data['teacher_id']} - {teacher_data['name']}")
                            except Exception as e:
                                Logger.warning(f"创建教师失败: {teacher_data['teacher_id']} - {e}")
                        
                        # 插入开课计划
                        if offering_data['offering_id']:
                            # 如果有指定 offering_id，需要特殊处理
                            # 先尝试插入，如果失败则更新
                            try:
                                self.db.insert_data('course_offerings', offering_data)
                            except Exception:
                                # 如果插入失败（可能是ID冲突），尝试更新
                                offering_id = offering_data.pop('offering_id')
                                self.db.update_data(
                                    'course_offerings',
                                    offering_data,
                                    {'offering_id': offering_id}
                                )
                        else:
                            # 自动生成 offering_id
                            offering_data.pop('offering_id')
                            self.db.insert_data('course_offerings', offering_data)
                        
                        Logger.debug(f"导入开课: {offering_data['course_id']} - {offering_data['semester']} - {offering_data['teacher_id']}")
                        success_count += 1
                        
                    except Exception as e:
                        fail_count += 1
                        Logger.error(f"导入开课计划失败: {row.get('offering_id', 'unknown')} - {e}")
                        continue
        
        except Exception as e:
            Logger.error(f"读取CSV文件失败: {e}", exc_info=True)
            return success_count, fail_count
        
        Logger.info(f"开课计划数据导入完成: 成功 {success_count} 条，失败 {fail_count} 条")
        return success_count, fail_count
    
    def verify_import(self):
        """验证导入结果"""
        Logger.info("=" * 60)
        Logger.info("导入数据验证")
        Logger.info("=" * 60)
        
        # 验证开课计划数据
        offerings = self.db.execute_query("SELECT COUNT(*) as count FROM course_offerings")
        offering_count = offerings[0]['count'] if offerings else 0
        Logger.info(f"✓ 开课计划总数: {offering_count}")
        
        # 验证有时间和教室的开课计划
        with_schedule = self.db.execute_query("""
            SELECT COUNT(*) as count FROM course_offerings 
            WHERE class_time IS NOT NULL AND class_time != '' 
            AND classroom IS NOT NULL AND classroom != ''
        """)
        schedule_count = with_schedule[0]['count'] if with_schedule else 0
        Logger.info(f"✓ 有时间和教室的开课计划: {schedule_count}")
        
        # 显示部分开课计划
        sample_offerings = self.db.execute_query("""
            SELECT o.offering_id, o.course_id, c.course_name, o.semester, 
                   o.class_time, o.classroom, t.name as teacher_name
            FROM course_offerings o
            LEFT JOIN courses c ON o.course_id = c.course_id
            LEFT JOIN teachers t ON o.teacher_id = t.teacher_id
            LIMIT 5
        """)
        Logger.info("  示例开课计划:")
        for s in sample_offerings:
            Logger.info(f"    - {s['offering_id']}: {s['course_id']} {s['course_name']} "
                       f"({s['semester']}) {s['class_time']} @ {s['classroom']} - {s['teacher_name']}")
        
        Logger.info("=" * 60)
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()


def main():
    """主函数"""
    print("=" * 60)
    print("北京邮电大学教学管理系统 - 课程开课计划导入工具")
    print("=" * 60)
    print()
    
    # 初始化日志
    Logger.init()
    
    # 创建导入器
    importer = CourseOfferingImporter()
    
    try:
        # 询问是否清空现有数据
        clear = True
        if len(sys.argv) > 1 and sys.argv[1] == '--no-clear':
            clear = False
            print("⚠ 将追加导入，不清空现有数据")
        else:
            print("⚠ 将清空现有开课计划数据并重新导入")
        print()
        
        # 导入开课计划数据
        print("正在导入开课计划数据...")
        success, fail = importer.import_offerings("data/course_offerings.csv", clear_existing=clear)
        print(f"✓ 开课计划: 成功 {success} 条, 失败 {fail} 条")
        print()
        
        # 验证导入
        print("验证导入结果...")
        importer.verify_import()
        print()
        
        print("=" * 60)
        print("✓ 课程开课计划导入完成！")
        print("=" * 60)
        print()
        print("提示:")
        print("  - 开课计划已包含时间和教室信息")
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

