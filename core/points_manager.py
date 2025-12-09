"""
积分管理模块 - 北京邮电大学教学管理系统
负责学生选课积分的分配、扣除、退还和查询
"""

from typing import Optional, List, Dict, Tuple
from datetime import datetime
from utils.logger import Logger


class PointsManager:
    """积分管理器 - 管理学生选课积分"""
    
    # 默认初始积分
    DEFAULT_POINTS = 200
    
    def __init__(self, db):
        """
        初始化积分管理器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        Logger.info("积分管理器初始化完成")
    
    def initialize_student_points(self, student_id: str, points: int = DEFAULT_POINTS) -> bool:
        """
        为新学生初始化积分
        
        Args:
            student_id: 学生学号
            points: 初始积分（默认200分）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 更新学生表的积分字段
            rows_affected = self.db.update_data(
                'students',
                {'course_points': points},
                {'student_id': student_id}
            )
            
            if rows_affected == 0:
                Logger.warning(f"学生不存在或积分已初始化: {student_id}")
                return False
            
            # 记录积分交易
            self._record_transaction(
                student_id=student_id,
                points_change=points,
                balance_after=points,
                transaction_type='init',
                reason='初始化选课积分'
            )
            
            Logger.info(f"学生积分初始化成功: {student_id}, 积分: {points}")
            return True
            
        except Exception as e:
            Logger.error(f"初始化学生积分失败: {e}", exc_info=True)
            return False
    
    def get_student_points(self, student_id: str) -> int:
        """
        获取学生当前积分
        
        Args:
            student_id: 学生学号
        
        Returns:
            int: 当前积分，如果学生不存在返回0
        """
        try:
            result = self.db.execute_query(
                "SELECT course_points FROM students WHERE student_id=?",
                (student_id,)
            )
            
            if result:
                points = result[0].get('course_points', 0)
                return points if points is not None else 0
            
            Logger.warning(f"学生不存在: {student_id}")
            return 0
            
        except Exception as e:
            Logger.error(f"查询学生积分失败: {e}", exc_info=True)
            return 0
    
    def deduct_points(self, student_id: str, points: int, reason: str) -> Tuple[bool, str]:
        """
        扣除学生积分
        
        Args:
            student_id: 学生学号
            points: 要扣除的积分
            reason: 扣除原因
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证积分数量
            if points <= 0:
                return False, "扣除积分必须大于0"
            
            # 获取当前积分
            current_points = self.get_student_points(student_id)
            
            if current_points < points:
                return False, f"积分不足，当前剩余{current_points}分"
            
            # 计算新积分
            new_points = current_points - points
            
            # 更新数据库
            rows_affected = self.db.update_data(
                'students',
                {'course_points': new_points},
                {'student_id': student_id}
            )
            
            if rows_affected == 0:
                return False, "学生不存在"
            
            # 记录交易
            self._record_transaction(
                student_id=student_id,
                points_change=-points,
                balance_after=new_points,
                transaction_type='deduct',
                reason=reason
            )
            
            Logger.info(f"扣除积分成功: {student_id}, 扣除: {points}, 剩余: {new_points}")
            return True, f"扣除成功，剩余{new_points}分"
            
        except Exception as e:
            Logger.error(f"扣除积分失败: {e}", exc_info=True)
            return False, "扣除积分失败"
    
    def refund_points(self, student_id: str, points: int, reason: str) -> Tuple[bool, str]:
        """
        退还学生积分
        
        Args:
            student_id: 学生学号
            points: 要退还的积分
            reason: 退还原因
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证积分数量
            if points <= 0:
                return False, "退还积分必须大于0"
            
            # 获取当前积分
            current_points = self.get_student_points(student_id)
            
            # 计算新积分
            new_points = current_points + points
            
            # 更新数据库
            rows_affected = self.db.update_data(
                'students',
                {'course_points': new_points},
                {'student_id': student_id}
            )
            
            if rows_affected == 0:
                return False, "学生不存在"
            
            # 记录交易
            self._record_transaction(
                student_id=student_id,
                points_change=points,
                balance_after=new_points,
                transaction_type='refund',
                reason=reason
            )
            
            Logger.info(f"退还积分成功: {student_id}, 退还: {points}, 剩余: {new_points}")
            return True, f"退还成功，当前{new_points}分"
            
        except Exception as e:
            Logger.error(f"退还积分失败: {e}", exc_info=True)
            return False, "退还积分失败"
    
    def get_points_history(self, student_id: str) -> List[Dict]:
        """
        获取学生积分历史记录
        
        Args:
            student_id: 学生学号
        
        Returns:
            List[Dict]: 积分交易历史列表
        """
        try:
            result = self.db.execute_query("""
                SELECT 
                    transaction_id,
                    points_change,
                    balance_after,
                    transaction_type,
                    reason,
                    operator_id,
                    created_at
                FROM points_transactions
                WHERE student_id=?
                ORDER BY created_at DESC
            """, (student_id,))
            
            return result
            
        except Exception as e:
            Logger.error(f"查询积分历史失败: {e}", exc_info=True)
            return []
    
    def admin_adjust_points(self, admin_id: str, student_id: str, 
                           points_change: int, reason: str) -> Tuple[bool, str]:
        """
        管理员调整学生积分
        
        Args:
            admin_id: 管理员ID
            student_id: 学生学号
            points_change: 积分变化（正数为增加，负数为减少）
            reason: 调整原因
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证原因不为空
            if not reason or not reason.strip():
                return False, "必须提供调整原因"
            
            # 获取当前积分
            current_points = self.get_student_points(student_id)
            
            # 计算新积分
            new_points = current_points + points_change
            
            # 验证新积分不能为负
            if new_points < 0:
                return False, f"调整后积分不能为负数（当前{current_points}分，调整{points_change}分）"
            
            # 更新数据库
            rows_affected = self.db.update_data(
                'students',
                {'course_points': new_points},
                {'student_id': student_id}
            )
            
            if rows_affected == 0:
                return False, "学生不存在"
            
            # 记录交易（包含管理员信息）
            self._record_transaction(
                student_id=student_id,
                points_change=points_change,
                balance_after=new_points,
                transaction_type='admin_adjust',
                reason=reason,
                operator_id=admin_id
            )
            
            action = "增加" if points_change > 0 else "减少"
            Logger.info(f"管理员调整积分: {admin_id} {action}学生 {student_id} {abs(points_change)}分, 原因: {reason}")
            return True, f"调整成功，当前{new_points}分"
            
        except Exception as e:
            Logger.error(f"管理员调整积分失败: {e}", exc_info=True)
            return False, "调整积分失败"
    
    def batch_reset_points(self, admin_id: str, points: int = DEFAULT_POINTS) -> Tuple[bool, str]:
        """
        批量重置所有学生积分
        
        Args:
            admin_id: 管理员ID
            points: 重置后的积分（默认200分）
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            # 验证积分值
            if points < 0:
                return False, "积分不能为负数"
            
            # 获取所有学生
            students = self.db.execute_query(
                "SELECT student_id, course_points FROM students WHERE status='active'"
            )
            
            if not students:
                return False, "没有找到活跃学生"
            
            # 批量更新积分
            success_count = 0
            for student in students:
                student_id = student['student_id']
                
                # 更新积分
                rows_affected = self.db.update_data(
                    'students',
                    {'course_points': points},
                    {'student_id': student_id}
                )
                
                if rows_affected > 0:
                    # 记录交易
                    old_points = student.get('course_points', 0) or 0
                    points_change = points - old_points
                    
                    self._record_transaction(
                        student_id=student_id,
                        points_change=points_change,
                        balance_after=points,
                        transaction_type='admin_adjust',
                        reason=f'管理员批量重置积分为{points}分',
                        operator_id=admin_id
                    )
                    
                    success_count += 1
            
            Logger.info(f"批量重置积分完成: {admin_id} 重置了 {success_count} 个学生的积分为 {points}分")
            return True, f"成功重置{success_count}个学生的积分为{points}分"
            
        except Exception as e:
            Logger.error(f"批量重置积分失败: {e}", exc_info=True)
            return False, "批量重置积分失败"
    
    def _record_transaction(self, student_id: str, points_change: int, 
                           balance_after: int, transaction_type: str, 
                           reason: str, operator_id: Optional[str] = None,
                           related_offering_id: Optional[int] = None) -> bool:
        """
        记录积分交易到数据库
        
        Args:
            student_id: 学生学号
            points_change: 积分变化
            balance_after: 操作后余额
            transaction_type: 交易类型
            reason: 原因说明
            operator_id: 操作人ID（可选）
            related_offering_id: 关联的开课ID（可选）
        
        Returns:
            bool: 是否成功
        """
        try:
            transaction_data = {
                'student_id': student_id,
                'points_change': points_change,
                'balance_after': balance_after,
                'transaction_type': transaction_type,
                'reason': reason,
                'operator_id': operator_id,
                'related_offering_id': related_offering_id,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            transaction_id = self.db.insert_data('points_transactions', transaction_data)
            
            if transaction_id:
                return True
            else:
                Logger.warning(f"记录积分交易失败: {student_id}")
                return False
                
        except Exception as e:
            Logger.error(f"记录积分交易异常: {e}", exc_info=True)
            return False
