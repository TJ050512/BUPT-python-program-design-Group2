#!/usr/bin/env python3
"""
修复开课计划选课人数脚本
用于同步 course_offerings.current_students 字段与实际选课数量
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

import sqlite3
from utils.logger import Logger


def fix_course_counts(db_path: str = "data/bupt_teaching.db"):
    """
    修复开课计划的选课人数统计
    
    Args:
        db_path: 数据库文件路径
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        Logger.info("开始修复开课计划选课人数...")
        
        # 1. 更新 current_students 为实际选课人数
        cursor.execute('''
            UPDATE course_offerings
            SET current_students = (
                SELECT COUNT(*)
                FROM enrollments
                WHERE enrollments.offering_id = course_offerings.offering_id
                AND enrollments.status IN ('enrolled', 'completed')
            )
        ''')
        
        affected_rows = cursor.rowcount
        Logger.info(f"已更新 {affected_rows} 条开课计划记录")
        
        # 2. 同步状态字段
        cursor.execute('''
            UPDATE course_offerings
            SET status = CASE
                WHEN current_students >= max_students THEN 'full'
                ELSE 'open'
            END
        ''')
        
        Logger.info("已同步开课状态")
        
        conn.commit()
        
        # 3. 验证结果
        cursor.execute('''
            SELECT COUNT(*) as total, 
                   SUM(current_students) as sum_students,
                   COUNT(CASE WHEN status='full' THEN 1 END) as full_count,
                   COUNT(CASE WHEN status='open' THEN 1 END) as open_count
            FROM course_offerings
        ''')
        
        result = cursor.fetchone()
        Logger.info(f"修复完成！统计信息:")
        Logger.info(f"  - 总开课计划: {result[0]}")
        Logger.info(f"  - 总选课人数: {result[1]}")
        Logger.info(f"  - 已满课程: {result[2]}")
        Logger.info(f"  - 开放课程: {result[3]}")
        
        conn.close()
        return True
        
    except Exception as e:
        Logger.error(f"修复失败: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="修复开课计划选课人数统计")
    parser.add_argument("--db", default="data/bupt_teaching.db", 
                       help="数据库文件路径 (默认: data/bupt_teaching.db)")
    
    args = parser.parse_args()
    
    success = fix_course_counts(args.db)
    
    if success:
        print("\n✓ 修复成功！")
        sys.exit(0)
    else:
        print("\n✗ 修复失败，请查看日志获取详细信息")
        sys.exit(1)

