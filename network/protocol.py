"""
网络通信协议模块
定义客户端-服务器通信协议
"""

import json
from datetime import datetime
from typing import Dict, Any
from utils.logger import Logger


class Protocol:
    """通信协议类"""
    
    # 消息类型
    TYPE_REQUEST = "request"
    TYPE_RESPONSE = "response"
    
    # 操作类型
    ACTION_LOGIN = "login"
    ACTION_LOGOUT = "logout"
    ACTION_QUERY = "query"
    ACTION_INSERT = "insert"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_START_CRAWL = "start_crawl"
    ACTION_GET_CRAWL_STATUS = "get_crawl_status"
    
    # 状态码
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_UNAUTHORIZED = "unauthorized"
    
    @staticmethod
    def encode(data: Dict) -> bytes:
        """
        编码消息为字节流
        
        Args:
            data: 消息字典
        
        Returns:
            bytes: 编码后的字节流
        """
        try:
            # 转换为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False)
            # 转换为字节流
            bytes_data = json_str.encode('utf-8')
            # 添加长度前缀（4字节，大端序）
            length = len(bytes_data)
            length_prefix = length.to_bytes(4, byteorder='big')
            
            return length_prefix + bytes_data
        except Exception as e:
            Logger.error(f"消息编码失败: {e}")
            raise
    
    @staticmethod
    def decode(bytes_data: bytes) -> Dict:
        """
        解码字节流为消息字典
        
        Args:
            bytes_data: 字节流（包含长度前缀）
        
        Returns:
            dict: 消息字典
        """
        try:
            # 读取长度前缀（前4字节）
            if len(bytes_data) < 4:
                raise ValueError("数据长度不足")
            
            length = int.from_bytes(bytes_data[:4], byteorder='big')
            
            # 读取消息体
            if len(bytes_data) < 4 + length:
                raise ValueError(f"数据不完整，期望{length}字节，实际{len(bytes_data)-4}字节")
            
            json_bytes = bytes_data[4:4+length]
            json_str = json_bytes.decode('utf-8')
            
            # 解析JSON
            data = json.loads(json_str)
            return data
        except Exception as e:
            Logger.error(f"消息解码失败: {e}")
            raise
    
    @staticmethod
    def create_request(action: str, data: Dict = None, user_id: int = None) -> Dict:
        """
        创建请求消息
        
        Args:
            action: 操作类型
            data: 请求数据
            user_id: 用户ID
        
        Returns:
            dict: 请求消息字典
        """
        request = {
            'type': Protocol.TYPE_REQUEST,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        if user_id is not None:
            request['user_id'] = user_id
        
        return request
    
    @staticmethod
    def create_response(status: str, data: Any = None, message: str = "") -> Dict:
        """
        创建响应消息
        
        Args:
            status: 状态（success/error/unauthorized）
            data: 响应数据
            message: 消息说明
        
        Returns:
            dict: 响应消息字典
        """
        response = {
            'type': Protocol.TYPE_RESPONSE,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if data is not None:
            response['data'] = data
        
        return response
    
    @staticmethod
    def is_valid_request(data: Dict) -> bool:
        """
        验证请求消息是否合法
        
        Args:
            data: 消息字典
        
        Returns:
            bool: 是否合法
        """
        if not isinstance(data, dict):
            return False
        
        if data.get('type') != Protocol.TYPE_REQUEST:
            return False
        
        if 'action' not in data:
            return False
        
        if 'timestamp' not in data:
            return False
        
        return True
    
    @staticmethod
    def is_valid_response(data: Dict) -> bool:
        """
        验证响应消息是否合法
        
        Args:
            data: 消息字典
        
        Returns:
            bool: 是否合法
        """
        if not isinstance(data, dict):
            return False
        
        if data.get('type') != Protocol.TYPE_RESPONSE:
            return False
        
        if 'status' not in data:
            return False
        
        if 'timestamp' not in data:
            return False
        
        return True


# 使用示例
if __name__ == "__main__":
    # 创建请求
    request = Protocol.create_request(
        action=Protocol.ACTION_LOGIN,
        data={'username': 'admin', 'password': 'admin123'}
    )
    print("请求消息:")
    print(json.dumps(request, indent=2, ensure_ascii=False))
    
    # 编码
    encoded = Protocol.encode(request)
    print(f"\n编码后长度: {len(encoded)} 字节")
    
    # 解码
    decoded = Protocol.decode(encoded)
    print("\n解码后消息:")
    print(json.dumps(decoded, indent=2, ensure_ascii=False))
    
    # 创建响应
    response = Protocol.create_response(
        status=Protocol.STATUS_SUCCESS,
        data={'user_id': 1, 'username': 'admin', 'role': 'admin'},
        message="登录成功"
    )
    print("\n响应消息:")
    print(json.dumps(response, indent=2, ensure_ascii=False))
    
    # 验证
    print(f"\n请求验证: {Protocol.is_valid_request(request)}")
    print(f"响应验证: {Protocol.is_valid_response(response)}")

