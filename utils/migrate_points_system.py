"""
积分制选课系统数据迁移脚本

功能：
1. 为students表添加course_points字段（默认200分）
2. 创建course_biddings表（课程竞价记录）
3. 创建points_transactions表（积分交易历史）
4. 为course_offerings表添加bidding_deadline和bidding_status字段
5. 为现有学生初始化200分积分
6. 为现有课程设置course_type（必修/选修）
7. 提供回滚功能

使用方法：
    python utils/migrate_points_system.py migrate    # 执行迁移
    python utils/migrate_points_system.py rollback   # 回滚迁移
    python utils/migrate_points_system.py status     # 查看迁移状态
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import Logger


class PointsSystemMigration:
    """积分制选课系统迁移管理器"""
    
    def __init__(self, db_path: str = "data/bupt_teaching.db"):
        """
        初始化迁移管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def connect(self):
        """连接数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            Logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            Logger.error(f"数据库连接失败: {e}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            Logger.info("数据库连接已关闭")
    
    def backup_database(self) -> bool:
        """
        备份数据库
        
        Returns:
            是否备份成功
        """
        try:
            import shutil
            shutil.copy2(self.db_path, self.backup_path)
            Logger.info(f"数据库备份成功: {self.backup_path}")
            return True
        except Exception as e:
            Logger.error(f"数据库备份失败: {e}")
            return False
    
    def check_migration_status(self) -> dict:
        """
        检查迁移状态
        
        Returns:
            迁移状态字典
        """
        status = {
            'students_course_points': False,
            'course_biddings_table': False,
            'points_transactions_table': False,
            'offerings_bidding_fields': False,
        }
        
        try:
            # 检查students表是否有course_points字段
            self.cursor.execute("PRAGMA table_info(students)")
            columns = [row[1] for row in self.cursor.fetchall()]
            status['students_course_points'] = 'course_points' in columns
            
            # 检查course_biddings表是否存在
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='course_biddings'"
            )
            status['course_biddings_table'] = self.cursor.fetchone() is not None
            
            # 检查points_transactions表是否存在
            self.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='points_transactions'"
            )
            status['points_transactions_table'] = self.cursor.fetchone() is not None
            
            # 检查course_offerings表是否有bidding字段
            self.cursor.execute("PRAGMA table_info(course_offerings)")
            columns = [row[1] for row in self.cursor.fetchall()]
            status['offerings_bidding_fields'] = (
                'bidding_deadline' in columns and 'bidding_status' in columns
            )
            
        except Exception as e:
            Logger.error(f"检查迁移状态失败: {e}")
        
        return status
    
    def migrate(self) -> Tuple[bool, str]:
        """
        执行迁移
        
        Returns:
            (是否成功, 消息)
        """
        try:
            # 检查当前状态
            status = self.check_migration_status()
            if all(status.values()):
                return True, "迁移已完成，无需重复执行"
            
            # 备份数据库
            if not self.backup_database():
                return False, "数据库备份失败，迁移中止"
            
            Logger.info("开始执行积分制选课系统迁移...")
            
            # 1. 为students表添加course_points字段
            if not status['students_course_points']:
                Logger.info("1. 为students表添加course_points字段...")
                self.cursor.execute("""
                    ALTER TABLE students ADD COLUMN course_points INTEGER DEFAULT 200
                """)
                self.conn.commit()
                Logger.info("✓ students表course_points字段添加成功")
            else:
                Logger.info("1. students表course_points字段已存在，跳过")
            
            # 2. 创建course_biddings表
            if not status['course_biddings_table']:
                Logger.info("2. 创建course_biddings表...")
                self.cursor.execute("""
                    CREATE TABLE course_biddings (
                        bidding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT NOT NULL,
                        offering_id INTEGER NOT NULL,
                        points_bid INTEGER NOT NULL,
                        bid_time TEXT DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id),
                        FOREIGN KEY (offering_id) REFERENCES course_offerings(offering_id),
                        UNIQUE(student_id, offering_id),
                        CHECK (points_bid >= 1 AND points_bid <= 100),
                        CHECK (status IN ('pending', 'accepted', 'rejected', 'cancelled'))
                    )
                """)
                self.conn.commit()
                Logger.info("✓ course_biddings表创建成功")
            else:
                Logger.info("2. course_biddings表已存在，跳过")
            
            # 3. 创建points_transactions表
            if not status['points_transactions_table']:
                Logger.info("3. 创建points_transactions表...")
                self.cursor.execute("""
                    CREATE TABLE points_transactions (
                        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id TEXT NOT NULL,
                        points_change INTEGER NOT NULL,
                        balance_after INTEGER NOT NULL,
                        transaction_type TEXT NOT NULL,
                        related_offering_id INTEGER,
                        reason TEXT,
                        operator_id TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (student_id) REFERENCES students(student_id),
                        FOREIGN KEY (related_offering_id) REFERENCES course_offerings(offering_id),
                        CHECK (transaction_type IN ('init', 'bid', 'refund', 'deduct', 'admin_adjust'))
                    )
                """)
                self.conn.commit()
                Logger.info("✓ points_transactions表创建成功")
            else:
                Logger.info("3. points_transactions表已存在，跳过")
            
            # 4. 为course_offerings表添加bidding字段
            if not status['offerings_bidding_fields']:
                Logger.info("4. 为course_offerings表添加bidding字段...")
                try:
                    self.cursor.execute("""
                        ALTER TABLE course_offerings ADD COLUMN bidding_deadline TEXT
                    """)
                except Exception:
                    pass  # 字段可能已存在
                
                try:
                    self.cursor.execute("""
                        ALTER TABLE course_offerings ADD COLUMN bidding_status TEXT DEFAULT 'open'
                    """)
                except Exception:
                    pass  # 字段可能已存在
                
                self.conn.commit()
                Logger.info("✓ course_offerings表bidding字段添加成功")
            else:
                Logger.info("4. course_offerings表bidding字段已存在，跳过")
            
            # 5. 为现有学生初始化200分积分
            Logger.info("5. 为现有学生初始化积分...")
            self.cursor.execute("""
                UPDATE students 
                SET course_points = 200 
                WHERE course_points IS NULL OR course_points = 0
            """)
            affected_rows = self.cursor.rowcount
            self.conn.commit()
            Logger.info(f"✓ 已为 {affected_rows} 名学生初始化200分积分")
            
            # 6. 为初始化的学生创建积分交易记录
            Logger.info("6. 创建积分初始化交易记录...")
            self.cursor.execute("""
                INSERT INTO points_transactions (student_id, points_change, balance_after, transaction_type, reason)
                SELECT student_id, 200, 200, 'init', '系统初始化积分'
                FROM students
                WHERE student_id NOT IN (
                    SELECT student_id FROM points_transactions WHERE transaction_type = 'init'
                )
            """)
            affected_rows = self.cursor.rowcount
            self.conn.commit()
            Logger.info(f"✓ 已创建 {affected_rows} 条积分初始化记录")
            
            # 7. 为现有课程设置course_type（基于课程名称和类型推断）
            Logger.info("7. 为现有课程设置course_type...")
            # 这里使用简单的规则：如果course_type包含"必修"则设为必修，否则设为选修
            self.cursor.execute("""
                SELECT course_id, course_type FROM courses
            """)
            courses = self.cursor.fetchall()
            
            for course in courses:
                course_id = course['course_id']
                course_type = course['course_type'] or ''
                
                # 简单推断：包含"必修"的为必修课，其他为选修课
                if '必修' in course_type:
                    new_type = '必修'
                else:
                    new_type = '选修'
                
                # 更新course_type为标准化的值
                self.cursor.execute("""
                    UPDATE courses SET course_type = ? WHERE course_id = ?
                """, (new_type, course_id))
            
            self.conn.commit()
            Logger.info(f"✓ 已为 {len(courses)} 门课程设置course_type")
            
            Logger.info("=" * 60)
            Logger.info("✅ 积分制选课系统迁移完成！")
            Logger.info(f"备份文件: {self.backup_path}")
            Logger.info("=" * 60)
            
            return True, "迁移成功完成"
            
        except Exception as e:
            self.conn.rollback()
            error_msg = f"迁移失败: {e}"
            Logger.error(error_msg)
            Logger.error("数据库已回滚，可以使用备份文件恢复")
            return False, error_msg
    
    def rollback(self) -> Tuple[bool, str]:
        """
        回滚迁移（删除新增的表和字段）
        
        注意：SQLite不支持DROP COLUMN，所以只能删除表
        
        Returns:
            (是否成功, 消息)
        """
        try:
            Logger.info("开始回滚积分制选课系统迁移...")
            
            # 1. 删除course_biddings表
            Logger.info("1. 删除course_biddings表...")
            self.cursor.execute("DROP TABLE IF EXISTS course_biddings")
            self.conn.commit()
            Logger.info("✓ course_biddings表已删除")
            
            # 2. 删除points_transactions表
            Logger.info("2. 删除points_transactions表...")
            self.cursor.execute("DROP TABLE IF EXISTS points_transactions")
            self.conn.commit()
            Logger.info("✓ points_transactions表已删除")
            
            # 3. 清空students表的course_points字段（设为NULL）
            Logger.info("3. 清空students表的course_points字段...")
            self.cursor.execute("UPDATE students SET course_points = NULL")
            self.conn.commit()
            Logger.info("✓ students表course_points字段已清空")
            
            # 4. 清空course_offerings表的bidding字段
            Logger.info("4. 清空course_offerings表的bidding字段...")
            self.cursor.execute("""
                UPDATE course_offerings 
                SET bidding_deadline = NULL, bidding_status = NULL
            """)
            self.conn.commit()
            Logger.info("✓ course_offerings表bidding字段已清空")
            
            Logger.info("=" * 60)
            Logger.info("✅ 积分制选课系统迁移已回滚！")
            Logger.info("注意：由于SQLite限制，字段未被删除，仅清空了数据")
            Logger.info("=" * 60)
            
            return True, "回滚成功完成"
            
        except Exception as e:
            self.conn.rollback()
            error_msg = f"回滚失败: {e}"
            Logger.error(error_msg)
            return False, error_msg
    
    def print_status(self):
        """打印迁移状态"""
        status = self.check_migration_status()
        
        print("\n" + "=" * 60)
        print("积分制选课系统迁移状态")
        print("=" * 60)
        print(f"students表course_points字段: {'✓ 已迁移' if status['students_course_points'] else '✗ 未迁移'}")
        print(f"course_biddings表: {'✓ 已创建' if status['course_biddings_table'] else '✗ 未创建'}")
        print(f"points_transactions表: {'✓ 已创建' if status['points_transactions_table'] else '✗ 未创建'}")
        print(f"course_offerings表bidding字段: {'✓ 已添加' if status['offerings_bidding_fields'] else '✗ 未添加'}")
        print("=" * 60)
        
        if all(status.values()):
            print("状态: ✅ 迁移已完成")
        else:
            print("状态: ⚠️  迁移未完成或部分完成")
        print("=" * 60 + "\n")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python utils/migrate_points_system.py migrate    # 执行迁移")
        print("  python utils/migrate_points_system.py rollback   # 回滚迁移")
        print("  python utils/migrate_points_system.py status     # 查看迁移状态")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    # 创建迁移管理器
    migration = PointsSystemMigration()
    
    try:
        migration.connect()
        
        if command == 'migrate':
            success, message = migration.migrate()
            if success:
                print(f"\n✅ {message}\n")
                sys.exit(0)
            else:
                print(f"\n❌ {message}\n")
                sys.exit(1)
        
        elif command == 'rollback':
            confirm = input("⚠️  确认要回滚迁移吗？这将删除所有积分数据！(yes/no): ")
            if confirm.lower() == 'yes':
                success, message = migration.rollback()
                if success:
                    print(f"\n✅ {message}\n")
                    sys.exit(0)
                else:
                    print(f"\n❌ {message}\n")
                    sys.exit(1)
            else:
                print("\n已取消回滚操作\n")
                sys.exit(0)
        
        elif command == 'status':
            migration.print_status()
            sys.exit(0)
        
        else:
            print(f"未知命令: {command}")
            print("可用命令: migrate, rollback, status")
            sys.exit(1)
    
    finally:
        migration.close()


if __name__ == "__main__":
    main()
