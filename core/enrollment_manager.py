"""
选课管理模块
负责学生选课、退课、选课查询
"""

import sqlite3
import re
from typing import List, Dict, Optional, Tuple, Set
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
    
    def enroll_course(self, student_id: str, offering_id: int) -> Tuple[bool, str]:
        """
        学生选课
        
        Args:
            student_id: 学号
            offering_id: 开课计划ID
        
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
            
            # 获取学期信息（从 offering 中获取，如果没有则从数据库查询）
            semester = offering.get('semester')
            Logger.debug(f"从offering获取semester: {repr(semester)}, offering_id={offering_id}")
            
            # 检查 semester 是否有有效值（不是 None 且不是空字符串）
            if not semester or (isinstance(semester, str) and not semester.strip()):
                # 如果 offering 中没有 semester，从数据库查询
                Logger.debug(f"offering中没有semester，从数据库查询: offering_id={offering_id}")
                off_rows = self.db.execute_query(
                    "SELECT semester FROM course_offerings WHERE offering_id=? LIMIT 1",
                    (offering_id,)
                )
                if not off_rows:
                    Logger.error(f"无法从数据库获取offering信息: offering_id={offering_id}")
                    return False, "无法获取课程学期信息"
                
                db_semester = off_rows[0].get('semester')
                Logger.debug(f"从数据库查询到的semester: {repr(db_semester)}")
                
                if not db_semester or (isinstance(db_semester, str) and not db_semester.strip()):
                    Logger.error(f"数据库中的semester也为空: offering_id={offering_id}, offering={offering}")
                    return False, "无法获取课程学期信息"
                semester = db_semester.strip() if isinstance(db_semester, str) else str(db_semester)
            else:
                semester = semester.strip() if isinstance(semester, str) else str(semester)
            
            # 最终验证 semester 有值
            if not semester or not semester.strip():
                Logger.error(f"最终验证失败: semester={repr(semester)}, offering_id={offering_id}")
                return False, "无法获取课程学期信息"
            
            semester = semester.strip()  # 确保去除前后空格
            Logger.info(f"选课学期确认: {repr(semester)}, offering_id={offering_id}")
            
            # 2. 检查是否已选过该课程
            existing_enrollment = self._get_enrollment(student_id, offering_id)
            
            # 如果已经选了这门课且状态是enrolled，则不能重复选课
            if existing_enrollment and existing_enrollment['status'] == 'enrolled':
                return False, "您已选过该课程"
            
            # 2.5. 检查是否已选择了同一门课程（不同老师）
            same_course_check = self._check_same_course_enrolled(student_id, offering['course_id'])
            if same_course_check:
                return False, f"您已选择了【{same_course_check}】，不能重复选择同一门课程"
            
            # 3. 检查时间冲突（包括公选课之间的冲突检查）
            conflict = self._check_time_conflict(student_id, offering['class_time'], offering_id)
            if conflict:
                return False, f"与已选课程【{conflict}】时间冲突"
            
            # 4. 插入或更新选课记录
            # 如果之前退过课，则更新记录；否则插入新记录
            if existing_enrollment and existing_enrollment['status'] == 'dropped':
                # 更新已存在的记录
                count = self.db.update_data(
                    'enrollments',
                    {'status': 'enrolled', 'semester': semester},
                    {'enrollment_id': existing_enrollment['enrollment_id']}
                )
                enrollment_id = existing_enrollment['enrollment_id'] if count > 0 else None
            else:
                # 再次验证 semester 有值
                if not semester or not semester.strip():
                    Logger.error(f"插入选课记录前验证失败: semester为空, offering_id={offering_id}, student_id={student_id}")
                    return False, "无法获取课程学期信息"
                
                try:
                    # 最后一次验证 semester 有值
                    if not semester:
                        Logger.error(f"插入前semester验证失败: semester={repr(semester)}, offering_id={offering_id}, student_id={student_id}")
                        return False, "无法获取课程学期信息"
                    
                    sql = """
                        INSERT INTO enrollments (student_id, offering_id, semester, status)
                        VALUES (?, ?, ?, ?)
                    """
                    Logger.info(f"插入选课记录: student_id={student_id}, offering_id={offering_id}, semester={repr(semester)}")
                    self.db.cursor.execute(sql, (student_id, offering_id, semester, 'enrolled'))
                    self.db.conn.commit()
                    enrollment_id = self.db.cursor.lastrowid
                    Logger.debug(f"选课记录插入成功: enrollment_id={enrollment_id}")
                except sqlite3.OperationalError as db_error:
                    error_msg = str(db_error)
                    Logger.error(f"数据库操作错误: {error_msg}, semester={repr(semester)}, offering_id={offering_id}")
                    raise db_error
                except Exception as db_error:
                    Logger.error(f"插入选课记录异常: {db_error}, semester={repr(semester)}, offering_id={offering_id}")
                    raise db_error
            
            if enrollment_id:
                # 5. 更新课程选课人数
                sql = "UPDATE course_offerings SET current_students = current_students + 1 WHERE offering_id = ?"
                self.db.execute_update(sql, (offering_id,))
                
                try:
                    from data.database_interface import DatabaseInterface
                    DatabaseInterface().sync_course_offering_counts()
                except Exception:
                    pass

                # 检查是否已满
                if offering['current_students'] + 1 >= offering['max_students']:
                    self.db.update_data('course_offerings', 
                                      {'status': 'full'}, 
                                      {'offering_id': offering_id})
                
                Logger.info(f"学生 {student_id} 选课成功: {offering['course_name']}")
                return True, "选课成功"
            else:
                return False, "选课失败，请稍后重试"
            
        except sqlite3.OperationalError as e:
            # 捕获数据库触发器错误
            error_msg = str(e)
            Logger.error(f"选课失败（数据库错误）: {error_msg}")
            
            # 检查是否是跨专业名额已满
            if "跨专业名额已满" in error_msg:
                return False, "该课程的跨专业名额已满，无法选课"
            elif "公选课必须安排在晚间节次" in error_msg:
                return False, "公选课必须安排在晚间节次"
            else:
                return False, f"选课失败：{error_msg}"
        except Exception as e:
            Logger.error(f"选课失败: {e}")
            error_msg = str(e)
            # 检查是否是跨专业名额已满（可能在其他异常中）
            if "跨专业名额已满" in error_msg:
                return False, "该课程的跨专业名额已满，无法选课"
            return False, f"选课失败：{error_msg}"
    
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
    
    def get_student_enrollments(self, student_id: str, 
                                status: str = 'enrolled') -> List[Dict]:
        """
        获取学生的选课记录
        
        Args:
            student_id: 学号
            status: 状态（enrolled/dropped/completed）
        
        Returns:
            选课记录列表
        """
        sql = """
            SELECT 
                e.enrollment_id,
                e.offering_id,
                e.enrollment_date,
                e.status,
                COALESCE(e.semester, co.semester) as semester,
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
    
    def get_enrollment_statistics(self) -> Dict:
        """
        获取选课统计信息
        
        Returns:
            统计信息字典
        """
        # 总选课人次
        sql1 = """
            SELECT COUNT(*) as total_enrollments
            FROM enrollments
            WHERE status = 'enrolled'
        """
        result1 = self.db.execute_query(sql1)
        total_enrollments = result1[0]['total_enrollments'] if result1 else 0
        
        # 热门课程（选课人数最多的前5门）
        sql2 = """
            SELECT 
                c.course_name,
                co.current_students,
                co.max_students
            FROM course_offerings co
            JOIN courses c ON co.course_id = c.course_id
            ORDER BY co.current_students DESC
            LIMIT 5
        """
        popular_courses = self.db.execute_query(sql2)
        
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
    
    def _check_time_conflict(self, student_id: str, class_time: str, offering_id: int = None) -> Optional[str]:
        """
        检查时间冲突
        
        Args:
            student_id: 学号
            class_time: 要检查的课程时间字符串
            offering_id: 开课计划ID（可选，用于判断是否是公选课）
        
        Returns:
            冲突的课程名称，无冲突返回None
        """
        if not class_time:
            return None
        
        # 解析当前课程的时间段
        current_time_slots = self._parse_time_slots(class_time)
        if not current_time_slots:
            return None
        
        # 检查当前要选的课程是否是公选课
        is_current_public_elective = False
        if offering_id:
            current_offering_info = self.db.execute_query(
                """
                SELECT c.is_public_elective 
                FROM course_offerings co
                JOIN courses c ON co.course_id = c.course_id
                WHERE co.offering_id = ?
                """,
                (offering_id,)
            )
            if current_offering_info and len(current_offering_info) > 0:
                is_current_public_elective = bool(current_offering_info[0].get('is_public_elective', 0))
        
        # 获取学生已选的所有课程及其时间
        sql = """
            SELECT 
                co.class_time,
                c.course_name,
                c.is_public_elective
            FROM enrollments e
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE e.student_id = ? 
              AND e.status = 'enrolled'
              AND co.class_time IS NOT NULL
              AND co.class_time <> ''
        """
        
        enrolled_courses = self.db.execute_query(sql, (student_id,))
        
        # 检查每个已选课程的时间段是否与当前课程冲突
        for course in enrolled_courses:
            enrolled_time_slots = self._parse_time_slots(course.get('class_time', ''))
            if not enrolled_time_slots:
                continue
            
            # 检查是否有时间段重叠
            if current_time_slots & enrolled_time_slots:  # 使用集合交集检查
                # 如果当前课程和已选课程都是公选课，特别提示
                is_enrolled_public_elective = bool(course.get('is_public_elective', 0))
                if is_current_public_elective and is_enrolled_public_elective:
                    return f"公选课【{course.get('course_name', '')}】与当前公选课时间冲突"
                return course.get('course_name', '')
        
        return None
    
    def _parse_time_slots(self, class_time: str) -> Set[Tuple[int, int]]:
        """
        解析时间字符串，提取所有时间段
        
        Args:
            class_time: 时间字符串（如：周一3-4节，周四3-4节）
        
        Returns:
            时间段集合，每个元素为(星期, 节次)的元组
        """
        time_slots = set()
        
        if not class_time:
            return time_slots
        
        # 支持中文逗号、英文逗号、顿号等多种分隔符
        time_blocks = re.split(r'[，,、]', class_time)
        
        # 星期映射
        weekday_map = {
            '周一': 1, '周二': 2, '周三': 3, '周四': 4, '周五': 5,
            '周1': 1, '周2': 2, '周3': 3, '周4': 4, '周5': 5
        }
        
        for block in time_blocks:
            block = block.strip()
            if not block:
                continue
            
            # 匹配星期和节次，支持多种格式：
            # 周一1-2节、周一1-3节、周一 1-2节、周1第1-2节等
            pattern = r'(周[一二三四五]|周[1-5])\s*(\d+)\s*[-~至]\s*(\d+)\s*[节堂]'
            match = re.search(pattern, block)
            
            if match:
                weekday_str = match.group(1)
                start_period = int(match.group(2))
                end_period = int(match.group(3))
                
                # 确保节次在合理范围内（1-14节，支持晚上课程）
                if start_period < 1 or end_period > 14 or start_period > end_period:
                    continue
                
                weekday = weekday_map.get(weekday_str)
                if weekday:
                    # 将连续节次都添加为时间段
                    for period in range(start_period, end_period + 1):
                        time_slots.add((weekday, period))
        
        return time_slots
    
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
    
    def _check_same_course_enrolled(self, student_id: str, course_id: str) -> Optional[str]:
        """
        检查学生是否已选择了同一门课程（不同老师）
        
        Args:
            student_id: 学号
            course_id: 课程ID
        
        Returns:
            如果已选，返回课程名称；否则返回None
        """
        sql = """
            SELECT c.course_name
            FROM enrollments e
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE e.student_id = ?
              AND e.status = 'enrolled'
              AND co.course_id = ?
            LIMIT 1
        """
        
        result = self.db.execute_query(sql, (student_id, course_id))
        return result[0]['course_name'] if result else None
