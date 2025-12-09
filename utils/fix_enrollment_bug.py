"""
修复enrollment bug - 积分被扣但没有创建enrollment记录的问题
"""

import sys
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.database import Database
from core.points_manager import PointsManager
from utils.logger import Logger

def fix_enrollment_bug():
    """修复积分被扣但没有enrollment记录的bug"""
    
    # 初始化数据库
    db = Database()
    points_manager = PointsManager(db)
    
    Logger.info("=" * 60)
    Logger.info("开始检查并修复enrollment bug...")
    Logger.info("=" * 60)
    
    # === 问题1: 查找accepted状态但没有对应enrollment记录的竞价 ===
    sql_accepted = """
        SELECT 
            cb.bidding_id,
            cb.student_id,
            cb.offering_id,
            cb.points_bid,
            s.name as student_name,
            c.course_name
        FROM course_biddings cb
        JOIN students s ON cb.student_id = s.student_id
        JOIN course_offerings co ON cb.offering_id = co.offering_id
        JOIN courses c ON co.course_id = c.course_id
        WHERE cb.status = 'accepted'
          AND NOT EXISTS (
              SELECT 1 FROM enrollments e 
              WHERE e.student_id = cb.student_id 
                AND e.offering_id = cb.offering_id
                AND e.status = 'enrolled'
          )
    """
    
    broken_records = db.execute_query(sql_accepted)
    
    if broken_records:
        Logger.info(f"[问题1] 发现 {len(broken_records)} 条accepted但无enrollment的记录")
        
        for record in broken_records:
            student_id = record['student_id']
            student_name = record['student_name']
            offering_id = record['offering_id']
            points = record['points_bid']
            course_name = record['course_name']
            bidding_id = record['bidding_id']
            
            Logger.info(f"  处理: {student_name} ({student_id}) - {course_name}, 积分: {points}")
            
            # 退还积分
            success, msg = points_manager.refund_points(
                student_id,
                points,
                f"修复bug退还积分（课程: {course_name}）"
            )
            
            if success:
                # 将竞价状态改回pending
                db.update_data(
                    'course_biddings',
                    {'status': 'pending'},
                    {'bidding_id': bidding_id}
                )
                
                # 减少课程的current_students
                db.execute_query("""
                    UPDATE course_offerings
                    SET current_students = current_students - 1
                    WHERE offering_id = ? AND current_students > 0
                """, (offering_id,))
                
                Logger.info(f"    ✓ 已退还 {points} 分，竞价状态重置为pending，人数-1")
            else:
                Logger.error(f"    ✗ 退还积分失败: {msg}")
    else:
        Logger.info("[问题1] 未发现accepted但无enrollment的记录 ✓")
    
    # === 问题2: 修复current_students与实际enrollment不一致的问题 ===
    Logger.info("\n" + "=" * 60)
    Logger.info("[问题2] 检查current_students计数是否准确...")
    
    sql_count_check = """
        SELECT 
            co.offering_id,
            co.current_students,
            c.course_name,
            COUNT(e.enrollment_id) as actual_count
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.course_id
        LEFT JOIN enrollments e ON co.offering_id = e.offering_id AND e.status = 'enrolled'
        GROUP BY co.offering_id, co.current_students, c.course_name
        HAVING co.current_students != COUNT(e.enrollment_id)
    """
    
    inconsistent_counts = db.execute_query(sql_count_check)
    
    if inconsistent_counts:
        Logger.info(f"  发现 {len(inconsistent_counts)} 个课程的人数计数不一致")
        
        for record in inconsistent_counts:
            offering_id = record['offering_id']
            wrong_count = record['current_students']
            correct_count = record['actual_count']
            course_name = record['course_name']
            
            Logger.info(f"  课程: {course_name} (ID: {offering_id})")
            Logger.info(f"    错误计数: {wrong_count}, 正确计数: {correct_count}")
            
            # 修正current_students
            db.update_data(
                'course_offerings',
                {'current_students': correct_count},
                {'offering_id': offering_id}
            )
            
            Logger.info(f"    ✓ 已修正为 {correct_count}")
    else:
        Logger.info("  所有课程的人数计数都是准确的 ✓")
    
    Logger.info("\n" + "=" * 60)
    Logger.info("修复完成！")
    Logger.info("=" * 60)
    
if __name__ == "__main__":
    fix_enrollment_bug()
