"""
用户管理模块 - 北京邮电大学教学管理系统
负责用户认证、注册、会话管理
支持学生和教师两种用户类型
"""

from typing import Optional, Dict
from datetime import datetime
from utils.logger import Logger
from utils.crypto import CryptoUtil
from utils.validator import Validator


class User:
    """用户类（学生或教师）"""
    
    def __init__(self, user_id: str, username: str, user_type: str, name: str = None, email: str = None, **kwargs):
        """
        初始化用户对象
        
        Args:
            user_id: 用户ID（学号或工号）
            username: 用户名（学号或工号）
            user_type: 用户类型（student/teacher）
            name: 真实姓名
            email: 邮箱
            **kwargs: 其他扩展信息（专业、职称等）
        """
        self.id = user_id
        self.username = username
        self.user_type = user_type  # student 或 teacher
        self.name = name
        self.email = email
        self.login_time = datetime.now()
        
        # 存储扩展信息
        self.extra_info = kwargs
    
    def has_permission(self, permission: str) -> bool:
        """
        检查用户是否有某个权限
        
        Args:
            permission: 权限名称
        
        Returns:
            bool: 是否有权限
        """
        from .permission_manager import PermissionManager
        return PermissionManager.check_permission(self, permission)
    
    def get_role(self) -> str:
        """获取用户角色（兼容旧代码）"""
        # teacher -> admin, student -> user
        return 'admin' if self.user_type == 'teacher' else 'user'
    
    def is_teacher(self) -> bool:
        """是否是教师"""
        return self.user_type == 'teacher'
    
    def is_student(self) -> bool:
        """是否是学生"""
        return self.user_type == 'student'
    
    def is_admin(self) -> bool:
        """是否是管理员（教师）"""
        return self.user_type == 'teacher'
    
    def to_dict(self) -> Dict:
        """
        转换为字典
        
        Returns:
            dict: 用户信息字典
        """
        data = {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'name': self.name,
            'email': self.email,
            'login_time': self.login_time.strftime('%Y-%m-%d %H:%M:%S'),
            'role': self.get_role()  # 兼容旧代码
        }
        data.update(self.extra_info)
        return data
    
    def __repr__(self):
        return f"User(id={self.id}, name='{self.name}', type='{self.user_type}')"


class UserManager:
    """用户管理类 - 支持学生和教师登录"""
    
    def __init__(self, db):
        """
        初始化用户管理器
        
        Args:
            db: 数据库实例
        """
        self.db = db
        self.current_user: Optional[User] = None
        Logger.info("用户管理器初始化完成")
    
    def login(self, username: str, password: str) -> tuple[bool, Optional[User], str]:
        """
        用户登录（支持学生和教师）
        
        Args:
            username: 用户名（学号或工号）
            password: 密码
        
        Returns:
            tuple: (是否成功, User对象, 消息)
        """
        try:
            # 验证输入
            if not username or not password:
                return False, None, "用户名和密码不能为空"
            
            Logger.info(f"尝试登录: {username}")
            
            # 判断是学生还是教师（根据ID格式）
            # 学生：10位数字，教师：teacher开头
            is_teacher = username.startswith('teacher') or not username.isdigit()
            
            # 查询用户
            if is_teacher:
                sql = "SELECT * FROM teachers WHERE teacher_id=?"
                result = self.db.execute_query(sql, (username,))
                user_type = 'teacher'
            else:
                sql = "SELECT * FROM students WHERE student_id=?"
                result = self.db.execute_query(sql, (username,))
                user_type = 'student'
            
            if not result:
                Logger.warning(f"用户不存在: {username}")
                return False, None, "用户名或密码错误"
            
            user_data = result[0]
            
            # 验证密码
            if not CryptoUtil.verify_password(password, user_data['password']):
                Logger.warning(f"密码错误: {username}")
                return False, None, "用户名或密码错误"
            
            # 创建User对象
            user_id = user_data.get('teacher_id') if is_teacher else user_data.get('student_id')
            
            extra_info = {}
            if is_teacher:
                extra_info = {
                    'title': user_data.get('title'),
                    'department': user_data.get('department')
                }
            else:
                extra_info = {
                    'major': user_data.get('major'),
                    'grade': user_data.get('grade'),
                    'class_name': user_data.get('class_name')
                }
            
            user = User(
                user_id=user_id,
                username=user_id,
                user_type=user_type,
                name=user_data.get('name'),
                email=user_data.get('email'),
                **extra_info
            )
            
            # 设置当前用户
            self.current_user = user
            
            user_type_cn = "教师" if is_teacher else "学生"
            Logger.info(f"{user_type_cn}登录成功: {user.name} ({username})")
            return True, user, "登录成功"
            
        except Exception as e:
            Logger.error(f"登录过程出错: {e}", exc_info=True)
            return False, None, "登录失败，请稍后重试"
    
    def logout(self):
        """用户注销"""
        if self.current_user:
            Logger.info(f"用户注销: {self.current_user.username}")
            self.current_user = None
    
    def register(self, username: str, password: str, email: str = None) -> tuple[bool, str]:
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
        
        Returns:
            tuple: (是否成功, 消息)
        """
        try:
            # 验证用户名
            if not Validator.is_valid_username(username):
                return False, "用户名格式不正确（3-20个字符，只能包含字母、数字、下划线）"
            
            # 验证密码
            is_valid, error_msg = Validator.is_valid_password(password)
            if not is_valid:
                return False, error_msg
            
            # 验证邮箱（如果提供）
            if email and not Validator.is_valid_email(email):
                return False, "邮箱格式不正确"
            
            # 检查用户名是否已存在
            if self.db.query_user_by_username(username):
                return False, "用户名已存在"
            
            # 哈希密码
            password_hash = CryptoUtil.hash_password(password)
            
            # 插入数据库
            user_data = {
                'username': username,
                'password': password_hash,
                'role': 'user',  # 默认为普通用户
                'email': email
            }
            
            user_id = self.db.insert_user(user_data)
            
            Logger.info(f"新用户注册: {username} (ID: {user_id})")
            return True, "注册成功"
            
        except Exception as e:
            Logger.error(f"注册过程出错: {e}", exc_info=True)
            return False, "注册失败，请稍后重试"
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            tuple: (是否成功, 消息)
        """
        try:
            # 验证新密码
            is_valid, error_msg = Validator.is_valid_password(new_password)
            if not is_valid:
                return False, error_msg
            
            # 获取用户信息
            user_data = self.db.query_user_by_id(user_id)
            if not user_data:
                return False, "用户不存在"
            
            # 验证旧密码
            if not CryptoUtil.verify_password(old_password, user_data['password']):
                return False, "旧密码错误"
            
            # 哈希新密码
            new_password_hash = CryptoUtil.hash_password(new_password)
            
            # 更新数据库
            self.db.update_user_password(user_id, new_password_hash)
            
            Logger.info(f"用户修改密码: {user_data['username']}")
            return True, "密码修改成功"
            
        except Exception as e:
            Logger.error(f"修改密码出错: {e}", exc_info=True)
            return False, "修改密码失败"
    
    def get_current_user(self) -> Optional[User]:
        """获取当前登录用户"""
        return self.current_user
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 用户信息（不包含密码）
        """
        try:
            user_data = self.db.query_user_by_id(user_id)
            if user_data:
                # 移除密码字段
                user_data.pop('password', None)
                return user_data
            return None
        except Exception as e:
            Logger.error(f"获取用户信息出错: {e}")
            return None


# 使用示例（需要数据库接口支持）
if __name__ == "__main__":
    # 这里需要一个模拟的数据库接口
    class MockDB:
        def query_user_by_username(self, username):
            if username == "admin":
                return {
                    'id': 1,
                    'username': 'admin',
                    'password': CryptoUtil.hash_password('admin123'),
                    'role': 'admin',
                    'email': 'admin@example.com'
                }
            return None
        
        def update_last_login(self, user_id):
            pass
    
    # 测试
    db = MockDB()
    user_manager = UserManager(db)
    
    success, user, msg = user_manager.login("admin", "admin123")
    print(f"登录结果: {success}, 消息: {msg}")
    if user:
        print(f"用户信息: {user}")

