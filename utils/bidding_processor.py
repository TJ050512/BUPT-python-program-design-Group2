"""
竞价截止自动处理模块 - 北京邮电大学教学管理系统
负责检查竞价截止时间并自动处理录取结果
"""

from typing import Tuple, List, Dict
from datetime import datetime
from utils.logger import Logger
from core.bidding_manager import BiddingManager
from core.points_manager import PointsManager


class BiddingProcessor:
    """竞价截止自动处理器"""
    
    def __init__(self, db):
        """
        初始化竞价处理器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.points_manager = PointsManager(db)
        self.bidding_manager = BiddingManager(db, self.points_manager)
        Logger.info("竞价处理器初始化完成")
    
    def check_and_process_deadlines(self) -> Tuple[bool, str, Dict]:
        """
        检查所有竞价截止时间已到的课程并处理录取结果
        
        Returns:
            Tuple[bool, str, Dict]: (是否成功, 消息, 处理详情)
            处理详情包含：
            - total_courses: 处理的课程总数
            - successful: 成功处理的课程数
            - failed: 失败的课程数
            - details: 每门课程的处理结果列表
        """
        try:
            Logger.info("开始检查竞价截止时间...")
            
            # 1. 查询所有需要处理的课程
            # 条件：bidding_status='open' 且 bidding_deadline 已过
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            courses_to_process = self.db.execute_query("""
                SELECT 
                    offering_id,
                    course_id,
                    bidding_deadline,
                    bidding_status
                FROM course_offerings
                WHERE bidding_status = 'open'
                  AND bidding_deadline IS NOT NULL
                  AND bidding_deadline <= ?
            """, (current_time,))
            
            if not courses_to_process:
                Logger.info("没有需要处理的课程")
                return True, "没有需要处理的课程", {
                    'total_courses': 0,
                    'successful': 0,
                    'failed': 0,
                    'details': []
                }
            
            Logger.info(f"找到 {len(courses_to_process)} 门需要处理的课程")
            
            # 2. 逐个处理每门课程
            results = {
                'total_courses': len(courses_to_process),
                'successful': 0,
                'failed': 0,
                'details': []
            }
            
            for course in courses_to_process:
                offering_id = course['offering_id']
                course_id = course['course_id']
                deadline = course['bidding_deadline']
                
                Logger.info(f"处理课程: offering_id={offering_id}, course_id={course_id}, deadline={deadline}")
                
                # 3. 调用 BiddingManager 处理录取
                success, message = self.bidding_manager.process_bidding_results(offering_id)
                
                # 4. 记录处理结果
                course_result = {
                    'offering_id': offering_id,
                    'course_id': course_id,
                    'deadline': deadline,
                    'success': success,
                    'message': message
                }
                
                results['details'].append(course_result)
                
                if success:
                    results['successful'] += 1
                    Logger.info(f"课程 {offering_id} 处理成功: {message}")
                else:
                    results['failed'] += 1
                    Logger.error(f"课程 {offering_id} 处理失败: {message}")
            
            # 5. 生成总结消息
            summary = f"处理完成：共 {results['total_courses']} 门课程，成功 {results['successful']} 门，失败 {results['failed']} 门"
            Logger.info(summary)
            
            return True, summary, results
            
        except Exception as e:
            error_msg = f"检查和处理竞价截止失败: {e}"
            Logger.error(error_msg, exc_info=True)
            return False, error_msg, {
                'total_courses': 0,
                'successful': 0,
                'failed': 0,
                'details': [],
                'error': str(e)
            }
    
    def process_single_course(self, offering_id: int) -> Tuple[bool, str]:
        """
        手动处理单门课程的竞价结果
        
        Args:
            offering_id: 开课ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            Logger.info(f"手动处理课程竞价: offering_id={offering_id}")
            
            # 检查课程是否存在
            course_info = self.db.execute_query("""
                SELECT 
                    offering_id,
                    course_id,
                    bidding_deadline,
                    bidding_status
                FROM course_offerings
                WHERE offering_id = ?
            """, (offering_id,))
            
            if not course_info:
                return False, "课程不存在"
            
            info = course_info[0]
            
            # 检查是否已经处理过
            if info['bidding_status'] == 'processed':
                return False, "该课程竞价已处理，无需重复处理"
            
            # 调用 BiddingManager 处理录取
            success, message = self.bidding_manager.process_bidding_results(offering_id)
            
            if success:
                Logger.info(f"手动处理课程 {offering_id} 成功: {message}")
            else:
                Logger.error(f"手动处理课程 {offering_id} 失败: {message}")
            
            return success, message
            
        except Exception as e:
            error_msg = f"手动处理课程失败: {e}"
            Logger.error(error_msg, exc_info=True)
            return False, error_msg
    
    def get_pending_courses(self) -> List[Dict]:
        """
        获取所有待处理的课程列表
        
        Returns:
            List[Dict]: 待处理课程列表
        """
        try:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            courses = self.db.execute_query("""
                SELECT 
                    co.offering_id,
                    co.course_id,
                    c.course_name,
                    co.bidding_deadline,
                    co.bidding_status,
                    co.max_students,
                    co.current_students,
                    COUNT(cb.bidding_id) as pending_bids
                FROM course_offerings co
                JOIN courses c ON co.course_id = c.course_id
                LEFT JOIN course_biddings cb ON co.offering_id = cb.offering_id 
                    AND cb.status = 'pending'
                WHERE co.bidding_status = 'open'
                  AND co.bidding_deadline IS NOT NULL
                  AND co.bidding_deadline <= ?
                GROUP BY co.offering_id
            """, (current_time,))
            
            return courses
            
        except Exception as e:
            Logger.error(f"获取待处理课程列表失败: {e}", exc_info=True)
            return []


def main():
    """
    主函数 - 可作为定时任务运行
    """
    from data.database import Database
    
    try:
        # 初始化数据库
        db = Database()
        
        # 创建处理器
        processor = BiddingProcessor(db)
        
        # 执行处理
        success, message, results = processor.check_and_process_deadlines()
        
        # 输出结果
        print(f"\n{'='*60}")
        print(f"竞价截止自动处理结果")
        print(f"{'='*60}")
        print(f"状态: {'成功' if success else '失败'}")
        print(f"消息: {message}")
        print(f"\n处理详情:")
        print(f"  总课程数: {results.get('total_courses', 0)}")
        print(f"  成功: {results.get('successful', 0)}")
        print(f"  失败: {results.get('failed', 0)}")
        
        if results.get('details'):
            print(f"\n各课程处理结果:")
            for detail in results['details']:
                status = "✓" if detail['success'] else "✗"
                print(f"  {status} 课程 {detail['offering_id']} ({detail['course_id']}): {detail['message']}")
        
        print(f"{'='*60}\n")
        
        # 关闭数据库
        db.close()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"执行失败: {e}")
        Logger.error(f"竞价处理主函数执行失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
