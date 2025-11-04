"""
客户端模块
实现与服务器的通信
"""

import socket
import threading
from typing import Optional, Dict, Callable
from utils.logger import Logger
from .protocol import Protocol


class Client:
    """客户端类"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, timeout: int = 30):
        """
        初始化客户端
        
        Args:
            host: 服务器地址
            port: 端口号
            timeout: 连接超时（秒）
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        
        # 接收线程
        self.receive_thread: Optional[threading.Thread] = None
        
        # 消息回调（用于处理服务器主动推送的消息）
        self.message_callback: Optional[Callable] = None
        
        Logger.info(f"客户端初始化: {host}:{port}")
    
    def connect(self) -> tuple[bool, str]:
        """
        连接到服务器
        
        Returns:
            tuple: (是否成功, 消息)
        """
        try:
            # 创建socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            
            # 连接服务器
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            
            Logger.info(f"连接服务器成功: {self.host}:{self.port}")
            
            # 启动接收线程（如果需要接收服务器推送）
            # self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            # self.receive_thread.start()
            
            return True, "连接成功"
            
        except socket.timeout:
            Logger.error(f"连接服务器超时: {self.host}:{self.port}")
            return False, "连接超时"
        except Exception as e:
            Logger.error(f"连接服务器失败: {e}", exc_info=True)
            return False, f"连接失败: {str(e)}"
    
    def disconnect(self):
        """断开连接"""
        self.is_connected = False
        
        if self.socket:
            try:
                self.socket.close()
                Logger.info("已断开服务器连接")
            except Exception as e:
                Logger.error(f"断开连接失败: {e}")
            finally:
                self.socket = None
    
    def send_request(self, request: Dict) -> Optional[Dict]:
        """
        发送请求并接收响应
        
        Args:
            request: 请求字典
        
        Returns:
            dict: 响应字典
            None: 发送失败或超时
        """
        if not self.is_connected or self.socket is None:
            Logger.error("未连接到服务器")
            return None
        
        try:
            # 编码并发送请求
            request_bytes = Protocol.encode(request)
            self.socket.sendall(request_bytes)
            
            Logger.debug(f"发送请求: {request.get('action')}")
            
            # 接收响应长度（4字节）
            length_data = self._recv_exact(4)
            if not length_data:
                Logger.error("接收响应长度失败")
                return None
            
            length = int.from_bytes(length_data, byteorder='big')
            
            # 接收响应体
            response_data = self._recv_exact(length)
            if not response_data:
                Logger.error("接收响应数据失败")
                return None
            
            # 解码响应
            full_data = length_data + response_data
            response = Protocol.decode(full_data)
            
            Logger.debug(f"收到响应: {response.get('status')}")
            
            return response
            
        except socket.timeout:
            Logger.error("接收响应超时")
            return None
        except Exception as e:
            Logger.error(f"发送请求失败: {e}", exc_info=True)
            return None
    
    def _recv_exact(self, size: int) -> Optional[bytes]:
        """
        精确接收指定字节数的数据
        
        Args:
            size: 要接收的字节数
        
        Returns:
            bytes: 接收到的数据
            None: 连接断开或接收失败
        """
        if self.socket is None:
            return None
        
        data = b''
        while len(data) < size:
            try:
                chunk = self.socket.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            except Exception as e:
                Logger.error(f"接收数据失败: {e}")
                return None
        return data
    
    def _receive_loop(self):
        """接收循环（用于接收服务器主动推送的消息）"""
        while self.is_connected:
            try:
                # 接收消息长度
                length_data = self._recv_exact(4)
                if not length_data:
                    break
                
                length = int.from_bytes(length_data, byteorder='big')
                
                # 接收消息体
                message_data = self._recv_exact(length)
                if not message_data:
                    break
                
                # 解码消息
                full_data = length_data + message_data
                message = Protocol.decode(full_data)
                
                # 调用回调
                if self.message_callback:
                    self.message_callback(message)
                
            except Exception as e:
                if self.is_connected:
                    Logger.error(f"接收消息失败: {e}")
                break
        
        Logger.info("接收循环结束")
    
    def set_message_callback(self, callback: Callable):
        """
        设置消息回调函数
        
        Args:
            callback: 回调函数，签名为 callback(message: Dict)
        """
        self.message_callback = callback
    
    # ============ 便捷方法 ============
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        """
        登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            dict: 响应数据
        """
        request = Protocol.create_request(
            action=Protocol.ACTION_LOGIN,
            data={'username': username, 'password': password}
        )
        return self.send_request(request)
    
    def query_data(self, filters: Dict = None, limit: int = 100) -> Optional[Dict]:
        """
        查询数据
        
        Args:
            filters: 过滤条件
            limit: 返回记录数
        
        Returns:
            dict: 响应数据
        """
        request = Protocol.create_request(
            action=Protocol.ACTION_QUERY,
            data={'filters': filters, 'limit': limit}
        )
        return self.send_request(request)


# 使用示例
if __name__ == "__main__":
    # 创建客户端
    client = Client(host='localhost', port=8888)
    
    # 连接服务器
    success, msg = client.connect()
    if not success:
        print(f"连接失败: {msg}")
        exit(1)
    
    print(f"连接成功: {msg}")
    
    # 发送登录请求
    response = client.login('admin', 'admin123')
    if response:
        print(f"登录响应: {response}")
        
        if response.get('status') == Protocol.STATUS_SUCCESS:
            print("登录成功！")
            user_data = response.get('data', {})
            print(f"用户信息: {user_data}")
        else:
            print(f"登录失败: {response.get('message')}")
    else:
        print("发送登录请求失败")
    
    # 断开连接
    client.disconnect()

