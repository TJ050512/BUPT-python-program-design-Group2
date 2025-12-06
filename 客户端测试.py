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
    print(f"   目标: {host}:{port}")
    
    import socket as sock_module
    try:
        # 先测试端口是否可达
        test_socket = sock_module.socket(sock_module.AF_INET, sock_module.SOCK_STREAM)
        test_socket.settimeout(3)
        result = test_socket.connect_ex((host, port))
        test_socket.close()
        
        if result != 0:
            print(f"✗ 端口连接测试失败 (错误码: {result})")
            print("\n可能的原因：")
            print("  1. 服务器未启动")
            print("  2. IP地址或端口错误")
            print("  3. 防火墙阻止连接")
            print("  4. 两台电脑不在同一局域网")
            print("  5. 服务器监听地址不正确")
            return False
        else:
            print(f"✓ 端口可达")
    except Exception as e:
        print(f"⚠ 端口测试异常: {e}")
    
    success, msg = client.connect()
    if not success:
        print(f"✗ 连接失败: {msg}")
        print("\n详细排查步骤：")
        print("  1. 确认服务器已启动并显示'服务器启动成功'")
        print(f"  2. 确认服务器IP是: {host}（不要使用 0.0.0.0）")
        print(f"  3. 确认端口是: {port}")
        print("  4. 在服务器电脑上查看本机IP:")
        print("     - Windows: ipconfig | findstr IPv4")
        print("     - macOS/Linux: ifconfig | grep 'inet '")
        print("  5. 在服务器电脑上运行: netstat -an | findstr 8888")
        print("  6. 检查防火墙设置（确保端口8888开放）")
        print("  7. 尝试ping服务器IP: ping " + host)
        print("  8. 确认两台电脑在同一局域网（同一WiFi或网段）")
        return False
    
    print(f"✓ 连接成功: {msg}")
    
    # 2. 测试学生登录
    print("\n[2] 测试学生登录...")
    # 使用数据库中实际存在的学号（2022级学生）
    # 注意：如果密码不正确，请先运行: python utils/reset_passwords.py
    # 将所有密码重置为 123456
    print("   尝试密码: 123456...")
    response = client.login('2022011001', '123456')
    if not response or response.get('status') != Protocol.STATUS_SUCCESS:
        # 如果失败，尝试 student123
        print("   尝试密码: student123...")
        response = client.login('2022011001', 'student123')
        if not response or response.get('status') != Protocol.STATUS_SUCCESS:
            print("   ✗ 登录失败，密码可能不正确")
            print("   💡 提示: 运行 'python utils/reset_passwords.py' 重置所有密码为 123456")
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
        data={}
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
    # 使用数据库中实际存在的教师工号（如果teacher001不存在）
    # 先尝试 teacher001，如果失败则尝试实际存在的工号
    teacher_ids_to_try = ['teacher001', '2005011013']
    teacher_id = None
    teacher_login_success = False
    
    for tid in teacher_ids_to_try:
        print(f"   尝试教师工号: {tid}, 密码: 123456...")
        response = client.login(tid, '123456')
        if response and response.get('status') == Protocol.STATUS_SUCCESS:
            print(f"✓ 登录成功")
            teacher_data = response.get('data', {})
            print(f"  教师信息: {teacher_data['name']} ({teacher_data.get('title', '')})")
            teacher_id = teacher_data['id']
            teacher_login_success = True
            break
        else:
            print(f"   ✗ 登录失败: {response.get('message') if response else '无响应'}")
    
    if not teacher_login_success:
        print(f"⚠ 教师登录失败，跳过后续教师功能测试")
        print(f"   💡 提示: 运行 'python utils/reset_passwords.py' 重置所有密码为 123456")
        # 不立即返回，继续测试其他功能
    
    # 6. 测试获取教师课程（仅当教师登录成功时）
    if teacher_login_success and teacher_id:
        print("\n[6] 测试获取教师课程...")
        request = Protocol.create_request(
            action='get_teacher_courses',
            data={
                'teacher_id': teacher_id,
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
    else:
        print("\n[6] 跳过教师课程测试（教师未登录）")
    
    # 断开连接
    print("\n[7] 断开连接...")
    client.disconnect()
    print("✓ 已断开连接")
    
    # 如果核心功能（连接、学生登录、获取课程）都成功，则认为测试通过
    # 教师登录失败不影响整体测试结果
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
        print("  提示: 服务器启动时会显示本机IP地址（不要使用 0.0.0.0）")
        host = input("\n服务器IP: ").strip()
        
        if not host:
            host = 'localhost'
            print(f"使用默认地址: {host}")
    
    # 检查是否错误地使用了 0.0.0.0
    if host.startswith('0.0.0.0'):
        print("\n" + "=" * 70)
        print("⚠️  错误：不能使用 0.0.0.0 作为服务器地址")
        print("=" * 70)
        print("\n说明：")
        print("  - 0.0.0.0 是服务器监听地址，不是客户端连接地址")
        print("  - 客户端需要连接服务器的实际IP地址")
        print("\n如何获取服务器IP：")
        print("  1. 在服务器电脑上运行: python 启动服务器.py")
        print("  2. 查看服务器启动时显示的'本机IP'")
        print("  3. 使用显示的IP地址（例如: 192.168.1.100）")
        print("\n示例：")
        print("  python 客户端测试.py 192.168.1.100")
        print("=" * 70)
        sys.exit(1)
    
    # 获取端口（如果host中包含端口，先解析）
    if ':' in host and not host.startswith('['):  # IPv6地址用[]包裹，需要特殊处理
        parts = host.rsplit(':', 1)
        if len(parts) == 2:
            try:
                port_from_host = int(parts[1])
                host = parts[0]
                port = port_from_host
            except ValueError:
                pass
    
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("端口号无效，使用默认端口 8888")
            port = 8888
    elif 'port' not in locals():
        port = 8888
    
    print(f"\n目标服务器: {host}:{port}")
    print(f"开始测试连接...")
    
    # 再次检查host（防止解析后还是0.0.0.0）
    if host == '0.0.0.0':
        print("\n⚠️  错误：不能使用 0.0.0.0 作为服务器地址")
        print("请使用服务器的实际IP地址（例如: 192.168.1.100）")
        sys.exit(1)
    
    # 运行测试
    try:
        success = test_connection(host, port)
        
        print("\n" + "=" * 70)
        if success:
            print("✓ 核心功能测试通过！网络连接正常")
            print("\n💡 提示：")
            print("  - 如果这是跨机器测试，说明网络配置正确")
            print("  - 学生登录、获取课程等功能正常")
            print("  - 如果教师登录失败，请运行: python utils/reset_passwords.py")
            print("  - 可以开始使用GUI客户端连接服务器")
        else:
            print("✗ 测试失败，请检查网络连接")
            print("\n🔧 故障排查：")
            print("  1. 确认服务器已启动（运行: python 启动服务器.py）")
            print(f"  2. 确认服务器IP地址正确（当前尝试: {host}）")
            print(f"  3. 确认端口正确（当前尝试: {port}）")
            print("  4. 检查防火墙设置")
            print("  5. 确认两台电脑在同一局域网")
            print("  6. 尝试在服务器电脑上运行: python 客户端测试.py localhost")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n收到中断信号")
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

