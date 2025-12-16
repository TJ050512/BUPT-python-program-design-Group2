"""
北京邮电大学教学管理系统 - 网络服务器启动脚本
支持远程客户端连接
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from network.server import Server
from network.protocol import Protocol
from utils.logger import Logger
from data.database import get_database
from core.user_manager import UserManager
from core.course_manager import CourseManager
from core.enrollment_manager import EnrollmentManager
from core.grade_manager import GradeManager


class ProductionServer:
    """生产环境服务器"""
    
    def __init__(self, host='0.0.0.0', port=8888):
        """
        初始化服务器
        
        Args:
            host: 监听地址，0.0.0.0表示监听所有网络接口
            port: 端口号
        """
        self.server = Server(host=host, port=port, max_connections=20)
        self.db = get_database()
        self.db.init_demo_data()
        
        # 初始化业务管理器
        self.user_manager = UserManager(self.db)
        self.course_manager = CourseManager(self.db)
        self.enrollment_manager = EnrollmentManager(self.db)
        self.grade_manager = GradeManager(self.db)
        
        # 注册所有处理器
        self.register_handlers()
    
    def register_handlers(self):
        """注册消息处理器"""
        
        # 1. 登录处理
        def handle_login(request):
            data = request.get('data', {})
            username = data.get('username')
            password = data.get('password')
            
            Logger.info(f"处理登录请求: {username}")
            
            success, user, msg = self.user_manager.login(username, password)
            
            if success:
                return Protocol.create_response(
                    status=Protocol.STATUS_SUCCESS,
                    data=user.to_dict(),
                    message="登录成功"
                )
            else:
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=msg
                )
        
        # 2. 获取可选课程
        def handle_get_courses(request):
            data = request.get('data', {})
            
            courses = self.course_manager.get_available_courses()
            
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data={'courses': courses},
                message=f"获取到{len(courses)}门课程"
            )
        
        # 3. 选课
        def handle_enroll(request):
            data = request.get('data', {})
            student_id = data.get('student_id')
            offering_id = data.get('offering_id')
            
            success, msg = self.enrollment_manager.enroll_course(
                student_id, offering_id
            )
            
            if success:
                return Protocol.create_response(
                    status=Protocol.STATUS_SUCCESS,
                    message=msg
                )
            else:
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=msg
                )
        
        # 4. 退课
        def handle_drop(request):
            data = request.get('data', {})
            student_id = data.get('student_id')
            offering_id = data.get('offering_id')
            
            success, msg = self.enrollment_manager.drop_course(student_id, offering_id)
            
            if success:
                return Protocol.create_response(
                    status=Protocol.STATUS_SUCCESS,
                    message=msg
                )
            else:
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=msg
                )
        
        # 5. 获取学生选课记录
        def handle_get_enrollments(request):
            data = request.get('data', {})
            student_id = data.get('student_id')
            
            enrollments = self.enrollment_manager.get_student_enrollments(
                student_id
            )
            
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data={'enrollments': enrollments},
                message=f"获取到{len(enrollments)}条选课记录"
            )
        
        # 6. 获取学生成绩
        def handle_get_grades(request):
            data = request.get('data', {})
            student_id = data.get('student_id')
            
            grades = self.grade_manager.get_student_grades(student_id)
            gpa = self.grade_manager.calculate_student_gpa(student_id)
            
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data={'grades': grades, 'gpa': gpa},
                message=f"获取到{len(grades)}条成绩记录"
            )
        
        # 7. 录入成绩（教师）
        def handle_input_grade(request):
            data = request.get('data', {})
            enrollment_id = data.get('enrollment_id')
            score = data.get('score')
            teacher_id = data.get('teacher_id')
            
            success, msg = self.grade_manager.input_grade(
                enrollment_id, score, teacher_id
            )
            
            if success:
                return Protocol.create_response(
                    status=Protocol.STATUS_SUCCESS,
                    message=msg
                )
            else:
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=msg
                )
        
        # 8. 获取教师课程
        def handle_get_teacher_courses(request):
            data = request.get('data', {})
            teacher_id = data.get('teacher_id')
            
            courses = self.course_manager.get_teacher_courses(teacher_id)
            
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data={'courses': courses},
                message=f"获取到{len(courses)}门课程"
            )
        
        # 9. 获取课程学生名单
        def handle_get_course_students(request):
            data = request.get('data', {})
            offering_id = data.get('offering_id')
            
            students = self.enrollment_manager.get_course_students(offering_id)
            
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data={'students': students},
                message=f"获取到{len(students)}名学生"
            )
        
        # 10. 获取成绩统计
        def handle_get_statistics(request):
            data = request.get('data', {})
            offering_id = data.get('offering_id')
            
            stats = self.grade_manager.get_course_statistics(offering_id)
            
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data=stats,
                message="统计完成"
            )
        
        # 11. 执行SQL查询（用于登录等通用数据库操作）
        def handle_execute_query(request):
            data = request.get('data', {})
            sql = data.get('sql')
            params = data.get('params', ())
            
            Logger.debug(f"执行查询: {sql[:50]}...")
            
            try:
                results = self.db.execute_query(sql, params)
                return Protocol.create_response(
                    status=Protocol.STATUS_SUCCESS,
                    data=results,
                    message=f"查询成功，返回{len(results)}条记录"
                )
            except Exception as e:
                Logger.error(f"查询失败: {e}")
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=f"查询失败: {str(e)}"
                )
        
        # 12. 执行SQL更新（用于修改密码等更新操作）
        def handle_execute_update(request):
            data = request.get('data', {})
            sql = data.get('sql')
            params = data.get('params', ())
            
            Logger.debug(f"执行更新: {sql[:50]}...")
            
            try:
                affected = self.db.execute_update(sql, params)
                return Protocol.create_response(
                    status=Protocol.STATUS_SUCCESS,
                    data={'affected_rows': affected},
                    message=f"更新成功，影响{affected}行"
                )
            except Exception as e:
                Logger.error(f"更新失败: {e}")
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=f"更新失败: {str(e)}"
                )
        
        # 注册所有处理器
        self.server.register_handler(Protocol.ACTION_LOGIN, handle_login)
        self.server.register_handler('get_courses', handle_get_courses)
        self.server.register_handler('enroll', handle_enroll)
        self.server.register_handler('drop', handle_drop)
        self.server.register_handler('get_enrollments', handle_get_enrollments)
        self.server.register_handler('get_grades', handle_get_grades)
        self.server.register_handler('input_grade', handle_input_grade)
        self.server.register_handler('get_teacher_courses', handle_get_teacher_courses)
        self.server.register_handler('get_course_students', handle_get_course_students)
        self.server.register_handler('get_statistics', handle_get_statistics)
        self.server.register_handler('execute_query', handle_execute_query)
        self.server.register_handler('execute_update', handle_execute_update)
        
        Logger.info("所有消息处理器注册完成")
    
    def start(self):
        """启动服务器"""
        self.server.start()
    
    def stop(self):
        """停止服务器"""
        self.server.stop()


def get_local_ip():
    """获取本机局域网IP地址"""
    import socket
    try:
        # 创建一个UDP连接来获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "无法获取"


def main():
    """主函数"""
    
    print("=" * 70)
    print("🌐 北京邮电大学教学管理系统 - 网络服务器")
    print("=" * 70)
    
    # 初始化日志
    Logger.init()
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    print("\n📡 服务器信息：")
    print(f"  监听地址: 0.0.0.0:8888 (所有网络接口)")
    print(f"  本机IP: {local_ip}")
    print(f"  最大连接数: 20")
    
    print("\n💡 客户端连接方式：")
    print(f"  本机测试: python 客户端测试.py localhost")
    print(f"  局域网测试: python 客户端测试.py {local_ip}")
    print(f"  或直接: python 客户端测试.py {local_ip} 8888")
    print(f"  (其他电脑需要在同一局域网)")
    
    print("\n⚠️  防火墙提示：")
    print("  如果其他电脑无法连接，请确保：")
    print("  1. 防火墙允许Python或端口8888")
    print("     - Windows: 控制面板 > 防火墙 > 允许应用通过防火墙")
    print("     - macOS: 系统设置 > 网络 > 防火墙 > 选项")
    print("     - Linux: sudo ufw allow 8888")
    print("  2. 两台电脑在同一局域网（同一WiFi或同一网段）")
    print("  3. 杀毒软件未阻止连接")
    print("  4. 路由器未阻止内网通信")
    
    print("\n🔍 测试连接：")
    print(f"  在另一台电脑上运行: python 客户端测试.py {local_ip}")
    print(f"  或使用telnet测试: telnet {local_ip} 8888")
    
    print("\n" + "=" * 70)
    print("正在启动服务器...")
    print("=" * 70 + "\n")
    
    # 创建并启动服务器
    server = ProductionServer(host='0.0.0.0', port=8888)
    
    try:
        server.start()
    except KeyboardInterrupt:
        print("\n\n收到中断信号，正在停止服务器...")
        server.stop()
        print("服务器已停止")
    except Exception as e:
        print(f"\n✗ 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

