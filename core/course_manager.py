"""
课程管理模块
负责课程信息管理、开课计划管理
"""

from typing import List, Dict, Optional
from utils.logger import Logger
from data.models import Course, CourseOffering


class CourseManager:
    """课程管理类"""
    
    def __init__(self, db):
        """
        初始化课程管理器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        Logger.info("课程管理器初始化完成")
    
    def get_all_courses(self) -> List[Dict]:
        """
        获取所有课程
        
        Returns:
            课程列表
        """
        sql = "SELECT * FROM courses ORDER BY course_id"
        return self.db.execute_query(sql)
    
    def get_course_by_id(self, course_id: str) -> Optional[Dict]:
        """
        根据课程ID获取课程信息
        
        Args:
            course_id: 课程代码
        
        Returns:
            课程信息字典
        """
        sql = "SELECT * FROM courses WHERE course_id=?"
        result = self.db.execute_query(sql, (course_id,))
        return result[0] if result else None
    
    def search_courses(self, keyword: str = None, course_type: str = None) -> List[Dict]:
        """
        搜索课程
        
        Args:
            keyword: 关键词（课程名称或代码）
            course_type: 课程类型
        
        Returns:
            课程列表
        """
        sql = "SELECT * FROM courses WHERE 1=1"
        params = []
        
        if keyword:
            sql += " AND (course_id LIKE ? OR course_name LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if course_type:
            sql += " AND course_type=?"
            params.append(course_type)
        
        sql += " ORDER BY course_id"
        
        return self.db.execute_query(sql, tuple(params) if params else None)
    
    def get_course_offerings(self, semester: str = None) -> List[Dict]:
        """
        获取开课计划
        
        Args:
            semester: 学期（如：2024-2025-2）
        
        Returns:
            开课计划列表
        """
        sql = """
            SELECT 
                co.offering_id,
                co.course_id,
                c.course_name,
                c.credits,
                c.course_type,
                co.teacher_id,
                t.name as teacher_name,
                co.semester,
                co.class_time,
                co.classroom,
                co.current_students,
                co.max_students,
                co.status
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            JOIN teachers t ON co.teacher_id = t.teacher_id
        """
        
        params = None
        if semester:
            sql += " WHERE co.semester=?"
            params = (semester,)
        
        sql += " ORDER BY co.course_id"
        
        return self.db.execute_query(sql, params)
    
    def get_offering_by_id(self, offering_id: int) -> Optional[Dict]:
        """
        根据开课计划ID获取信息
        
        Args:
            offering_id: 开课计划ID
        
        Returns:
            开课计划信息
        """
        sql = """
            SELECT 
                co.offering_id,
                co.course_id,
                c.course_name,
                c.credits,
                c.hours,
                c.course_type,
                c.description,
                co.teacher_id,
                t.name as teacher_name,
                t.title,
                co.semester,
                co.class_time,
                co.classroom,
                co.current_students,
                co.max_students,
                co.status
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            JOIN teachers t ON co.teacher_id = t.teacher_id
            WHERE co.offering_id=?
        """
        
        result = self.db.execute_query(sql, (offering_id,))
        return result[0] if result else None
    
    def get_available_courses(self, semester: str) -> List[Dict]:
        """
        获取可选课程（状态为open且未满）
        
        Args:
            semester: 学期
        
        Returns:
            可选课程列表
        """
        sql = """
            SELECT 
                co.offering_id,
                co.course_id,
                c.course_name,
                c.credits,
                c.course_type,
                co.teacher_id,
                t.name as teacher_name,
                co.semester,
                co.class_time,
                co.classroom,
                co.current_students,
                co.max_students,
                co.status
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            JOIN teachers t ON co.teacher_id = t.teacher_id
            WHERE co.semester=? AND co.status='open' AND co.current_students < co.max_students
            ORDER BY c.course_type, co.course_id
        """
        
        return self.db.execute_query(sql, (semester,))
    
    def get_teacher_courses(self, teacher_id: str, semester: str = None) -> List[Dict]:
        """
        获取教师授课列表
        
        Args:
            teacher_id: 教师工号
            semester: 学期（可选）
        
        Returns:
            授课列表
        """
        sql = """
            SELECT 
                co.offering_id,
                co.course_id,
                c.course_name,
                c.credits,
                co.semester,
                co.class_time,
                co.classroom,
                co.current_students,
                co.max_students
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            WHERE co.teacher_id=?
        """
        
        params = [teacher_id]
        if semester:
            sql += " AND co.semester=?"
            params.append(semester)
        
        sql += " ORDER BY co.semester DESC, co.course_id"
        
        return self.db.execute_query(sql, tuple(params))
    
    def add_course(self, course_data: Dict) -> bool:
        """
        添加新课程
        
        Args:
            course_data: 课程信息
        
        Returns:
            是否成功
        """
        try:
            self.db.insert_data('courses', course_data)
            Logger.info(f"添加课程成功: {course_data.get('course_name')}")
            return True
        except Exception as e:
            Logger.error(f"添加课程失败: {e}")
            return False
    
    def update_course(self, course_id: str, course_data: Dict) -> bool:
        """
        更新课程信息
        
        Args:
            course_id: 课程代码
            course_data: 新的课程信息
        
        Returns:
            是否成功
        """
        try:
            course_data['updated_at'] = 'CURRENT_TIMESTAMP'
            count = self.db.update_data('courses', course_data, {'course_id': course_id})
            
            if count > 0:
                Logger.info(f"更新课程成功: {course_id}")
                return True
            else:
                Logger.warning(f"课程不存在: {course_id}")
                return False
        except Exception as e:
            Logger.error(f"更新课程失败: {e}")
            return False
    
    def delete_course(self, course_id: str) -> bool:
        """
        删除课程
        
        Args:
            course_id: 课程代码
        
        Returns:
            是否成功
        """
        try:
            count = self.db.delete_data('courses', {'course_id': course_id})
            
            if count > 0:
                Logger.info(f"删除课程成功: {course_id}")
                return True
            else:
                Logger.warning(f"课程不存在: {course_id}")
                return False
        except Exception as e:
            Logger.error(f"删除课程失败: {e}")
            return False
    
    def add_course_offering(self, offering_data: Dict) -> Optional[int]:
        """
        添加开课计划
        
        Args:
            offering_data: 开课计划信息
        
        Returns:
            新插入的offering_id，失败返回None
        """
        try:
            offering_id = self.db.insert_data('course_offerings', offering_data)
            Logger.info(f"添加开课计划成功: {offering_data.get('course_id')}")
            return offering_id
        except Exception as e:
            Logger.error(f"添加开课计划失败: {e}")
            return None
    
    def update_offering_students(self, offering_id: int, increment: int = 1) -> bool:
        """
        更新开课计划的选课人数
        
        Args:
            offering_id: 开课计划ID
            increment: 增量（正数为增加，负数为减少）
        
        Returns:
            是否成功
        """
        try:
            sql = """
                UPDATE course_offerings 
                SET current_students = current_students + ?
                WHERE offering_id = ?
            """
            self.db.execute_update(sql, (increment, offering_id))
            
            # 检查是否已满，更新状态
            offering = self.get_offering_by_id(offering_id)
            if offering:
                if offering['current_students'] >= offering['max_students']:
                    self.db.update_data('course_offerings', 
                                      {'status': 'full'}, 
                                      {'offering_id': offering_id})
                elif offering['status'] == 'full':
                    self.db.update_data('course_offerings', 
                                      {'status': 'open'}, 
                                      {'offering_id': offering_id})
            
            return True
        except Exception as e:
            Logger.error(f"更新选课人数失败: {e}")
            return False

