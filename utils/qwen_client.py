"""
Qwen API 客户端 - 用于生成学习建议
支持通过 OpenAI 兼容接口调用通义千问模型
"""

import os
import time
from typing import Optional, Dict, List
from openai import OpenAI
from utils.logger import Logger


class QwenAdvisor:
    """Qwen 学习建议生成器"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "qwen-plus"):
        """
        初始化 Qwen 客户端
        
        Args:
            api_key: API密钥，如果不提供则从环境变量 DASH_SCOPE_API_KEY 读取
            model: 模型名称，默认为 qwen-plus
        """
        key = api_key or os.getenv("DASH_SCOPE_API_KEY")
        if not key:
            raise RuntimeError("Qwen API key missing. Please set DASH_SCOPE_API_KEY environment variable.")
        
        # 禁用代理，直接连接API服务器
        # 如果系统配置了代理但代理不可用，会导致连接失败
        import httpx
        
        # 临时清除环境变量中的代理设置（仅对当前进程有效）
        original_proxies = {}
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ[var]
                del os.environ[var]
        
        try:
            # 创建HTTP客户端，明确禁用代理并设置超时
            # 注意：httpx.Client 不直接接受 proxies 参数，需要通过 transport 或环境变量控制
            http_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,  # 连接超时10秒
                    read=60.0,     # 读取超时60秒（AI生成可能需要较长时间）
                    write=10.0,    # 写入超时10秒
                    pool=10.0      # 连接池超时10秒
                ),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                follow_redirects=True
            )
            
            self.client = OpenAI(
                api_key=key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                http_client=http_client
            )
        except Exception as e:
            # 如果出错，恢复原始代理设置
            for var, value in original_proxies.items():
                os.environ[var] = value
            raise
        
        self.model = model
        Logger.info(f"QwenAdvisor initialized with model: {model}")
    
    def advise(self, student_info: Dict, courses: List[Dict], 
               past_semester_courses: List[Dict] = None,
               past_semester_grades: List[Dict] = None,
               next_semester_courses: List[Dict] = None,
               timeout: int = 60) -> str:
        """
        生成学习建议
        
        Args:
            student_info: 学生信息字典，包含 name, id, major, college, grade 等
            courses: 当前学期的已选课程列表
            past_semester_courses: 以往学期的已选课程列表
            past_semester_grades: 以往学期的成绩列表
            next_semester_courses: 下个学期的推荐课程列表
            timeout: 超时时间（秒），默认60秒
        
        Returns:
            生成的学习建议文本
        
        Raises:
            RuntimeError: API调用失败或超时
        """
        try:
            # 格式化学生信息
            student_text = self._format_student_info(student_info)
            
            # 格式化课程信息
            courses_text = self._format_courses(courses)
            
            # 格式化以往学期的课程
            past_courses_text = ""
            if past_semester_courses:
                past_courses_text = self._format_courses(past_semester_courses)
            
            # 格式化以往学期的成绩
            past_grades_text = ""
            if past_semester_grades:
                past_grades_text = self._format_grades(past_semester_grades)
            
            # 格式化下个学期的推荐课程
            next_courses_text = ""
            if next_semester_courses:
                next_courses_text = self._format_courses(next_semester_courses)
            
            # 构建提示词
            prompt = self._build_prompt(
                student_text, 
                courses_text,
                past_courses_text=past_courses_text,
                past_grades_text=past_grades_text,
                next_courses_text=next_courses_text
            )
            
            Logger.info(f"Calling Qwen API for student: {student_info.get('name', 'Unknown')}")
            start_time = time.time()
            
            # 调用API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的教学顾问，擅长根据学生的专业背景、学院特色和当前行业趋势，为学生提供个性化的学习建议和职业规划指导。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                timeout=timeout
            )
            
            elapsed_time = time.time() - start_time
            advice = response.choices[0].message.content.strip()
            
            Logger.info(f"Qwen API call completed in {elapsed_time:.2f}s")
            return advice
            
        except Exception as e:
            error_str = str(e)
            error_msg = f"Qwen API调用失败: {error_str}"
            
            # 提供更友好的错误提示
            if "Connection error" in error_str or "10061" in error_str or "积极拒绝" in error_str:
                error_msg += "\n\n可能的原因：\n"
                error_msg += "1. 网络连接问题或防火墙阻止\n"
                error_msg += "2. 系统代理配置问题（已自动禁用代理，如仍有问题请检查网络设置）\n"
                error_msg += "3. API服务暂时不可用，请稍后重试\n"
                error_msg += "4. 请检查是否能访问 https://dashscope.aliyuncs.com"
            elif "timed out" in error_str.lower() or "timeout" in error_str.lower():
                error_msg += "\n\n可能的原因：\n"
                error_msg += "1. 网络响应较慢，请求超时（已设置60秒超时）\n"
                error_msg += "2. API服务繁忙，请稍后重试\n"
                error_msg += "3. 网络连接不稳定\n"
                error_msg += "4. 提示词过长，导致处理时间过长"
            
            Logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
    
    def _format_student_info(self, student_info: Dict) -> str:
        """格式化学生信息"""
        lines = [
            f"姓名：{student_info.get('name', '未知')}",
            f"学号：{student_info.get('id', '未知')}",
        ]
        
        if student_info.get('major'):
            lines.append(f"专业：{student_info.get('major')}")
        
        if student_info.get('college'):
            lines.append(f"学院：{student_info.get('college')}")
        
        if student_info.get('grade'):
            lines.append(f"年级：{student_info.get('grade')}级")
        
        if student_info.get('class_name'):
            lines.append(f"班级：{student_info.get('class_name')}")
        
        return "\n".join(lines)
    
    def _format_courses(self, courses: List[Dict]) -> str:
        """格式化课程列表"""
        if not courses:
            return "暂无课程"
        
        lines = []
        for i, course in enumerate(courses, 1):
            course_line = f"{i}. {course.get('course_name', '未知课程')}"
            
            if course.get('course_id'):
                course_line += f"（{course.get('course_id')}）"
            
            if course.get('credits'):
                course_line += f" - {course.get('credits')}学分"
            
            if course.get('course_type'):
                course_line += f" - {course.get('course_type')}"
            
            if course.get('teacher_name'):
                course_line += f" - 授课教师：{course.get('teacher_name')}"
            
            if course.get('semester'):
                course_line += f" - 学期：{course.get('semester')}"
            
            lines.append(course_line)
        
        return "\n".join(lines)
    
    def _format_grades(self, grades: List[Dict]) -> str:
        """格式化成绩列表"""
        if not grades:
            return "暂无成绩记录"
        
        lines = []
        for i, grade in enumerate(grades, 1):
            grade_line = f"{i}. {grade.get('course_name', '未知课程')}"
            
            if grade.get('course_id'):
                grade_line += f"（{grade.get('course_id')}）"
            
            if grade.get('score') is not None:
                grade_line += f" - 分数：{grade.get('score')}"
            
            if grade.get('gpa') is not None:
                grade_line += f" - 绩点：{grade.get('gpa')}"
            
            if grade.get('grade_level'):
                grade_line += f" - 等级：{grade.get('grade_level')}"
            
            if grade.get('semester'):
                grade_line += f" - 学期：{grade.get('semester')}"
            
            lines.append(grade_line)
        
        return "\n".join(lines)
    
    def _build_prompt(self, student_text: str, courses_text: str,
                     past_courses_text: str = "",
                     past_grades_text: str = "",
                     next_courses_text: str = "") -> str:
        """构建提示词"""
        prompt = f"""请为以下学生提供学习建议和职业规划指导。

【学生信息】
{student_text}

【当前学期已选课程】
{courses_text}
"""
        
        if past_courses_text:
            prompt += f"""
【以往学期已选课程】
{past_courses_text}
"""
        
        if past_grades_text:
            prompt += f"""
【以往学期成绩】
{past_grades_text}
"""
        
        if next_courses_text:
            prompt += f"""
【下个学期推荐课程】
{next_courses_text}
"""
        
        prompt += """
【要求】
1. 结合学生的专业背景、学院特色和当前行业发展趋势，对当前学期每门已选课程提供具体的学习建议（每门课程1-2条建议）
2. 基于以往学期的成绩表现，分析学生的学习优势和薄弱环节，给出针对性的改进建议
3. 分析学生当前选课结构的合理性，结合以往学期的课程和成绩，指出优势和可能的不足
4. 根据下个学期的推荐课程，提供选课建议和学习准备建议
5. 根据专业特点和行业趋势，提供整体学习规划建议和未来发展方向
6. 建议要具体、实用，避免空泛的套话

请用清晰的结构组织回答，可以使用以下格式：
## 当前学期课程学习建议
（逐门课程分析，结合以往成绩表现）

## 学习表现分析
（基于以往学期成绩，分析学习优势和薄弱环节）

## 选课结构分析
（结合以往学期课程和当前学期课程，整体评价）

## 下个学期选课建议
（基于培养方案和当前学习情况，提供选课建议）

## 学习规划建议
（未来发展方向）

## 职业发展建议
（结合行业趋势）
"""
        return prompt