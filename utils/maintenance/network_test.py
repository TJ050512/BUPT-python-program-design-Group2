"""
网络连接诊断工具
用于测试服务器和客户端之间的网络连接

用法:
    python3 utils/network_test.py [server_ip] [port]
"""

import sys
import socket
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_network_connection(host: str, port: int = 8888):
    """测试网络连接"""
    print("=" * 70)
    print("网络连接诊断工具")
    print("=" * 70)
    print(f"\n目标服务器: {host}:{port}\n")
    
    # 1. 测试DNS解析（如果不是IP地址）
    print("[1] 测试DNS解析...")
    try:
        if host not in ['localhost', '127.0.0.1']:
            ip = socket.gethostbyname(host)
            print(f"✓ DNS解析成功: {host} -> {ip}")
        else:
            print(f"✓ 使用本地地址: {host}")
    except socket.gaierror as e:
        print(f"✗ DNS解析失败: {e}")
        return False
    
    # 2. 测试端口可达性
    print(f"\n[2] 测试端口 {port} 可达性...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        result = test_socket.connect_ex((host, port))
        test_socket.close()
        
        if result == 0:
            print(f"✓ 端口 {port} 可达")
        else:
            print(f"✗ 端口 {port} 不可达 (错误码: {result})")
            print("\n可能的原因：")
            print("  1. 服务器未启动")
            print("  2. 防火墙阻止连接")
            print("  3. 端口被占用")
            print("  4. 网络不通")
            return False
    except Exception as e:
        print(f"✗ 端口测试失败: {e}")
        return False
    
    # 3. 测试TCP连接
    print(f"\n[3] 测试TCP连接...")
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.settimeout(5)
        test_socket.connect((host, port))
        print(f"✓ TCP连接成功")
        
        # 尝试发送一个字节
        try:
            test_socket.send(b'\x00')
            print(f"✓ 数据发送成功")
        except Exception as e:
            print(f"⚠ 数据发送失败: {e}")
        
        test_socket.close()
        print(f"✓ 连接已关闭")
        
    except socket.timeout:
        print(f"✗ 连接超时")
        return False
    except Exception as e:
        print(f"✗ TCP连接失败: {e}")
        return False
    
    # 4. 测试应用层协议
    print(f"\n[4] 测试应用层协议...")
    try:
        from network.client import Client
        client = Client(host=host, port=port, timeout=5)
        success, msg = client.connect()
        if success:
            print(f"✓ 应用层连接成功: {msg}")
            client.disconnect()
            return True
        else:
            print(f"✗ 应用层连接失败: {msg}")
            return False
    except Exception as e:
        print(f"✗ 应用层测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    host = 'localhost'
    port = 8888
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print("端口号无效，使用默认端口 8888")
    
    success = test_network_connection(host, port)
    
    print("\n" + "=" * 70)
    if success:
        print("✓ 所有网络测试通过！")
        print("\n💡 提示：")
        print("  - 网络连接正常，可以开始使用客户端")
        print("  - 如果这是跨机器测试，说明配置正确")
    else:
        print("✗ 网络测试失败")
        print("\n🔧 排查建议：")
        print("  1. 确认服务器已启动: python 启动服务器.py")
        print(f"  2. 确认服务器IP: {host}")
        print(f"  3. 确认端口: {port}")
        print("  4. 检查防火墙设置")
        print("  5. 确认网络连通性: ping " + host)
    print("=" * 70)


if __name__ == "__main__":
    main()

