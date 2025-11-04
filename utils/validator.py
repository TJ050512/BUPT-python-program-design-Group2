"""
数据验证模块
提供各种数据验证功能
"""

import re
from typing import Any, Optional


class Validator:
    """数据验证类"""
    
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """
        验证用户名是否合法
        规则：3-20个字符，只能包含字母、数字、下划线
        
        Args:
            username: 用户名
        
        Returns:
            bool: 是否合法
        """
        if not username or not isinstance(username, str):
            return False
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def is_valid_password(password: str) -> tuple[bool, str]:
        """
        验证密码强度
        规则：至少6个字符
        
        Args:
            password: 密码
        
        Returns:
            tuple: (是否合法, 错误信息)
        """
        if not password or not isinstance(password, str):
            return False, "密码不能为空"
        
        if len(password) < 6:
            return False, "密码至少需要6个字符"
        
        # 可以添加更强的密码规则
        # if not re.search(r'[A-Z]', password):
        #     return False, "密码必须包含至少一个大写字母"
        # if not re.search(r'[a-z]', password):
        #     return False, "密码必须包含至少一个小写字母"
        # if not re.search(r'[0-9]', password):
        #     return False, "密码必须包含至少一个数字"
        
        return True, ""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
        
        Returns:
            bool: 是否合法
        """
        if not email or not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_not_empty(value: Any) -> bool:
        """
        检查值是否非空
        
        Args:
            value: 要检查的值
        
        Returns:
            bool: 是否非空
        """
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (list, dict, tuple)):
            return len(value) > 0
        return True
    
    @staticmethod
    def is_in_range(value: float, min_val: float, max_val: float) -> bool:
        """
        检查数值是否在范围内
        
        Args:
            value: 数值
            min_val: 最小值
            max_val: 最大值
        
        Returns:
            bool: 是否在范围内
        """
        try:
            value = float(value)
            return min_val <= value <= max_val
        except (ValueError, TypeError):
            return False


# 使用示例
if __name__ == "__main__":
    # 用户名验证
    print("用户名验证:")
    print(f"'admin': {Validator.is_valid_username('admin')}")
    print(f"'ab': {Validator.is_valid_username('ab')}")  # 太短
    print(f"'user@123': {Validator.is_valid_username('user@123')}")  # 非法字符
    
    # 密码验证
    print("\n密码验证:")
    print(f"'123456': {Validator.is_valid_password('123456')}")
    print(f"'12345': {Validator.is_valid_password('12345')}")  # 太短
    
    # 邮箱验证
    print("\n邮箱验证:")
    print(f"'test@example.com': {Validator.is_valid_email('test@example.com')}")
    print(f"'invalid-email': {Validator.is_valid_email('invalid-email')}")

