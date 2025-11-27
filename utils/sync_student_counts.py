"""
同步课程选课人数工具
修复 course_offerings.current_students 与实际 enrollments 记录不一致的问题
"""

import sqlite3
import os


def sync_student_counts(semester: str = None):
    """
    同步课程选课人数
    
    Args:
        semester: 学期（可选，如果指定则只同步该学期）
    """
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'bupt_teaching.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # 构建SQL查询
        if semester:
            sql = """
                UPDATE course_offerings 
                SET current_students = (
                    SELECT COUNT(*) 
                    FROM enrollments 
                    WHERE enrollments.offering_id = course_offerings.offering_id
                      AND enrollments.status IN ('enrolled', 'completed')
                      AND enrollments.semester = ?
                )
                WHERE semester = ?
            """
            params = (semester, semester)
            print(f"开始同步 {semester} 学期的选课人数...")
        else:
            sql = """
                UPDATE course_offerings 
                SET current_students = (
                    SELECT COUNT(*) 
                    FROM enrollments 
                    WHERE enrollments.offering_id = course_offerings.offering_id
                      AND enrollments.status IN ('enrolled', 'completed')
                )
            """
            params = ()
            print("开始同步所有学期的选课人数...")
        
        # 执行更新
        cursor.execute(sql, params)
        conn.commit()
        
        # 查询更新结果
        if semester:
            check_sql = """
                SELECT 
                    co.offering_id,
                    co.course_id,
                    c.course_name,
                    co.class_time,
                    co.classroom,
                    co.current_students as new_count
                FROM course_offerings co
                JOIN courses c ON co.course_id = c.course_id
                WHERE co.semester = ?
                ORDER BY co.offering_id
            """
            cursor.execute(check_sql, (semester,))
        else:
            check_sql = """
                SELECT 
                    co.offering_id,
                    co.course_id,
                    c.course_name,
                    co.class_time,
                    co.classroom,
                    co.current_students as new_count
                FROM course_offerings co
                JOIN courses c ON co.course_id = c.course_id
                ORDER BY co.offering_id
            """
            cursor.execute(check_sql)
        
        results = cursor.fetchall()
        
        # 统计信息
        total_updated = len(results)
        print(f"✅ 同步完成！共更新了 {total_updated} 个开课计划的选课人数")
        
        # 更新课程状态（满员/开放）
        update_status_sql = """
            UPDATE course_offerings
            SET status = CASE
                WHEN current_students >= max_students THEN 'full'
                ELSE 'open'
            END
        """
        if semester:
            update_status_sql += " WHERE semester = ?"
            cursor.execute(update_status_sql, (semester,))
        else:
            cursor.execute(update_status_sql)
        conn.commit()
        
        print("✅ 课程状态已更新")
        
    except Exception as e:
        print(f"❌ 同步选课人数失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="同步课程选课人数")
    parser.add_argument(
        "--semester",
        type=str,
        default=None,
        help="指定学期（如：2024-2025-1），不指定则同步所有学期"
    )
    
    args = parser.parse_args()
    
    sync_student_counts(args.semester)

