"""
数据模型类
定义系统中的核心数据对象
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


def _parse_datetime(val: Any) -> Optional[str]:
    """把可能的 datetime 或字符串规范化为 'YYYY-MM-DD HH:MM:SS' 或返回 None"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    try:
        # 尝试解析已是字符串的时间
        return datetime.fromisoformat(str(val)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(val)


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

    def to_dict(self) -> Dict[str, Any]:
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Student":
        return cls(
            student_id=str(d.get('student_id') or d.get('id') or ''),
            name=d.get('name') or '',
            gender=d.get('gender'),
            major=d.get('major'),
            grade=d.get('grade'),
            class_name=d.get('class_name') or d.get('class'),
            email=d.get('email'),
            phone=d.get('phone'),
            status=d.get('status') or 'active'
        )


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

    def to_dict(self) -> Dict[str, Any]:
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Teacher":
        return cls(
            teacher_id=str(d.get('teacher_id') or d.get('id') or ''),
            name=d.get('name') or '',
            gender=d.get('gender'),
            title=d.get('title'),
            department=d.get('department'),
            email=d.get('email'),
            phone=d.get('phone'),
            status=d.get('status') or 'active'
        )


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

    def to_dict(self) -> Dict[str, Any]:
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Course":
        return cls(
            course_id=str(d.get('course_id') or d.get('id') or ''),
            course_name=d.get('course_name') or d.get('name') or '',
            credits=float(d.get('credits') or 0.0),
            hours=int(d.get('hours') or 0),
            course_type=d.get('course_type') or '',
            department=d.get('department'),
            description=d.get('description')
        )


@dataclass
class CourseOffering:
    """开课计划数据模型"""
    offering_id: Optional[int] = None
    course_id: str = ''
    course_name: Optional[str] = None
    teacher_id: Optional[str] = None
    teacher_name: Optional[str] = None
    semester: str = ''
    class_time: Optional[str] = None
    classroom: Optional[str] = None
    current_students: int = 0
    max_students: int = 60
    status: str = 'open'
    credits: float = 0.0

    def is_full(self) -> bool:
        """是否已满"""
        return self.current_students >= self.max_students

    def to_dict(self) -> Dict[str, Any]:
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CourseOffering":
        return cls(
            offering_id=d.get('offering_id') or d.get('id'),
            course_id=str(d.get('course_id') or ''),
            course_name=d.get('course_name'),
            teacher_id=d.get('teacher_id'),
            teacher_name=d.get('teacher_name'),
            semester=d.get('semester') or '',
            class_time=d.get('class_time'),
            classroom=d.get('classroom'),
            current_students=int(d.get('current_students') or 0),
            max_students=int(d.get('max_students') or 60),
            status=d.get('status') or 'open',
            credits=float(d.get('credits') or 0.0)
        )


@dataclass
class Enrollment:
    """选课记录数据模型"""
    enrollment_id: Optional[int] = None
    student_id: str = ''
    offering_id: int = 0
    semester: str = ''
    enrollment_date: Optional[str] = None
    status: str = 'enrolled'

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enrollment_id': self.enrollment_id,
            'student_id': self.student_id,
            'offering_id': self.offering_id,
            'semester': self.semester,
            'enrollment_date': _parse_datetime(self.enrollment_date) if self.enrollment_date else None,
            'status': self.status
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Enrollment":
        return cls(
            enrollment_id=d.get('enrollment_id') or d.get('id'),
            student_id=str(d.get('student_id') or ''),
            offering_id=int(d.get('offering_id') or 0),
            semester=d.get('semester') or '',
            enrollment_date=_parse_datetime(d.get('enrollment_date')) if d.get('enrollment_date') else None,
            status=d.get('status') or 'enrolled'
        )


@dataclass
class Grade:
    """成绩数据模型"""
    grade_id: Optional[int] = None
    enrollment_id: int = 0
    student_id: str = ''
    offering_id: int = 0
    course_name: str = ''
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

    def to_dict(self) -> Dict[str, Any]:
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

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Grade":
        return cls(
            grade_id=d.get('grade_id') or d.get('id'),
            enrollment_id=int(d.get('enrollment_id') or 0),
            student_id=str(d.get('student_id') or ''),
            offering_id=int(d.get('offering_id') or 0),
            course_name=d.get('course_name') or '',
            score=(None if d.get('score') is None else float(d.get('score'))),
            grade_level=d.get('grade_level'),
            gpa=(None if d.get('gpa') is None else float(d.get('gpa'))),
            credits=float(d.get('credits') or 0.0),
            semester=d.get('semester')
        )

