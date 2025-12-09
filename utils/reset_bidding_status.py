"""
重置课程竞价状态 - 允许学生重新投入积分
"""

import sys
from pathlib import Path

# 添加项目根目录到path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.database import Database
from utils.logger import Logger

def reset_bidding_status(offering_id=111):
    """重置课程的竞价状态为open"""
    
    db = Database()
    
    Logger.info("=" * 70)
    Logger.info(f"重置课程 (开课ID: {offering_id}) 的竞价状态")
    Logger.info("=" * 70)
    
    # 1. 查询当前状态
    sql_check = """
        SELECT 
            co.offering_id,
            co.bidding_status,
            co.status as offering_status,
            c.course_id,
            c.course_name,
            t.name as teacher_name
        FROM course_offerings co
        JOIN courses c ON co.course_id = c.course_id
        JOIN teachers t ON co.teacher_id = t.teacher_id
        WHERE co.offering_id = ?
    """
    
    course_info = db.execute_query(sql_check, (offering_id,))
    
    if not course_info:
        Logger.error(f"未找到开课ID为 {offering_id} 的课程")
        return
    
    info = course_info[0]
    Logger.info(f"\n课程信息：")
    Logger.info(f"  课程代码: {info['course_id']}")
    Logger.info(f"  课程名称: {info['course_name']}")
    Logger.info(f"  授课教师: {info['teacher_name']}")
    Logger.info(f"  当前竞价状态: {info['bidding_status']}")
    Logger.info(f"  开课状态: {info['offering_status']}")
    
    if info['bidding_status'] == 'open':
        Logger.info("\n✓ 竞价状态已经是'open'，无需重置")
        return
    
    # 2. 重置竞价状态
    Logger.info(f"\n正在重置竞价状态: {info['bidding_status']} -> open")
    
    rows_affected = db.update_data(
        'course_offerings',
        {'bidding_status': 'open'},
        {'offering_id': offering_id}
    )
    
    if rows_affected > 0:
        Logger.info("✓ 竞价状态已成功重置为 'open'")
        Logger.info("  现在学生可以重新投入积分了！")
    else:
        Logger.error("✗ 重置失败")
    
    Logger.info("\n" + "=" * 70)
    Logger.info("操作完成")
    Logger.info("=" * 70)

if __name__ == "__main__":
    # 默认重置开课ID为111的课程（创新创业基础）
    reset_bidding_status(111)
