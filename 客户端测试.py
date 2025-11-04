"""
北京邮电大学教学管理系统 - 远程客户端测试脚本
用于测试连接到远程服务器
"""

import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from network.client import Client
from network.protocol import Protocol
from utils.logger import Logger


def test_connection(host: str, port: int = 8888):
    """
    测试与服务器的连接
    
    Args:
        host: 服务器IP地址
        port: 端口号
    """
    
    print("\n" + "=" * 70)
    print(f"🌐 连接测试: {host}:{port}")
    print("=" * 70)
    
    # 创建客户端
    client = Client(host=host, port=port, timeout=10)
    
    # 1. 测试连接
    print("\n[1] 测试连接服务器...")
    success, msg = client.connect()
    if not success:
        print(f"✗ 连接失败: {msg}")
        print("\n可能的原因：")
        print("  1. 服务器未启动")
        print("  2. IP地址或端口错误")
        print("  3. 防火墙阻止连接")
        print("  4. 两台电脑不在同一局域网")
        return False
    
    print(f"✓ 连接成功")
    
    # 2. 测试学生登录
    print("\n[2] 测试学生登录...")
    response = client.login('2021211001', 'student123')
    if response and response.get('status') == Protocol.STATUS_SUCCESS:
        print(f"✓ 登录成功")
        student_data = response.get('data', {})
        print(f"  用户信息: {student_data['name']} ({student_data['user_type']})")
        student_id = student_data['id']
    else:
        print(f"✗ 登录失败: {response.get('message') if response else '无响应'}")
        client.disconnect()
        return False
    
    # 3. 测试获取可选课程
    print("\n[3] 测试获取可选课程...")
    request = Protocol.create_request(
        action='get_courses',
        data={'semester': '2024-2025-2'}
    )
    response = client.send_request(request)
    if response and response.get('status') == Protocol.STATUS_SUCCESS:
        courses = response.get('data', {}).get('courses', [])
        print(f"✓ 获取成功，共{len(courses)}门课程")
        for i, course in enumerate(courses[:5], 1):
            print(f"  {i}. {course['course_name']} - {course['teacher_name']}")
    else:
        print(f"✗ 获取失败")
    
    # 4. 测试获取成绩
    print("\n[4] 测试获取成绩...")
    request = Protocol.create_request(
        action='get_grades',
        data={
            'student_id': student_id,
            'semester': '2024-2025-2'
        }
    )
    response = client.send_request(request)
    if response and response.get('status') == Protocol.STATUS_SUCCESS:
        data = response.get('data', {})
        grades = data.get('grades', [])
        gpa = data.get('gpa', 0)
        print(f"✓ 获取成功，共{len(grades)}条成绩记录，GPA: {gpa:.2f}")
    else:
        print(f"✗ 获取失败")
    
    # 5. 测试教师登录
    print("\n[5] 测试教师登录...")
    response = client.login('teacher001', 'teacher123')
    if response and response.get('status') == Protocol.STATUS_SUCCESS:
        print(f"✓ 登录成功")
        teacher_data = response.get('data', {})
        print(f"  教师信息: {teacher_data['name']} ({teacher_data.get('title', '')})")
        teacher_id = teacher_data['id']
    else:
        print(f"✗ 登录失败")
        client.disconnect()
        return False
    
    # 6. 测试获取教师课程
    print("\n[6] 测试获取教师课程...")
    request = Protocol.create_request(
        action='get_teacher_courses',
        data={
            'teacher_id': teacher_id,
            'semester': '2024-2025-2'
        }
    )
    response = client.send_request(request)
    if response and response.get('status') == Protocol.STATUS_SUCCESS:
        courses = response.get('data', {}).get('courses', [])
        print(f"✓ 获取成功，共{len(courses)}门课程")
        for i, c in enumerate(courses, 1):
            print(f"  {i}. {c['course_name']} - 选课人数:{c['current_students']}/{c['max_students']}")
    else:
        print(f"✗ 获取失败")
    
    # 断开连接
    print("\n[7] 断开连接...")
    client.disconnect()
    print("✓ 已断开连接")
    
    return True


def main():
    """主函数"""
    
    print("\n" + "=" * 70)
    print("🌐 北京邮电大学教学管理系统 - 客户端测试工具")
    print("=" * 70)
    
    # 初始化日志（可选）
    # Logger.init()
    
    # 获取服务器地址
    if len(sys.argv) > 1:
        host = sys.argv[1]
    else:
        print("\n请输入服务器IP地址:")
        print("  本机测试: localhost 或 127.0.0.1")
        print("  局域网测试: 例如 192.168.1.100")
        host = input("\n服务器IP: ").strip()
        
        if not host:
            host = 'localhost'
            print(f"使用默认地址: {host}")
    
    # 获取端口
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("端口号无效，使用默认端口 8888")
            port = 8888
    else:
        port = 8888
    
    print(f"\n目标服务器: {host}:{port}")
    
    # 运行测试
    try:
        success = test_connection(host, port)
        
        print("\n" + "=" * 70)
        if success:
            print("✓ 所有测试通过！网络连接正常")
        else:
            print("✗ 测试失败，请检查网络连接")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n收到中断信号")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

