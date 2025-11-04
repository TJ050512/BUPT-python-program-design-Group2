"""
加密工具模块
提供密码哈希、数据加密等功能
"""

import hashlib
import bcrypt
from typing import Union


class CryptoUtil:
    """加密工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        使用bcrypt哈希密码
        
        Args:
            password: 明文密码
        
        Returns:
            str: 哈希后的密码
        """
        # 生成salt并哈希
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed: 哈希后的密码
        
        Returns:
            bool: 密码是否匹配
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception:
            return False
    
    @staticmethod
    def sha256(data: Union[str, bytes]) -> str:
        """
        SHA256哈希（用于非密码的数据哈希）
        
        Args:
            data: 要哈希的数据
        
        Returns:
            str: 哈希值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def md5(data: Union[str, bytes]) -> str:
        """
        MD5哈希（不推荐用于安全场景）
        
        Args:
            data: 要哈希的数据
        
        Returns:
            str: 哈希值（十六进制）
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.md5(data).hexdigest()


# 使用示例
if __name__ == "__main__":
    # 密码哈希示例
    password = "my_secure_password"
    hashed = CryptoUtil.hash_password(password)
    print(f"原始密码: {password}")
    print(f"哈希密码: {hashed}")
    print(f"验证结果: {CryptoUtil.verify_password(password, hashed)}")
    print(f"错误密码: {CryptoUtil.verify_password('wrong_password', hashed)}")
    
    # SHA256示例
    data = "Hello, World!"
    print(f"\nSHA256: {CryptoUtil.sha256(data)}")

