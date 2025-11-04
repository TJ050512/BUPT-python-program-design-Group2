"""
选课管理模块
负责学生选课、退课、选课查询
"""

from typing import List, Dict, Optional, Tuple
from utils.logger import Logger


class EnrollmentManager:
    """选课管理类"""
    
    def __init__(self, db):
        """
        初始化选课管理器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        Logger.info("选课管理器初始化完成")
    
    def enroll_course(self, student_id: str, offering_id: int, semester: str) -> Tuple[bool, str]:
        """
        学生选课
        
        Args:
            student_id: 学号
            offering_id: 开课计划ID
            semester: 学期
        
        Returns:
            (是否成功, 消息)
        """
        try:
            # 1. 检查课程是否存在且可选
            offering = self._get_offering_info(offering_id)
            if not offering:
                return False, "课程不存在"
            
            if offering['status'] != 'open':
                return False, "该课程已关闭选课"
            
            if offering['current_students'] >= offering['max_students']:
                return False, "该课程已满"
            
            # 2. 检查是否已选过该课程
            existing_enrollment = self._get_enrollment(student_id, offering_id)
            
            # 如果已经选了这门课且状态是enrolled，则不能重复选课
            if existing_enrollment and existing_enrollment['status'] == 'enrolled':
                return False, "您已选过该课程"
            
            # 3. 检查时间冲突
            conflict = self._check_time_conflict(student_id, semester, offering['class_time'])
            if conflict:
                return False, f"与已选课程【{conflict}】时间冲突"
            
            # 4. 插入或更新选课记录
            # 如果之前退过课，则更新记录；否则插入新记录
            if existing_enrollment and existing_enrollment['status'] == 'dropped':
                # 更新已存在的记录
                count = self.db.update_data('enrollments', 
                                          {'status': 'enrolled', 'semester': semester}, 
                                          {'enrollment_id': existing_enrollment['enrollment_id']})
                enrollment_id = existing_enrollment['enrollment_id'] if count > 0 else None
            else:
                # 插入新记录
                enrollment_data = {
                    'student_id': student_id,
                    'offering_id': offering_id,
                    'semester': semester,
                    'status': 'enrolled'
                }
                enrollment_id = self.db.insert_data('enrollments', enrollment_data)
            
            if enrollment_id:
                # 5. 更新课程选课人数
                sql = "UPDATE course_offerings SET current_students = current_students + 1 WHERE offering_id = ?"
                self.db.execute_update(sql, (offering_id,))
                
                # 检查是否已满
                if offering['current_students'] + 1 >= offering['max_students']:
                    self.db.update_data('course_offerings', 
                                      {'status': 'full'}, 
                                      {'offering_id': offering_id})
                
                Logger.info(f"学生 {student_id} 选课成功: {offering['course_name']}")
                return True, "选课成功"
            else:
                return False, "选课失败，请稍后重试"
            
        except Exception as e:
            Logger.error(f"选课失败: {e}")
            return False, "选课失败，请稍后重试"
    
    def drop_course(self, student_id: str, offering_id: int) -> Tuple[bool, str]:
        """
        学生退课
        
        Args:
            student_id: 学号
            offering_id: 开课计划ID
        
        Returns:
            (是否成功, 消息)
        """
        try:
            # 1. 检查是否已选该课程
            enrollment = self._get_enrollment(student_id, offering_id)
            if not enrollment:
                return False, "您未选该课程"
            
            if enrollment['status'] != 'enrolled':
                return False, "该课程不可退课"
            
            # 2. 检查是否已有成绩
            grade = self._get_grade_by_enrollment(enrollment['enrollment_id'])
            if grade and grade.get('score') is not None:
                return False, "已录入成绩的课程不可退课"
            
            # 3. 更新选课状态为已退课
            count = self.db.update_data('enrollments', 
                                       {'status': 'dropped'}, 
                                       {'enrollment_id': enrollment['enrollment_id']})
            
            if count > 0:
                # 4. 更新课程选课人数
                sql = "UPDATE course_offerings SET current_students = current_students - 1 WHERE offering_id = ?"
                self.db.execute_update(sql, (offering_id,))
                
                # 如果原来是满的，改为open
                self.db.update_data('course_offerings', 
                                  {'status': 'open'}, 
                                  {'offering_id': offering_id, 'status': 'full'})
                
                Logger.info(f"学生 {student_id} 退课成功: offering_id={offering_id}")
                return True, "退课成功"
            else:
                return False, "退课失败"
            
        except Exception as e:
            Logger.error(f"退课失败: {e}")
            return False, "退课失败，请稍后重试"
    
    def get_student_enrollments(self, student_id: str, semester: str = None, 
                                status: str = 'enrolled') -> List[Dict]:
        """
        获取学生的选课记录
        
        Args:
            student_id: 学号
            semester: 学期（可选）
            status: 状态（enrolled/dropped/completed）
        
        Returns:
            选课记录列表
        """
        sql = """
            SELECT 
                e.enrollment_id,
                e.offering_id,
                e.semester,
                e.enrollment_date,
                e.status,
                co.course_id,
                c.course_name,
                c.credits,
                c.course_type,
                co.teacher_id,
                t.name as teacher_name,
                co.class_time,
                co.classroom
            FROM enrollments e
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN teachers t ON co.teacher_id = t.teacher_id
            WHERE e.student_id = ?
        """
        
        params = [student_id]
        
        if semester:
            sql += " AND e.semester = ?"
            params.append(semester)
        
        if status:
            sql += " AND e.status = ?"
            params.append(status)
        
        sql += " ORDER BY e.semester DESC, c.course_id"
        
        return self.db.execute_query(sql, tuple(params))
    
    def get_course_students(self, offering_id: int) -> List[Dict]:
        """
        获取某门课程的选课学生列表
        包括所有选课的学生（无论是否有成绩），只要状态是enrolled或completed
        
        Args:
            offering_id: 开课计划ID
        
        Returns:
            学生列表
        """
        sql = """
            SELECT 
                e.enrollment_id,
                e.student_id,
                s.name as student_name,
                s.major,
                s.class_name,
                e.enrollment_date,
                e.status
            FROM enrollments e
            JOIN students s ON e.student_id = s.student_id
            WHERE e.offering_id = ? AND e.status IN ('enrolled', 'completed')
            ORDER BY s.student_id
        """
        
        return self.db.execute_query(sql, (offering_id,))
    
    def get_enrollment_statistics(self, semester: str) -> Dict:
        """
        获取选课统计信息
        
        Args:
            semester: 学期
        
        Returns:
            统计信息字典
        """
        # 总选课人次
        sql1 = """
            SELECT COUNT(*) as total_enrollments
            FROM enrollments
            WHERE semester = ? AND status = 'enrolled'
        """
        result1 = self.db.execute_query(sql1, (semester,))
        total_enrollments = result1[0]['total_enrollments'] if result1 else 0
        
        # 热门课程（选课人数最多的前5门）
        sql2 = """
            SELECT 
                c.course_name,
                co.current_students,
                co.max_students
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            WHERE co.semester = ?
            ORDER BY co.current_students DESC
            LIMIT 5
        """
        popular_courses = self.db.execute_query(sql2, (semester,))
        
        return {
            'total_enrollments': total_enrollments,
            'popular_courses': popular_courses
        }
    
    def _get_offering_info(self, offering_id: int) -> Optional[Dict]:
        """获取开课信息"""
        sql = """
            SELECT 
                co.*,
                c.course_name
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            WHERE co.offering_id = ?
        """
        result = self.db.execute_query(sql, (offering_id,))
        return result[0] if result else None
    
    def _is_enrolled(self, student_id: str, offering_id: int) -> bool:
        """检查是否已选课"""
        sql = """
            SELECT COUNT(*) as count 
            FROM enrollments 
            WHERE student_id = ? AND offering_id = ? AND status = 'enrolled'
        """
        result = self.db.execute_query(sql, (student_id, offering_id))
        return result[0]['count'] > 0 if result else False
    
    def _check_time_conflict(self, student_id: str, semester: str, class_time: str) -> Optional[str]:
        """
        检查时间冲突
        
        Returns:
            冲突的课程名称，无冲突返回None
        """
        if not class_time:
            return None
        
        # 简化版：检查是否有完全相同的上课时间
        sql = """
            SELECT c.course_name
            FROM enrollments e
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE e.student_id = ? 
              AND e.semester = ? 
              AND e.status = 'enrolled'
              AND co.class_time = ?
            LIMIT 1
        """
        
        result = self.db.execute_query(sql, (student_id, semester, class_time))
        return result[0]['course_name'] if result else None
    
    def _get_enrollment(self, student_id: str, offering_id: int) -> Optional[Dict]:
        """获取选课记录"""
        sql = """
            SELECT * FROM enrollments 
            WHERE student_id = ? AND offering_id = ?
            ORDER BY enrollment_date DESC
            LIMIT 1
        """
        result = self.db.execute_query(sql, (student_id, offering_id))
        return result[0] if result else None
    
    def _get_grade_by_enrollment(self, enrollment_id: int) -> Optional[Dict]:
        """根据选课记录ID获取成绩"""
        sql = "SELECT * FROM grades WHERE enrollment_id = ?"
        result = self.db.execute_query(sql, (enrollment_id,))
        return result[0] if result else None

