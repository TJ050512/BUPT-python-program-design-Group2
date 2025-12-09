"""
验证迁移完整性并修复缺失的初始化记录
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import Logger


def verify_and_fix_migration(db_path: str = "data/bupt_teaching.db"):
    """验证并修复迁移"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查有多少学生有200分但没有init记录
        cursor.execute("""
            SELECT COUNT(*) FROM students s
            WHERE s.course_points = 200
            AND NOT EXISTS (
                SELECT 1 FROM points_transactions pt
                WHERE pt.student_id = s.student_id
                AND pt.transaction_type = 'init'
            )
        """)
        missing_count = cursor.fetchone()[0]
        
        if missing_count > 0:
            Logger.info(f"发现 {missing_count} 名学生缺少初始化交易记录")
            Logger.info("正在创建缺失的记录...")
            
            # 为这些学生创建init记录
            cursor.execute("""
                INSERT INTO points_transactions (student_id, points_change, balance_after, transaction_type, reason)
                SELECT s.student_id, 200, 200, 'init', '系统初始化积分'
                FROM students s
                WHERE s.course_points = 200
                AND NOT EXISTS (
                    SELECT 1 FROM points_transactions pt
                    WHERE pt.student_id = s.student_id
                    AND pt.transaction_type = 'init'
                )
            """)
            
            conn.commit()
            Logger.info(f"✓ 已创建 {cursor.rowcount} 条初始化记录")
        else:
            Logger.info("✓ 所有学生都有完整的初始化记录")
        
        # 显示统计信息
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM points_transactions WHERE transaction_type = 'init'")
        init_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT student_id) FROM points_transactions WHERE transaction_type = 'init'")
        students_with_init = cursor.fetchone()[0]
        
        print("\n" + "=" * 60)
        print("迁移验证结果")
        print("=" * 60)
        print(f"学生总数: {total_students}")
        print(f"初始化记录数: {init_records}")
        print(f"有初始化记录的学生数: {students_with_init}")
        print("=" * 60)
        
        if total_students == students_with_init:
            print("状态: ✅ 迁移完整")
        else:
            print(f"状态: ⚠️  有 {total_students - students_with_init} 名学生缺少初始化记录")
        print("=" * 60 + "\n")
        
    except Exception as e:
        Logger.error(f"验证失败: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    verify_and_fix_migration()
