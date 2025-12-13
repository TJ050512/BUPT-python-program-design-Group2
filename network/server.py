"""
服务器端模块
实现多客户端并发的服务器
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import socket
import threading
import asyncio
from typing import Dict, Optional, Callable
from utils.logger import Logger
from network.protocol import Protocol


class Server:
    """服务器类"""
    
    def __init__(self, host: str = 'localhost', port: int = 8888, max_connections: int = 10):
        """
        初始化服务器
        
        Args:
            host: 服务器地址
            port: 端口号
            max_connections: 最大连接数
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        
        self.server_socket: Optional[socket.socket] = None
        self.is_running = False
        self.clients: Dict[str, socket.socket] = {}  # {client_id: socket}
        self.client_lock = threading.Lock()
        
        # 消息处理器（由业务层注册）
        self.message_handlers: Dict[str, Callable] = {}
        
        Logger.info(f"服务器初始化: {host}:{port}")
    
    def register_handler(self, action: str, handler: Callable):
        """
        注册消息处理器
        
        Args:
            action: 操作类型
            handler: 处理函数，签名为 handler(request_data) -> response_data
        """
        self.message_handlers[action] = handler
        Logger.info(f"注册消息处理器: {action}")
    
    def start(self):
        """启动服务器"""
        try:
            # 创建socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # 绑定地址和端口
            self.server_socket.bind((self.host, self.port))
            
            # 开始监听
            self.server_socket.listen(self.max_connections)
            self.is_running = True
            
            Logger.info(f"服务器启动成功，监听 {self.host}:{self.port}")
            
            # 接受客户端连接
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    Logger.info(f"新客户端连接: {client_address}")
                    
                    # 为每个客户端创建新线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.is_running:
                        Logger.error(f"接受连接失败: {e}")
        
        except Exception as e:
            Logger.error(f"服务器启动失败: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self):
        """停止服务器"""
        self.is_running = False
        
        # 关闭所有客户端连接
        with self.client_lock:
            for client_id, client_socket in self.clients.items():
                try:
                    client_socket.close()
                    Logger.info(f"关闭客户端连接: {client_id}")
                except Exception as e:
                    Logger.error(f"关闭客户端连接失败: {e}")
            self.clients.clear()
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
                Logger.info("服务器socket已关闭")
            except Exception as e:
                Logger.error(f"关闭服务器socket失败: {e}")
        
        Logger.info("服务器已停止")
    
    def handle_client(self, client_socket: socket.socket, client_address: tuple):
        """
        处理客户端连接
        
        Args:
            client_socket: 客户端socket
            client_address: 客户端地址
        """
        client_id = f"{client_address[0]}:{client_address[1]}"
        
        # 添加到客户端列表
        with self.client_lock:
            self.clients[client_id] = client_socket
        
        try:
            while self.is_running:
                # 接收消息长度（4字节）
                length_data = self._recv_exact(client_socket, 4)
                if not length_data:
                    break
                
                length = int.from_bytes(length_data, byteorder='big')
                
                # 接收消息体
                message_data = self._recv_exact(client_socket, length)
                if not message_data:
                    break
                
                # 解码消息
                full_data = length_data + message_data
                request = Protocol.decode(full_data)
                
                Logger.debug(f"收到来自 {client_id} 的请求: {request.get('action')}")
                
                # 处理请求
                response = self.process_request(request)
                
                # 发送响应
                response_bytes = Protocol.encode(response)
                client_socket.sendall(response_bytes)
                
        except Exception as e:
            Logger.error(f"处理客户端 {client_id} 时出错: {e}", exc_info=True)
        finally:
            # 移除客户端
            with self.client_lock:
                if client_id in self.clients:
                    del self.clients[client_id]
            
            try:
                client_socket.close()
            except Exception:
                pass
            
            Logger.info(f"客户端断开连接: {client_id}")
    
    def _recv_exact(self, sock: socket.socket, size: int) -> Optional[bytes]:
        """
        精确接收指定字节数的数据
        
        Args:
            sock: socket对象
            size: 要接收的字节数
        
        Returns:
            bytes: 接收到的数据
            None: 连接断开
        """
        data = b''
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data
    
    def process_request(self, request: Dict) -> Dict:
        """
        处理请求
        
        Args:
            request: 请求字典
        
        Returns:
            dict: 响应字典
        """
        try:
            # 验证请求
            if not Protocol.is_valid_request(request):
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message="无效的请求格式"
                )
            
            action = request.get('action')
            
            # 查找处理器
            handler = self.message_handlers.get(action)
            if handler is None:
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=f"未知的操作类型: {action}"
                )
            
            # 调用处理器
            try:
                result = handler(request)
                return result
            except Exception as e:
                Logger.error(f"处理器执行失败: {e}", exc_info=True)
                return Protocol.create_response(
                    status=Protocol.STATUS_ERROR,
                    message=f"处理失败: {str(e)}"
                )
        
        except Exception as e:
            Logger.error(f"处理请求失败: {e}", exc_info=True)
            return Protocol.create_response(
                status=Protocol.STATUS_ERROR,
                message="服务器内部错误"
            )
    
    def broadcast(self, message: Dict):
        """
        广播消息给所有客户端
        
        Args:
            message: 消息字典
        """
        message_bytes = Protocol.encode(message)
        
        with self.client_lock:
            for client_id, client_socket in self.clients.items():
                try:
                    client_socket.sendall(message_bytes)
                    Logger.debug(f"向 {client_id} 发送广播")
                except Exception as e:
                    Logger.error(f"向 {client_id} 发送广播失败: {e}")


# 使用示例
if __name__ == "__main__":
    # 创建服务器
    server = Server(host='localhost', port=8888)
    
    # 注册处理器
    def handle_login(request):
        """处理登录请求"""
        username = request.get('data', {}).get('username')
        password = request.get('data', {}).get('password')
        
        Logger.info(f"处理登录: {username}")
        
        # 简单验证（实际应调用用户管理器）
        if username == 'admin' and password == 'admin123':
            return Protocol.create_response(
                status=Protocol.STATUS_SUCCESS,
                data={'user_id': 1, 'username': 'admin', 'role': 'admin'},
                message="登录成功"
            )
        else:
            return Protocol.create_response(
                status=Protocol.STATUS_ERROR,
                message="用户名或密码错误"
            )
    
    server.register_handler(Protocol.ACTION_LOGIN, handle_login)
    
    # 启动服务器（在实际应用中应该在单独的线程中启动）
    try:
        server.start()
    except KeyboardInterrupt:
        Logger.info("收到中断信号，停止服务器")
        server.stop()

