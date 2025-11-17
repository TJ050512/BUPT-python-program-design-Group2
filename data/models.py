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
    password: Optional[str] = None
    gender: Optional[str] = None
    major: Optional[str] = None
    grade: Optional[int] = None
    class_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = 'active'
    college_code: Optional[str] = None
    major_id: Optional[int] = None
    admission_type: Optional[str] = None
    program_years: Optional[int] = None

    def generate_id(self):
        """根据 grade 和 college_code 自动生成学号"""
        return f"{self.grade}{self.college_code}{self.student_id[-3:]}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        if self.student_id and self.college_code and not self.student_id.startswith(str(self.grade)):
            self.student_id = f"{self.grade}{self.college_code}{self.student_id[-3:]}"
        return {
            'student_id': self.student_id,
            'college_code': self.college_code,
            'major_id': self.major_id,
            'name': self.name,
            'password': self.password,
            'gender': self.gender,
            'major': self.major,
            'grade': self.grade,
            'class_name': self.class_name,
            'email': self.email,
            'phone': self.phone,
            'status': self.status,
            'admission_type': self.admission_type,
            'program_years': self.program_years,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Student":
        return cls(
            student_id=str(d.get('student_id') or d.get('id') or ''),
            college_code=d.get('college_code'),
            major_id=d.get('major_id'),
            name=d.get('name') or '',
            password=d.get('password'),
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
class College:
    college_code: str
    name: str
    dean_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "college_code": self.college_code,
            "name": self.name,
            "dean_name": self.dean_name
        }

@dataclass
class Major:
    major_id: Optional[int]
    college_code: str
    name: str
    code: Optional[str]=None
    def to_dict(self):
        return {"major_id": self.major_id, "college_code": self.college_code, "name": self.name, "code": self.code}


@dataclass
class Classroom:
    classroom_id: Optional[int]
    name: str
    location_type: str
    seat_count: int
    room_type: str
    available_equipment: Optional[str] = None
    def to_dict(self):
        return {
            "classroom_id": self.classroom_id,
            "name": self.name,
            "location_type": self.location_type,
            "seat_count": self.seat_count,
            "room_type": self.room_type,
            "available_equipment": self.available_equipment
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
    prerequisite: Optional[str] = None
    max_students: Optional[int] = 60
    is_public_elective: Optional[int] = 0
    credit_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        d = {
            'course_id': self.course_id,
            'course_name': self.course_name,
            'credits': self.credits,
            'hours': self.hours,
            'course_type': self.course_type,
            'department': self.department,
            'description': self.description,
            'prerequisite': self.prerequisite,
            'is_public_elective': self.is_public_elective,
            'credit_type': self.credit_type,
            'max_students': self.max_students
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Course":
        return cls(
            course_id=str(d.get('course_id') or d.get('id') or ''),
            course_name=d.get('course_name') or d.get('name') or '',
            credits=float(d.get('credits') or 0.0),
            hours=int(d.get('hours') or 0),
            course_type=d.get('course_type') or '',
            department=d.get('department'),
            is_public_elective=int(d.get('is_public_elective') or 0),
            credit_type=d.get('credit_type'),
            description=d.get('description')
        )


@dataclass
class CourseOffering:
    """开课计划数据模型"""
    offering_id: Optional[int] = None
    course_id: str = ''
    course_name: Optional[str] = None
    teacher_id: Optional[str] = None
    ta1_id: Optional[str] = None           # 助教 1
    ta2_id: Optional[str] = None           # 助教 2
    teacher_name: Optional[str] = None
    department: Optional[str] = None       # 开课学院
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
            'ta1_id': self.ta1_id,
            'ta2_id': self.ta2_id,
            'department': self.department,
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
            teacher_name = d.get("teacher_name") or d.get("name"),
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
    exam_type: Optional[str] = None
    remarks: Optional[str] = None
    is_makeup: Optional[int] = 0
    exam_round: Optional[int] = None

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


@dataclass
class TimeSlot:
    slot_id: Optional[int]
    day_of_week: int
    section_no: int
    starts_at: str
    ends_at: str
    session: str  # AM/PM/EVENING
    def to_dict(self):
        return {"slot_id": self.slot_id, "day_of_week": self.day_of_week, "section_no": self.section_no,
                "starts_at": self.starts_at, "ends_at": self.ends_at, "session": self.session}


@dataclass
class ProgramCourse:
    id: Optional[int]
    major_id: int
    course_id: str
    course_category: str   # 必修/选修/公选
    cross_major_quota: int = 0
    grade_recommendation: Optional[int] = None
    def to_dict(self):
        return {"id": self.id, "major_id": self.major_id, "course_id": self.course_id,
                "course_category": self.course_category, "cross_major_quota": self.cross_major_quota,
                "grade_recommendation": self.grade_recommendation}