"""
权限管理模块
负责权限验证和角色管理
"""

import json
from pathlib import Path
from typing import List, Dict
from utils.logger import Logger


class PermissionManager:
    """权限管理类"""
    
    _permissions_config = None
    
    @classmethod
    def load_permissions(cls, config_file: str = 'config/permissions.json'):
        """
        加载权限配置
        
        Args:
            config_file: 权限配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                cls._permissions_config = json.load(f)
            Logger.info("权限配置加载成功")
        except Exception as e:
            Logger.error(f"权限配置加载失败: {e}")
            # 使用默认配置
            cls._permissions_config = {
                'roles': {
                    'admin': {
                        'name': '管理员',
                        'permissions': ['view_data', 'add_data', 'edit_data', 
                                       'delete_data', 'manage_users', 'view_logs']
                    },
                    'user': {
                        'name': '普通用户',
                        'permissions': ['view_data']
                    }
                }
            }
    
    @classmethod
    def _ensure_loaded(cls):
        """确保权限配置已加载"""
        if cls._permissions_config is None:
            cls.load_permissions()
    
    @classmethod
    def check_permission(cls, user, permission: str) -> bool:
        """
        检查用户是否有某个权限
        
        Args:
            user: User对象
            permission: 权限名称
        
        Returns:
            bool: 是否有权限
        """
        cls._ensure_loaded()
        
        if user is None:
            return False
        
        role = user.get_role()
        role_config = cls._permissions_config.get('roles', {}).get(role, {})
        permissions = role_config.get('permissions', [])
        
        return permission in permissions
    
    @classmethod
    def get_role_permissions(cls, role: str) -> List[str]:
        """
        获取角色的所有权限
        
        Args:
            role: 角色名称
        
        Returns:
            list: 权限列表
        """
        cls._ensure_loaded()
        
        role_config = cls._permissions_config.get('roles', {}).get(role, {})
        return role_config.get('permissions', [])
    
    @classmethod
    def get_all_roles(cls) -> Dict:
        """
        获取所有角色
        
        Returns:
            dict: 角色配置
        """
        cls._ensure_loaded()
        return cls._permissions_config.get('roles', {})
    
    @classmethod
    def get_permission_description(cls, permission: str) -> str:
        """
        获取权限描述
        
        Args:
            permission: 权限名称
        
        Returns:
            str: 权限描述
        """
        cls._ensure_loaded()
        descriptions = cls._permissions_config.get('permission_descriptions', {})
        return descriptions.get(permission, permission)


def require_permission(permission: str):
    """
    权限装饰器：要求特定权限才能执行函数
    
    Args:
        permission: 所需权限
    
    Example:
        @require_permission('delete_data')
        def delete_record(user, record_id):
            # 删除记录的代码
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 假设第一个参数是user对象
            user = args[0] if args else None
            
            if not PermissionManager.check_permission(user, permission):
                Logger.warning(f"权限不足: 用户 {user.username if user else 'None'} 尝试执行需要 {permission} 权限的操作")
                raise PermissionError(f"权限不足，需要 {permission} 权限")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 使用示例
if __name__ == "__main__":
    from core.user_manager import User
    
    # 加载权限配置
    PermissionManager.load_permissions()
    
    # 创建测试用户
    admin_user = User(1, 'admin', 'admin')
    normal_user = User(2, 'user', 'user')
    
    # 测试权限检查
    print(f"管理员删除数据权限: {PermissionManager.check_permission(admin_user, 'delete_data')}")
    print(f"普通用户删除数据权限: {PermissionManager.check_permission(normal_user, 'delete_data')}")
    print(f"普通用户查看数据权限: {PermissionManager.check_permission(normal_user, 'view_data')}")
    
    # 获取角色权限
    print(f"\n管理员权限列表: {PermissionManager.get_role_permissions('admin')}")
    print(f"普通用户权限列表: {PermissionManager.get_role_permissions('user')}")

