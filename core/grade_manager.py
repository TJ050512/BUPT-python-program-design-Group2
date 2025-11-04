"""
成绩管理模块
负责成绩录入、查询、统计分析
"""

from typing import List, Dict, Optional, Tuple
from utils.logger import Logger
from data.models import Grade


class GradeManager:
    """成绩管理类"""
    
    def __init__(self, db):
        """
        初始化成绩管理器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        Logger.info("成绩管理器初始化完成")
    
    def input_grade(self, enrollment_id: int, score: float, 
                   teacher_id: str, remarks: str = None) -> Tuple[bool, str]:
        """
        录入或更新成绩
        
        Args:
            enrollment_id: 选课记录ID
            score: 成绩（0-100）
            teacher_id: 录入教师ID
            remarks: 备注
        
        Returns:
            (是否成功, 消息)
        """
        try:
            # 验证成绩范围
            if not (0 <= score <= 100):
                return False, "成绩必须在0-100之间"
            
            # 计算等级和GPA
            grade_level, gpa = Grade.calculate_gpa(score)
            
            # 获取选课信息
            enrollment = self._get_enrollment_info(enrollment_id)
            if not enrollment:
                return False, "选课记录不存在"
            
            # 检查是否已有成绩记录
            existing_grade = self._get_grade_by_enrollment(enrollment_id)
            
            if existing_grade:
                # 更新成绩
                grade_data = {
                    'score': score,
                    'grade_level': grade_level,
                    'gpa': gpa,
                    'remarks': remarks,
                    'input_by': teacher_id,
                    'updated_at': 'CURRENT_TIMESTAMP'
                }
                
                count = self.db.update_data('grades', grade_data, 
                                           {'grade_id': existing_grade['grade_id']})
                
                if count > 0:
                    Logger.info(f"更新成绩成功: 学生{enrollment['student_id']}, 课程{enrollment['course_name']}, 成绩{score}")
                    return True, "成绩更新成功"
                else:
                    return False, "更新成绩失败"
            else:
                # 新增成绩记录
                grade_data = {
                    'enrollment_id': enrollment_id,
                    'student_id': enrollment['student_id'],
                    'offering_id': enrollment['offering_id'],
                    'score': score,
                    'grade_level': grade_level,
                    'gpa': gpa,
                    'remarks': remarks,
                    'input_by': teacher_id
                }
                
                grade_id = self.db.insert_data('grades', grade_data)
                
                if grade_id:
                    # 更新选课状态为已完成
                    self.db.update_data('enrollments', 
                                      {'status': 'completed'}, 
                                      {'enrollment_id': enrollment_id})
                    
                    Logger.info(f"录入成绩成功: 学生{enrollment['student_id']}, 课程{enrollment['course_name']}, 成绩{score}")
                    return True, "成绩录入成功"
                else:
                    return False, "录入成绩失败"
            
        except Exception as e:
            Logger.error(f"录入成绩失败: {e}")
            return False, "录入成绩失败，请稍后重试"
    
    def get_student_grades(self, student_id: str, semester: str = None) -> List[Dict]:
        """
        获取学生成绩
        
        Args:
            student_id: 学号
            semester: 学期（可选）
        
        Returns:
            成绩列表
        """
        sql = """
            SELECT 
                g.grade_id,
                g.score,
                g.grade_level,
                g.gpa,
                g.exam_type,
                g.remarks,
                g.input_date,
                co.semester,
                c.course_id,
                c.course_name,
                c.credits,
                c.course_type,
                t.name as teacher_name
            FROM grades g
            JOIN enrollments e ON g.enrollment_id = e.enrollment_id
            JOIN course_offerings co ON g.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            JOIN teachers t ON co.teacher_id = t.teacher_id
            WHERE g.student_id = ?
        """
        
        params = [student_id]
        
        if semester:
            sql += " AND co.semester = ?"
            params.append(semester)
        
        sql += " ORDER BY co.semester DESC, c.course_id"
        
        return self.db.execute_query(sql, tuple(params))
    
    def get_course_grades(self, offering_id: int) -> List[Dict]:
        """
        获取某门课程的所有学生成绩
        
        Args:
            offering_id: 开课计划ID
        
        Returns:
            成绩列表
        """
        sql = """
            SELECT 
                g.grade_id,
                g.enrollment_id,
                g.student_id,
                s.name as student_name,
                s.major,
                s.class_name,
                g.score,
                g.grade_level,
                g.gpa,
                g.remarks,
                g.input_date
            FROM grades g
            JOIN students s ON g.student_id = s.student_id
            WHERE g.offering_id = ?
            ORDER BY s.student_id
        """
        
        return self.db.execute_query(sql, (offering_id,))
    
    def calculate_student_gpa(self, student_id: str, semester: str = None) -> float:
        """
        计算学生GPA
        
        Args:
            student_id: 学号
            semester: 学期（可选，不传则计算总GPA）
        
        Returns:
            GPA值
        """
        sql = """
            SELECT 
                g.gpa,
                c.credits
            FROM grades g
            JOIN course_offerings co ON g.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE g.student_id = ?
        """
        
        params = [student_id]
        
        if semester:
            sql += " AND co.semester = ?"
            params.append(semester)
        
        result = self.db.execute_query(sql, tuple(params))
        
        if not result:
            return 0.0
        
        # 加权平均GPA
        total_credits = 0.0
        weighted_gpa = 0.0
        
        for record in result:
            gpa = record['gpa'] or 0
            credits = record['credits'] or 0
            weighted_gpa += gpa * credits
            total_credits += credits
        
        return round(weighted_gpa / total_credits, 2) if total_credits > 0 else 0.0
    
    def get_grade_statistics(self, offering_id: int) -> Dict:
        """
        获取某门课程的成绩统计
        
        Args:
            offering_id: 开课计划ID
        
        Returns:
            统计信息字典
        """
        sql = """
            SELECT 
                COUNT(*) as total_count,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score,
                SUM(CASE WHEN score >= 90 THEN 1 ELSE 0 END) as excellent_count,
                SUM(CASE WHEN score >= 80 AND score < 90 THEN 1 ELSE 0 END) as good_count,
                SUM(CASE WHEN score >= 70 AND score < 80 THEN 1 ELSE 0 END) as medium_count,
                SUM(CASE WHEN score >= 60 AND score < 70 THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN score < 60 THEN 1 ELSE 0 END) as fail_count
            FROM grades
            WHERE offering_id = ?
        """
        
        result = self.db.execute_query(sql, (offering_id,))
        
        if result and result[0]['total_count'] > 0:
            stats = result[0]
            return {
                'total_count': stats['total_count'],
                'avg_score': round(stats['avg_score'], 2) if stats['avg_score'] else 0,
                'max_score': stats['max_score'],
                'min_score': stats['min_score'],
                'excellent_count': stats['excellent_count'],
                'good_count': stats['good_count'],
                'medium_count': stats['medium_count'],
                'pass_count': stats['pass_count'],
                'fail_count': stats['fail_count'],
                'pass_rate': round((stats['total_count'] - stats['fail_count']) / stats['total_count'] * 100, 2)
            }
        else:
            return {
                'total_count': 0,
                'avg_score': 0,
                'max_score': 0,
                'min_score': 0,
                'excellent_count': 0,
                'good_count': 0,
                'medium_count': 0,
                'pass_count': 0,
                'fail_count': 0,
                'pass_rate': 0
            }
    
    def get_grade_distribution(self, offering_id: int) -> Dict[str, int]:
        """
        获取成绩分布
        
        Args:
            offering_id: 开课计划ID
        
        Returns:
            各等级人数字典
        """
        sql = """
            SELECT 
                grade_level,
                COUNT(*) as count
            FROM grades
            WHERE offering_id = ?
            GROUP BY grade_level
        """
        
        result = self.db.execute_query(sql, (offering_id,))
        
        distribution = {}
        for record in result:
            distribution[record['grade_level']] = record['count']
        
        return distribution
    
    def get_student_transcript(self, student_id: str) -> Dict:
        """
        获取学生成绩单（含GPA）
        
        Args:
            student_id: 学号
        
        Returns:
            成绩单信息
        """
        # 获取所有成绩
        grades = self.get_student_grades(student_id)
        
        # 计算总GPA
        total_gpa = self.calculate_student_gpa(student_id)
        
        # 统计学分
        total_credits = sum(g['credits'] for g in grades)
        earned_credits = sum(g['credits'] for g in grades if g['score'] and g['score'] >= 60)
        
        return {
            'student_id': student_id,
            'grades': grades,
            'total_gpa': total_gpa,
            'total_credits': total_credits,
            'earned_credits': earned_credits
        }
    
    def _get_enrollment_info(self, enrollment_id: int) -> Optional[Dict]:
        """获取选课信息"""
        sql = """
            SELECT 
                e.*,
                c.course_name
            FROM enrollments e
            JOIN course_offerings co ON e.offering_id = co.offering_id
            JOIN courses c ON co.course_id = c.course_id
            WHERE e.enrollment_id = ?
        """
        result = self.db.execute_query(sql, (enrollment_id,))
        return result[0] if result else None
    
    def _get_grade_by_enrollment(self, enrollment_id: int) -> Optional[Dict]:
        """根据选课记录ID获取成绩"""
        sql = "SELECT * FROM grades WHERE enrollment_id = ?"
        result = self.db.execute_query(sql, (enrollment_id,))
        return result[0] if result else None

