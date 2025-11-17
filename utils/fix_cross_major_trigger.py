"""
修复跨专业名额触发器
更新触发器逻辑，确保只有真正跨专业选课时才检查名额限制

用法:
    python3 utils/fix_cross_major_trigger.py
"""

import sqlite3
from pathlib import Path


def fix_cross_major_trigger(db_path: str = "data/bupt_teaching.db"):
    """修复跨专业名额触发器"""
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"✗ 数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("修复跨专业名额触发器")
    print("=" * 60)
    
    try:
        # 删除旧的触发器
        print("\n删除旧触发器...")
        cursor.execute("DROP TRIGGER IF EXISTS trg_cross_major_quota_bi")
        print("✓ 已删除旧触发器")
        
        # 创建新的触发器
        print("\n创建新触发器...")
        cursor.execute('''
            CREATE TRIGGER trg_cross_major_quota_bi
            BEFORE INSERT ON enrollments
            BEGIN
                SELECT
                CASE
                    -- 只有当学生选择的是其他专业的课程时才检查跨专业名额
                    -- 即：学生的major_id不在该课程的任何program_courses记录中
                    WHEN EXISTS (
                        SELECT 1
                        FROM course_offerings o
                        JOIN students s ON s.student_id = NEW.student_id
                        WHERE o.offering_id = NEW.offering_id
                            AND s.major_id IS NOT NULL
                            -- 检查是否存在该学生专业的program_courses记录
                            AND NOT EXISTS (
                                SELECT 1
                                FROM program_courses pc
                                WHERE pc.course_id = o.course_id
                                    AND pc.major_id = s.major_id
                                    AND pc.course_category IN ('必修','选修')
                            )
                            -- 并且该课程确实有program_courses记录（说明是专业课程）
                            AND EXISTS (
                                SELECT 1
                                FROM program_courses pc2
                                WHERE pc2.course_id = o.course_id
                                    AND pc2.course_category IN ('必修','选修')
                            )
                    )
                    THEN
                    CASE
                        WHEN (
                            SELECT MIN(pcx.cross_major_quota) - (
                                SELECT COUNT(*)
                                FROM enrollments e
                                JOIN students sx ON sx.student_id = e.student_id
                                JOIN course_offerings ox ON ox.offering_id = e.offering_id
                                WHERE e.offering_id = NEW.offering_id
                                    AND e.status = 'enrolled'
                                    AND sx.major_id IS NOT NULL
                                    -- 统计跨专业选课的学生数（不在任何program_courses记录中的学生）
                                    AND NOT EXISTS (
                                        SELECT 1
                                        FROM program_courses pc3
                                        WHERE pc3.course_id = ox.course_id
                                            AND pc3.major_id = sx.major_id
                                            AND pc3.course_category IN ('必修','选修')
                                    )
                            )
                            FROM program_courses pcx
                            JOIN course_offerings ox ON ox.course_id = pcx.course_id
                            WHERE ox.offering_id = NEW.offering_id
                                AND pcx.course_category IN ('必修','选修')
                        ) <= 0
                        THEN RAISE(ABORT,'跨专业名额已满')
                    END
                END;
            END;
        ''')
        
        conn.commit()
        print("✓ 新触发器创建成功")
        
        # 验证触发器是否存在
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='trigger' AND name='trg_cross_major_quota_bi'
        """)
        result = cursor.fetchone()
        if result:
            print(f"\n✓ 触发器验证成功: {result[0]}")
        else:
            print("\n✗ 触发器验证失败")
        
    except Exception as e:
        print(f"\n✗ 修复触发器失败: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\n✓ 数据库连接已关闭")


if __name__ == "__main__":
    fix_cross_major_trigger()

