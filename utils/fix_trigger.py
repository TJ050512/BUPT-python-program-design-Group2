"""
修复数据库触发器：允许学生退课后重新选课
"""
import sqlite3
from pathlib import Path

def fix_trigger():
    """修复重复选课检查的触发器"""
    db_path = Path(__file__).parent.parent / "data" / "bupt_teaching.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        print("🔧 开始修复触发器...")
        
        # 1. 删除旧的触发器
        cursor.execute("DROP TRIGGER IF EXISTS trg_single_course_enrollment_bi")
        print("✓ 已删除旧触发器")
        
        # 2. 创建新的触发器（带status检查）
        cursor.executescript('''
            CREATE TRIGGER IF NOT EXISTS trg_single_course_enrollment_bi
            BEFORE INSERT ON enrollments
            BEGIN
                SELECT
                    CASE
                        -- 检查学生是否已经选了这门课程的任何一个班级（只检查enrolled和completed状态）
                        WHEN EXISTS (
                            SELECT 1
                            FROM enrollments e
                            -- 通过 course_offerings 表获取 course_id
                            JOIN course_offerings o ON e.offering_id = o.offering_id
                            WHERE e.student_id = NEW.student_id -- 目标学生
                              -- 当前尝试插入的 offering_id 对应的 course_id
                              AND o.course_id = (SELECT course_id FROM course_offerings WHERE offering_id = NEW.offering_id)
                              -- 只检查已选课（enrolled）和已完成（completed）的记录，忽略已退课（dropped）的记录
                              AND e.status IN ('enrolled', 'completed')
                        )
                        THEN RAISE(ABORT, '该学生已选了该课程的任一班级，不能重复选择')
                    END;
            END;
        ''')
        print("✓ 已创建新触发器（带status检查）")
        
        conn.commit()
        print("\n✅ 触发器修复完成！")
        print("现在学生退课后可以重新选课了")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_trigger()
