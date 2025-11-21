"""
网络数据库适配器
将网络客户端包装成数据库接口，供登录窗口使用
"""

from typing import Optional, List, Dict, Any, Tuple
from utils.logger import Logger
from network.client import Client
from network.protocol import Protocol


class NetworkDatabaseAdapter:
    """
    网络数据库适配器
    将网络客户端的调用转换为数据库接口
    """
    
    def __init__(self, client: Client):
        """
        初始化适配器
        
        Args:
            client: 网络客户端实例
        """
        self.client = client
        Logger.info("网络数据库适配器初始化完成")
    
    def init_demo_data(self):
        """初始化演示数据（网络模式下由服务器负责）"""
        pass
    
    def execute_query(self, sql: str, params: tuple = None) -> List[Dict]:
        """
        执行SQL查询
        
        Args:
            sql: SQL语句
            params: 参数元组
        
        Returns:
            list: 查询结果列表
        """
        try:
            # 创建查询请求
            request = Protocol.create_request(
                action="execute_query",
                data={
                    'sql': sql,
                    'params': params or ()
                }
            )
            
            # 发送请求
            response = self.client.send_request(request)
            
            if not response:
                Logger.error("查询请求失败：未收到响应")
                return []
            
            if response.get('status') == Protocol.STATUS_SUCCESS:
                return response.get('data', [])
            else:
                Logger.error(f"查询失败: {response.get('message')}")
                return []
        
        except Exception as e:
            Logger.error(f"查询异常: {e}", exc_info=True)
            return []
    
    def execute_update(self, sql: str, params: tuple = None) -> int:
        """
        执行SQL更新
        
        Args:
            sql: SQL语句
            params: 参数元组
        
        Returns:
            int: 影响的行数
        """
        try:
            # 创建更新请求
            request = Protocol.create_request(
                action="execute_update",
                data={
                    'sql': sql,
                    'params': params or ()
                }
            )
            
            # 发送请求
            response = self.client.send_request(request)
            
            if not response:
                Logger.error("更新请求失败：未收到响应")
                return 0
            
            if response.get('status') == Protocol.STATUS_SUCCESS:
                return response.get('data', {}).get('affected_rows', 0)
            else:
                Logger.error(f"更新失败: {response.get('message')}")
                return 0
        
        except Exception as e:
            Logger.error(f"更新异常: {e}", exc_info=True)
            return 0
    
    def get_student_by_id(self, student_id: str) -> Optional[Dict]:
        """
        根据学号获取学生信息
        
        Args:
            student_id: 学号
        
        Returns:
            dict: 学生信息，不存在返回None
        """
        sql = "SELECT * FROM students WHERE student_id = ?"
        results = self.execute_query(sql, (student_id,))
        return results[0] if results else None
    
    def get_teacher_by_id(self, teacher_id: str) -> Optional[Dict]:
        """
        根据工号获取教师信息
        
        Args:
            teacher_id: 工号
        
        Returns:
            dict: 教师信息，不存在返回None
        """
        sql = "SELECT * FROM teachers WHERE teacher_id = ?"
        results = self.execute_query(sql, (teacher_id,))
        return results[0] if results else None
    
    def get_admin_by_id(self, admin_id: str) -> Optional[Dict]:
        """
        根据ID获取管理员信息
        
        Args:
            admin_id: 管理员ID
        
        Returns:
            dict: 管理员信息，不存在返回None
        """
        sql = "SELECT * FROM admins WHERE admin_id = ?"
        results = self.execute_query(sql, (admin_id,))
        return results[0] if results else None
    
    def update_student_password(self, student_id: str, password_hash: str) -> bool:
        """
        更新学生密码
        
        Args:
            student_id: 学号
            password_hash: 密码哈希
        
        Returns:
            bool: 是否成功
        """
        sql = "UPDATE students SET password_hash = ? WHERE student_id = ?"
        affected = self.execute_update(sql, (password_hash, student_id))
        return affected > 0
    
    def update_teacher_password(self, teacher_id: str, password_hash: str) -> bool:
        """
        更新教师密码
        
        Args:
            teacher_id: 工号
            password_hash: 密码哈希
        
        Returns:
            bool: 是否成功
        """
        sql = "UPDATE teachers SET password_hash = ? WHERE teacher_id = ?"
        affected = self.execute_update(sql, (password_hash, teacher_id))
        return affected > 0
    
    def update_admin_password(self, admin_id: str, password_hash: str) -> bool:
        """
        更新管理员密码
        
        Args:
            admin_id: 管理员ID
            password_hash: 密码哈希
        
        Returns:
            bool: 是否成功
        """
        sql = "UPDATE admins SET password_hash = ? WHERE admin_id = ?"
        affected = self.execute_update(sql, (password_hash, admin_id))
        return affected > 0
    
    def get_courses(self, filters: Dict = None) -> List[Dict]:
        """
        获取课程列表
        
        Args:
            filters: 过滤条件
        
        Returns:
            list: 课程列表
        """
        sql = "SELECT * FROM courses"
        where_clauses = []
        params = []
        
        if filters:
            if 'course_id' in filters:
                where_clauses.append("course_id = ?")
                params.append(filters['course_id'])
            if 'course_name' in filters:
                where_clauses.append("course_name LIKE ?")
                params.append(f"%{filters['course_name']}%")
            if 'teacher_id' in filters:
                where_clauses.append("teacher_id = ?")
                params.append(filters['teacher_id'])
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        return self.execute_query(sql, tuple(params))
    
    def get_enrollments(self, student_id: str = None, course_id: str = None) -> List[Dict]:
        """
        获取选课记录
        
        Args:
            student_id: 学号（可选）
            course_id: 课程ID（可选）
        
        Returns:
            list: 选课记录列表
        """
        sql = "SELECT * FROM enrollments"
        where_clauses = []
        params = []
        
        if student_id:
            where_clauses.append("student_id = ?")
            params.append(student_id)
        
        if course_id:
            where_clauses.append("course_id = ?")
            params.append(course_id)
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        return self.execute_query(sql, tuple(params))
    
    def get_grades(self, student_id: str = None, course_id: str = None) -> List[Dict]:
        """
        获取成绩记录
        
        Args:
            student_id: 学号（可选）
            course_id: 课程ID（可选）
        
        Returns:
            list: 成绩记录列表
        """
        sql = """
            SELECT e.*, c.course_name, c.credits, t.name as teacher_name
            FROM enrollments e
            LEFT JOIN courses c ON e.course_id = c.course_id
            LEFT JOIN teachers t ON c.teacher_id = t.teacher_id
        """
        where_clauses = []
        params = []
        
        if student_id:
            where_clauses.append("e.student_id = ?")
            params.append(student_id)
        
        if course_id:
            where_clauses.append("e.course_id = ?")
            params.append(course_id)
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)
        
        return self.execute_query(sql, tuple(params))
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.disconnect()
            Logger.info("网络客户端连接已关闭")


if __name__ == "__main__":
    # 测试适配器
    from network.client import Client
    
    # 创建客户端
    client = Client(host='localhost', port=8888)
    
    # 连接服务器
    success, msg = client.connect()
    if not success:
        print(f"连接失败: {msg}")
        exit(1)
    
    print(f"连接成功: {msg}")
    
    # 创建适配器
    adapter = NetworkDatabaseAdapter(client)
    
    # 测试查询
    print("\n测试查询学生信息...")
    student = adapter.get_student_by_id('2024210001')
    if student:
        print(f"学生信息: {student}")
    else:
        print("未找到学生")
    
    # 关闭连接
    adapter.close()

