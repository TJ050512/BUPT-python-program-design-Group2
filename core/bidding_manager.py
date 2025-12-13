"""
竞价管理模块 - 北京邮电大学教学管理系统
负责选修课的积分投入、修改、取消和录取处理
"""

from typing import Optional, List, Dict, Tuple
from datetime import datetime
from utils.logger import Logger


class BiddingManager:
    """竞价管理器 - 管理选修课积分竞价"""
    
    # 单门课程最大投入积分
    MAX_BID_POINTS = 100
    
    def __init__(self, db, points_manager):
        """
        初始化竞价管理器
        
        Args:
            db: 数据库实例
            points_manager: 积分管理器实例
        """
        self.db = db
        self.points_manager = points_manager
        Logger.info("竞价管理器初始化完成")
    
    def place_bid(self, student_id: str, offering_id: int, 
                  points: int) -> Tuple[bool, str]:
        """
        学生为选修课投入积分
        
        Args:
            student_id: 学生学号
            offering_id: 开课ID
            points: 投入的积分
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 1. 验证积分范围
            if points < 1 or points > self.MAX_BID_POINTS:
                return False, f"投入积分必须在1-{self.MAX_BID_POINTS}之间"
            
            # 2. 获取学生当前积分
            current_points = self.points_manager.get_student_points(student_id)
            
            # 3. 计算已投入的积分总和
            pending_bids = self.db.execute_query("""
                SELECT SUM(points_bid) as total
                FROM course_biddings
                WHERE student_id=? AND status='pending'
            """, (student_id,))
            
            total_pending = pending_bids[0].get('total', 0) if pending_bids else 0
            total_pending = total_pending if total_pending is not None else 0
            
            # 4. 验证剩余积分是否足够
            available_points = current_points - total_pending
            if points > available_points:
                return False, f"积分不足，当前剩余{available_points}分"
            
            # 5. 检查是否已经投入过（排除已取消的记录）
            existing_bid = self.db.execute_query("""
                SELECT bidding_id, status FROM course_biddings
                WHERE student_id=? AND offering_id=?
            """, (student_id, offering_id))
            
            if existing_bid:
                bid_status = existing_bid[0].get('status')
                if bid_status == 'cancelled':
                    # 如果之前取消过，删除旧记录，允许重新投入
                    self.db.delete_data('course_biddings', {
                        'student_id': student_id,
                        'offering_id': offering_id,
                        'status': 'cancelled'
                    })
                    Logger.info(f"删除已取消的竞价记录: student_id={student_id}, offering_id={offering_id}")
                else:
                    return False, "您已为该课程投入积分，请使用修改功能"
            
            # 6. 检查竞价是否已截止
            offering_info = self.db.execute_query("""
                SELECT bidding_deadline, bidding_status
                FROM course_offerings
                WHERE offering_id=?
            """, (offering_id,))
            
            if not offering_info:
                return False, "课程不存在"
            
            deadline = offering_info[0].get('bidding_deadline')
            status = offering_info[0].get('bidding_status', 'open')
            
            if status != 'open':
                return False, "竞价已截止，无法投入"
            
            if deadline:
                deadline_dt = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
                if datetime.now() > deadline_dt:
                    return False, "竞价已截止，无法投入"
            
            # 7. 插入竞价记录
            bid_data = {
                'student_id': student_id,
                'offering_id': offering_id,
                'points_bid': points,
                'bid_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'pending',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            bidding_id = self.db.insert_data('course_biddings', bid_data)
            
            if not bidding_id:
                return False, "投入积分失败"
            
            Logger.info(f"学生投入积分成功: {student_id}, 课程: {offering_id}, 积分: {points}")
            return True, f"投入成功，已投入{points}分"
            
        except Exception as e:
            Logger.error(f"投入积分失败: {e}", exc_info=True)
            return False, "投入积分失败"

    def modify_bid(self, student_id: str, offering_id: int, 
                   new_points: int) -> Tuple[bool, str]:
        """
        修改已投入的积分
        
        Args:
            student_id: 学生学号
            offering_id: 开课ID
            new_points: 新的投入积分
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 1. 验证积分范围
            if new_points < 1 or new_points > self.MAX_BID_POINTS:
                return False, f"投入积分必须在1-{self.MAX_BID_POINTS}之间"
            
            # 2. 检查竞价是否已截止
            offering_info = self.db.execute_query("""
                SELECT bidding_deadline, bidding_status
                FROM course_offerings
                WHERE offering_id=?
            """, (offering_id,))
            
            if not offering_info:
                return False, "课程不存在"
            
            deadline = offering_info[0].get('bidding_deadline')
            status = offering_info[0].get('bidding_status', 'open')
            
            if status != 'open':
                return False, "竞价已截止，无法修改"
            
            if deadline:
                deadline_dt = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
                if datetime.now() > deadline_dt:
                    return False, "竞价已截止，无法修改"
            
            # 3. 获取现有投入记录
            existing_bid = self.db.execute_query("""
                SELECT bidding_id, points_bid, status
                FROM course_biddings
                WHERE student_id=? AND offering_id=?
            """, (student_id, offering_id))
            
            if not existing_bid:
                return False, "您尚未为该课程投入积分"
            
            if existing_bid[0]['status'] != 'pending':
                return False, "该投入已处理，无法修改"
            
            old_points = existing_bid[0]['points_bid']
            
            # 4. 获取学生当前积分
            current_points = self.points_manager.get_student_points(student_id)
            
            # 5. 计算其他课程的已投入积分
            other_bids = self.db.execute_query("""
                SELECT SUM(points_bid) as total
                FROM course_biddings
                WHERE student_id=? AND status='pending' AND offering_id!=?
            """, (student_id, offering_id))
            
            other_total = other_bids[0].get('total', 0) if other_bids else 0
            other_total = other_total if other_total is not None else 0
            
            # 6. 验证剩余积分是否足够
            available_points = current_points - other_total
            if new_points > available_points:
                return False, f"积分不足，当前剩余{available_points}分"
            
            # 7. 更新投入记录
            rows_affected = self.db.update_data(
                'course_biddings',
                {
                    'points_bid': new_points,
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    'student_id': student_id,
                    'offering_id': offering_id
                }
            )
            
            if rows_affected == 0:
                return False, "修改失败"
            
            Logger.info(f"修改投入积分成功: {student_id}, 课程: {offering_id}, {old_points}->{new_points}")
            return True, f"修改成功，当前投入{new_points}分"
            
        except Exception as e:
            Logger.error(f"修改投入积分失败: {e}", exc_info=True)
            return False, "修改投入积分失败"
    
    def cancel_bid(self, student_id: str, offering_id: int) -> Tuple[bool, str]:
        """
        取消积分投入
        
        Args:
            student_id: 学生学号
            offering_id: 开课ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 1. 检查竞价是否已截止
            offering_info = self.db.execute_query("""
                SELECT bidding_deadline, bidding_status
                FROM course_offerings
                WHERE offering_id=?
            """, (offering_id,))
            
            if not offering_info:
                return False, "课程不存在"
            
            deadline = offering_info[0].get('bidding_deadline')
            status = offering_info[0].get('bidding_status', 'open')
            
            if status != 'open':
                return False, "竞价已截止，无法取消"
            
            if deadline:
                deadline_dt = datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
                if datetime.now() > deadline_dt:
                    return False, "竞价已截止，无法取消"
            
            # 2. 获取现有投入记录
            existing_bid = self.db.execute_query("""
                SELECT bidding_id, points_bid, status
                FROM course_biddings
                WHERE student_id=? AND offering_id=?
            """, (student_id, offering_id))
            
            if not existing_bid:
                return False, "您尚未为该课程投入积分"
            
            bid_status = existing_bid[0]['status']
            if bid_status not in ('pending', 'rejected'):
                return False, "该投入已处理，无法取消"
            
            points = existing_bid[0]['points_bid']
            
            # 3. 返还积分（如果状态是pending，说明积分已扣除）
            if bid_status == 'pending':
                success, msg = self.points_manager.refund_points(
                    student_id,
                    points,
                    f"取消竞价退还积分（开课ID: {offering_id}）"
                )
                
                if not success:
                    return False, f"返还积分失败：{msg}"
            
            # 4. 更新状态为cancelled
            rows_affected = self.db.update_data(
                'course_biddings',
                {
                    'status': 'cancelled',
                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    'student_id': student_id,
                    'offering_id': offering_id
                }
            )
            
            if rows_affected == 0:
                # 回滚积分
                if bid_status == 'pending':
                    self.points_manager.deduct_points(
                        student_id,
                        points,
                        f"回滚：取消竞价失败（开课ID: {offering_id}）"
                    )
                return False, "取消失败"
            
            Logger.info(f"取消投入成功: {student_id}, 课程: {offering_id}, 退还: {points}")
            return True, f"取消成功，已退还{points}分"
            
        except Exception as e:
            Logger.error(f"取消投入失败: {e}", exc_info=True)
            return False, "取消投入失败"
    
    def get_bid_info(self, student_id: str, offering_id: int) -> Optional[Dict]:
        """
        获取学生对某课程的投入信息（排除已取消的记录）
        
        Args:
            student_id: 学生学号
            offering_id: 开课ID
        
        Returns:
            Optional[Dict]: 投入信息，如果不存在或已取消返回None
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    bidding_id,
                    points_bid,
                    bid_time,
                    status,
                    created_at,
                    updated_at
                FROM course_biddings
                WHERE student_id=? AND offering_id=? AND status != 'cancelled'
            """, (student_id, offering_id))
            
            if result:
                return result[0]
            return None
            
        except Exception as e:
            Logger.error(f"查询投入信息失败: {e}", exc_info=True)
            return None
    
    def get_course_bidding_status(self, offering_id: int) -> Dict:
        """
        获取课程的竞价状态（人数、排名等）
        
        Args:
            offering_id: 开课ID
        
        Returns:
            Dict: 竞价状态信息
        """
        try:
            # 1. 获取课程基本信息
            offering_info = self.db.execute_query("""
                SELECT 
                    max_students,
                    current_students,
                    bidding_deadline,
                    bidding_status
                FROM course_offerings
                WHERE offering_id=?
            """, (offering_id,))
            
            if not offering_info:
                return {
                    'exists': False,
                    'error': '课程不存在'
                }
            
            info = offering_info[0]
            
            # 2. 统计pending状态的投入人数
            bid_count = self.db.execute_query("""
                SELECT COUNT(*) as count
                FROM course_biddings
                WHERE offering_id=? AND status='pending'
            """, (offering_id,))
            
            pending_count = bid_count[0]['count'] if bid_count else 0
            
            # 3. 获取最高和最低投入积分
            bid_stats = self.db.execute_query("""
                SELECT 
                    MAX(points_bid) as max_points,
                    MIN(points_bid) as min_points,
                    AVG(points_bid) as avg_points
                FROM course_biddings
                WHERE offering_id=? AND status='pending'
            """, (offering_id,))
            
            stats = bid_stats[0] if bid_stats else {}
            
            return {
                'exists': True,
                'max_students': info['max_students'],
                'current_students': info['current_students'],
                'pending_bids': pending_count,
                'bidding_deadline': info.get('bidding_deadline'),
                'bidding_status': info.get('bidding_status', 'open'),
                'max_points': stats.get('max_points'),
                'min_points': stats.get('min_points'),
                'avg_points': stats.get('avg_points')
            }
            
        except Exception as e:
            Logger.error(f"查询竞价状态失败: {e}", exc_info=True)
            return {
                'exists': False,
                'error': '查询失败'
            }
    
    def get_bidding_ranking(self, offering_id: int) -> List[Dict]:
        """
        获取课程的竞价排名列表（包括所有状态）
        
        Args:
            offering_id: 开课ID
        
        Returns:
            List[Dict]: 排名列表（按积分降序，同分按时间升序）
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    cb.student_id,
                    cb.points_bid,
                    cb.bid_time,
                    cb.status,
                    s.name as student_name
                FROM course_biddings cb
                JOIN students s ON cb.student_id = s.student_id
                WHERE cb.offering_id=?
                ORDER BY cb.points_bid DESC, cb.bid_time ASC
            """, (offering_id,))
            
            # 添加排名信息
            for i, bid in enumerate(result, 1):
                bid['rank'] = i
            
            return result
            
        except Exception as e:
            Logger.error(f"查询竞价排名失败: {e}", exc_info=True)
            return []

    def process_bidding_results(self, offering_id: int) -> Tuple[bool, str]:
        """
        处理某门课程的竞价结果（录取+积分处理）
        录取算法：按积分降序，同分按时间升序
        
        Args:
            offering_id: 开课ID
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 1. 获取课程容量
            offering_info = self.db.execute_query("""
                SELECT max_students, current_students
                FROM course_offerings
                WHERE offering_id=?
            """, (offering_id,))
            
            if not offering_info:
                return False, "课程不存在"
            
            max_students = offering_info[0]['max_students']
            current_students = offering_info[0].get('current_students', 0) or 0
            
            # 计算剩余名额
            available_slots = max_students - current_students
            
            if available_slots <= 0:
                return False, "课程已满，无可用名额"
            
            # 2. 获取所有pending状态的投入，按录取规则排序
            pending_bids = self.db.execute_query("""
                SELECT 
                    bidding_id,
                    student_id,
                    points_bid,
                    bid_time
                FROM course_biddings
                WHERE offering_id=? AND status='pending'
                ORDER BY points_bid DESC, bid_time ASC
            """, (offering_id,))
            
            if not pending_bids:
                return False, "没有待处理的投入"
            
            # 3. 确定录取名单（前N名）
            accepted_bids = pending_bids[:available_slots]
            rejected_bids = pending_bids[available_slots:]
            
            accepted_count = 0
            rejected_count = 0
            
            # 4. 处理录取的学生
            for bid in accepted_bids:
                student_id = bid['student_id']
                points = bid['points_bid']
                bidding_id = bid['bidding_id']
                
                try:
                    # 4.0 检查是否已选过该课程或同课程的其他班级
                    offering_info_check = self.db.execute_query("""
                        SELECT course_id FROM course_offerings WHERE offering_id=?
                    """, (offering_id,))
                    
                    if offering_info_check:
                        course_id = offering_info_check[0]['course_id']
                        
                        # 检查是否已选了这门课程的任何班级
                        existing_enrollment = self.db.execute_query("""
                            SELECT e.enrollment_id
                            FROM enrollments e
                            JOIN course_offerings o ON e.offering_id = o.offering_id
                            WHERE e.student_id = ? AND o.course_id = ? AND e.status = 'enrolled'
                        """, (student_id, course_id))
                        
                        if existing_enrollment:
                            Logger.warning(f"学生 {student_id} 已选过课程 {course_id}，跳过录取")
                            # 更新竞价状态为rejected
                            self.db.update_data(
                                'course_biddings',
                                {
                                    'status': 'rejected',
                                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                },
                                {'bidding_id': bidding_id}
                            )
                            rejected_count += 1
                            continue
                    
                    # 4.1 更新竞价状态为accepted
                    self.db.update_data(
                        'course_biddings',
                        {
                            'status': 'accepted',
                            'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        {'bidding_id': bidding_id}
                    )
                    
                    # 4.2 扣除积分
                    success, msg = self.points_manager.deduct_points(
                        student_id,
                        points,
                        f"选修课录取扣除（课程ID: {offering_id}）"
                    )
                    
                    if not success:
                        Logger.warning(f"扣除积分失败: {student_id}, {msg}")
                        # 回滚竞价状态
                        self.db.update_data(
                            'course_biddings',
                            {
                                'status': 'pending',
                                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            },
                            {'bidding_id': bidding_id}
                        )
                        rejected_count += 1
                        continue
                    
                    # 4.3 创建或更新选课记录
                    try:
                        # 获取开课信息的 semester
                        offering_semester = self.db.execute_query("""
                            SELECT semester FROM course_offerings WHERE offering_id=?
                        """, (offering_id,))
                        semester = None
                        if offering_semester and offering_semester[0].get('semester'):
                            semester = offering_semester[0]['semester']
                        else:
                            # 如果开课信息也没有 semester，使用当前学期
                            import os
                            semester = os.getenv("CURRENT_SEMESTER", "2024-2025-2")
                        
                        # 先检查是否已存在该学生的enrollment记录（可能是dropped状态）
                        existing_enrollment = self.db.execute_query("""
                            SELECT enrollment_id, status 
                            FROM enrollments 
                            WHERE student_id = ? AND offering_id = ?
                            LIMIT 1
                        """, (student_id, offering_id))
                        
                        result_success = False
                        
                        if existing_enrollment and existing_enrollment[0]['status'] == 'dropped':
                            # 如果存在dropped状态的记录，更新为enrolled
                            enrollment_id = existing_enrollment[0]['enrollment_id']
                            update_count = self.db.update_data(
                                'enrollments',
                                {
                                    'status': 'enrolled',
                                    'semester': semester,
                                    'enrollment_date': datetime.now().strftime('%Y-%m-%d')
                                },
                                {'enrollment_id': enrollment_id}
                            )
                            result_success = update_count > 0
                        else:
                            # 如果不存在，插入新记录
                            enrollment_data = {
                                'student_id': student_id,
                                'offering_id': offering_id,
                                'semester': semester,
                                'enrollment_date': datetime.now().strftime('%Y-%m-%d'),
                                'status': 'enrolled'
                            }
                            result_id = self.db.insert_data('enrollments', enrollment_data)
                            result_success = result_id is not None
                        
                        if result_success:
                            accepted_count += 1
                            Logger.info(f"录取学生: {student_id}, 课程: {offering_id}, 扣除积分: {points}")
                        else:
                            # 操作失败，回滚积分和竞价状态
                            Logger.error(f"创建/更新enrollment记录失败: {student_id}")
                            self.points_manager.refund_points(
                                student_id,
                                points,
                                f"录取失败退还积分（开课ID: {offering_id}）"
                            )
                            self.db.update_data(
                                'course_biddings',
                                {
                                    'status': 'pending',
                                    'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                },
                                {'bidding_id': bidding_id}
                            )
                            rejected_count += 1
                            
                    except Exception as insert_error:
                        # 插入失败，回滚积分和竞价状态
                        Logger.error(f"插入enrollment记录异常: {insert_error}", exc_info=True)
                        self.points_manager.refund_points(
                            student_id,
                            points,
                            f"录取失败退还积分（开课ID: {offering_id}）"
                        )
                        self.db.update_data(
                            'course_biddings',
                            {
                                'status': 'pending',
                                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            },
                            {'bidding_id': bidding_id}
                        )
                        rejected_count += 1
                        
                except Exception as e:
                    Logger.error(f"处理学生录取失败: {student_id}, {e}", exc_info=True)
                    rejected_count += 1
            
            # 5. 处理未录取的学生
            for bid in rejected_bids:
                student_id = bid['student_id']
                points = bid['points_bid']
                bidding_id = bid['bidding_id']
                
                # 5.1 更新竞价状态为rejected
                self.db.update_data(
                    'course_biddings',
                    {
                        'status': 'rejected',
                        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    {'bidding_id': bidding_id}
                )
                
                # 5.2 退还积分（注意：积分实际上没有被扣除，只是标记为pending）
                # 这里不需要实际退还，因为积分从未被扣除
                # 但为了记录，我们可以记录一条refund交易
                rejected_count += 1
                Logger.info(f"未录取学生: {student_id}, 课程: {offering_id}, 积分: {points}")
            
            # 6. 更新课程的current_students和竞价状态
            new_current = current_students + accepted_count
            
            # 竞价逻辑：只有录满人数才关闭竞价，否则保持开放
            if new_current >= max_students:
                # 已录满，关闭竞价
                bidding_status = 'closed'
                offering_status = 'full'
                status_msg = "课程已满，竞价已关闭"
            else:
                # 未录满，保持竞价开放
                bidding_status = 'open'
                offering_status = 'open'
                remaining = max_students - new_current
                status_msg = f"还有{remaining}个名额，竞价继续开放"
            
            update_data = {
                'current_students': new_current,
                'bidding_status': bidding_status,
                'status': offering_status
            }
            
            self.db.update_data(
                'course_offerings',
                update_data,
                {'offering_id': offering_id}
            )
            
            Logger.info(f"竞价处理完成: 课程 {offering_id}, 录取 {accepted_count} 人, 未录取 {rejected_count} 人")
            Logger.info(f"  人数: {new_current}/{max_students}, {status_msg}")
            
            result_message = f"处理完成：录取{accepted_count}人，未录取{rejected_count}人\n"
            result_message += f"当前人数：{new_current}/{max_students}\n"
            result_message += status_msg
            
            return True, result_message
            
        except Exception as e:
            Logger.error(f"处理竞价结果失败: {e}", exc_info=True)
            return False, "处理竞价结果失败"
