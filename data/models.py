"""
数据模型类
定义系统中的核心数据对象
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Student:
    """学生数据模型"""
    student_id: str
    name: str
    gender: Optional[str] = None
    major: Optional[str] = None
    grade: Optional[int] = None
    class_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = 'active'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'student_id': self.student_id,
            'name': self.name,
            'gender': self.gender,
            'major': self.major,
            'grade': self.grade,
            'class_name': self.class_name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status
        }


@dataclass
class Teacher:
    """教师数据模型"""
    teacher_id: str
    name: str
    gender: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = 'active'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'teacher_id': self.teacher_id,
            'name': self.name,
            'gender': self.gender,
            'title': self.title,
            'department': self.department,
            'email': self.email,
            'phone': self.phone,
            'status': self.status
        }


@dataclass
class Course:
    """课程数据模型"""
    course_id: str
    course_name: str
    credits: float
    hours: int
    course_type: str
    department: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'credits': self.credits,
            'hours': self.hours,
            'course_type': self.course_type,
            'department': self.department,
            'description': self.description
        }


@dataclass
class CourseOffering:
    """开课计划数据模型"""
    offering_id: int
    course_id: str
    course_name: str
    teacher_id: str
    teacher_name: str
    semester: str
    class_time: Optional[str] = None
    classroom: Optional[str] = None
    current_students: int = 0
    max_students: int = 60
    status: str = 'open'
    credits: float = 0.0
    
    def is_full(self) -> bool:
        """是否已满"""
        return self.current_students >= self.max_students
    
    def to_dict(self):
        """转换为字典"""
        return {
            'offering_id': self.offering_id,
            'course_id': self.course_id,
            'course_name': self.course_name,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher_name,
            'semester': self.semester,
            'class_time': self.class_time,
            'classroom': self.classroom,
            'current_students': self.current_students,
            'max_students': self.max_students,
            'status': self.status,
            'credits': self.credits
        }


@dataclass
class Enrollment:
    """选课记录数据模型"""
    enrollment_id: int
    student_id: str
    offering_id: int
    semester: str
    enrollment_date: str
    status: str = 'enrolled'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'enrollment_id': self.enrollment_id,
            'student_id': self.student_id,
            'offering_id': self.offering_id,
            'semester': self.semester,
            'enrollment_date': self.enrollment_date,
            'status': self.status
        }


@dataclass
class Grade:
    """成绩数据模型"""
    grade_id: int
    enrollment_id: int
    student_id: str
    offering_id: int
    course_name: str
    score: Optional[float] = None
    grade_level: Optional[str] = None
    gpa: Optional[float] = None
    credits: float = 0.0
    semester: Optional[str] = None
    
    @staticmethod
    def calculate_gpa(score: float) -> tuple[str, float]:
        """
        根据分数计算等级和GPA
        
        Args:
            score: 分数（0-100）
        
        Returns:
            (等级, GPA)
        """
        if score >= 90:
            return 'A', 4.0
        elif score >= 85:
            return 'A-', 3.7
        elif score >= 82:
            return 'B+', 3.3
        elif score >= 78:
            return 'B', 3.0
        elif score >= 75:
            return 'B-', 2.7
        elif score >= 72:
            return 'C+', 2.3
        elif score >= 68:
            return 'C', 2.0
        elif score >= 64:
            return 'C-', 1.5
        elif score >= 60:
            return 'D', 1.0
        else:
            return 'F', 0.0
    
    def to_dict(self):
        """转换为字典"""
        return {
            'grade_id': self.grade_id,
            'enrollment_id': self.enrollment_id,
            'student_id': self.student_id,
            'offering_id': self.offering_id,
            'course_name': self.course_name,
            'score': self.score,
            'grade_level': self.grade_level,
            'gpa': self.gpa,
            'credits': self.credits,
            'semester': self.semester
        }

