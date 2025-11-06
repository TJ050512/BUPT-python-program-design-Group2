"""
数据库接口模块
提供统一的数据库访问接口，对接队友的数据库模块
"""
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

# 确保项目根在模块搜索路径中（当作为脚本直接运行时）
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import Logger
# 尝试从配置读取数据库路径
try:
    from utils.config_manager import Config  # type: ignore
except Exception:
    Config = None  # type: ignore

class _DBAdapter:
    """内部适配器：屏蔽不同数据库实现差异"""
    def __init__(self, db_path: str):
        self._impl = None
        # 优先尝试队友的 database_module.DatabaseManager
        try:
            from database_module import DatabaseManager  # type: ignore
            cfg = {'type': 'sqlite', 'path': str(db_path)}
            self._impl = DatabaseManager(cfg)
            self._mode = 'database_module'
            Logger.info("DatabaseInterface: 使用 database_module.DatabaseManager")
        except Exception:
            try:
                # 回退到项目内的 data.database
                from data.database import Database, get_database  # type: ignore
                # 尝试使用单例 get_database if provided
                try:
                    self._impl = get_database()  # type: ignore
                    self._mode = 'data.database.single'
                except Exception:
                    self._impl = Database(str(db_path))
                    self._mode = 'data.database'
                Logger.info("DatabaseInterface: 回退使用 data.database")
            except Exception as e:
                Logger.error("DatabaseInterface: 无法找到可用的数据库实现", exc_info=True)
                raise

    # 统一方法名：query 返回 list[dict], execute 返回受影响行数, insert 返回新 id 或 None
    def query(self, sql: str, params: Tuple = None) -> List[Dict]:
        if self._mode == 'database_module':
            if hasattr(self._impl, 'query'):
                return self._impl.query(sql, params)
            if hasattr(self._impl, 'execute'):
                return self._impl.execute(sql, params)
        else:
            # data.database: execute_query 返回 List[Dict]
            return self._impl.execute_query(sql, params)
        raise NotImplementedError("query 方法不可用")

    def execute(self, sql: str, params: Tuple = None) -> int:
        if self._mode == 'database_module':
            if hasattr(self._impl, 'execute'):
                return self._impl.execute(sql, params)
            if hasattr(self._impl, 'execute_update'):
                return self._impl.execute_update(sql, params)
        else:
            return self._impl.execute_update(sql, params)
        raise NotImplementedError("execute 方法不可用")

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        if self._mode == 'database_module':
            if hasattr(self._impl, 'insert'):
                return self._impl.insert(table, data)
            if hasattr(self._impl, 'insert_data'):
                return self._impl.insert_data(table, data)
        else:
            return self._impl.insert_data(table, data)
        raise NotImplementedError("insert 方法不可用")

    def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> int:
        # 优先调用实现的 update_data / update
        if self._mode == 'database_module':
            if hasattr(self._impl, 'update'):
                return self._impl.update(table, data, condition)
            if hasattr(self._impl, 'execute_update'):
                # 组装简单 UPDATE SQL
                cols = ", ".join([f"{k}=?" for k in data.keys()])
                conds = " AND ".join([f"{k}=?" for k in condition.keys()])
                params = tuple(list(data.values()) + list(condition.values()))
                sql = f"UPDATE {table} SET {cols} WHERE {conds}"
                return self._impl.execute_update(sql, params)
        else:
            return self._impl.update_data(table, data, condition)
        raise NotImplementedError("update 方法不可用")

    def delete(self, table: str, condition: Dict[str, Any]) -> int:
        if self._mode == 'database_module':
            if hasattr(self._impl, 'delete'):
                return self._impl.delete(table, condition)
            if hasattr(self._impl, 'execute_update'):
                conds = " AND ".join([f"{k}=?" for k in condition.keys()])
                params = tuple(condition.values())
                sql = f"DELETE FROM {table} WHERE {conds}"
                return self._impl.execute_update(sql, params)
        else:
            return self._impl.delete_data(table, condition)
        raise NotImplementedError("delete 方法不可用")

    def close(self):
        try:
            if hasattr(self._impl, 'close'):
                return self._impl.close()
        except Exception:
            pass


class DatabaseInterface:
    """
    数据库接口类
    这个类作为中间层，调用队友提供的数据库模块
    """

    def __init__(self, config: dict = None):
        """
        初始化数据库接口

        Args:
            config: 数据库配置字典
        """
        self.config = config or {}
        self.db = None  # _DBAdapter 实例
        self._init_database()

    def _get_db_path(self) -> str:
        # 优先从 config 或 Config 管理器读取
        db_path = self.config.get('path') or self.config.get('database.path')
        if not db_path and Config:
            try:
                # Config.get 可能返回 None
                db_path = Config.get('database.path') or Config.get('database.file') or Config.get('database')
            except Exception:
                db_path = None
        if not db_path:
            db_path = 'data/bupt_teaching.db'
        # 确保目录存在
        p = Path(db_path)
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)

    def _init_database(self):
        """初始化数据库连接"""
        try:
            db_path = self._get_db_path()
            self.db = _DBAdapter(db_path)
            Logger.info("数据库接口初始化完成")
        except Exception as e:
            Logger.error(f"数据库初始化失败: {e}", exc_info=True)
            self.db = None

    # ============ 用户相关操作 ============

    def query_user_by_username(self, username: str) -> Optional[Dict]:
        try:
            sql = "SELECT * FROM users WHERE username=? LIMIT 1"
            res = self.db.query(sql, (username,))
            return res[0] if res else None
        except Exception as e:
            Logger.error(f"查询用户失败: {e}", exc_info=True)
            return None

    def query_user_by_id(self, user_id: int) -> Optional[Dict]:
        try:
            sql = "SELECT * FROM users WHERE id=? LIMIT 1"
            res = self.db.query(sql, (user_id,))
            return res[0] if res else None
        except Exception as e:
            Logger.error(f"查询用户失败: {e}", exc_info=True)
            return None

    def insert_user(self, user_data: Dict) -> int:
        try:
            return self.db.insert('users', user_data)  # 期望返回 id 或 None
        except Exception as e:
            Logger.error(f"插入用户失败: {e}", exc_info=True)
            raise

    def update_user_password(self, user_id: int, new_password_hash: str) -> bool:
        try:
            affected = self.db.update('users', {'password': new_password_hash}, {'id': user_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"更新密码失败: {e}", exc_info=True)
            return False

    def update_last_login(self, user_id: int) -> bool:
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            affected = self.db.update('users', {'last_login': now}, {'id': user_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"更新最后登录时间失败: {e}", exc_info=True)
            return False

    # ============ 数据记录相关操作 ============

    def query_data_list(self, filters: Dict = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        try:
            sql = "SELECT * FROM data_records"
            params: List[Any] = []
            if filters:
                conds = []
                for k, v in filters.items():
                    conds.append(f"{k}=?")
                    params.append(v)
                sql += " WHERE " + " AND ".join(conds)
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            return self.db.query(sql, tuple(params))
        except Exception as e:
            Logger.error(f"查询数据失败: {e}", exc_info=True)
            return []

    def insert_data_record(self, data: Dict) -> int:
        try:
            return self.db.insert('data_records', data)
        except Exception as e:
            Logger.error(f"插入数据记录失败: {e}", exc_info=True)
            raise

    def update_data_record(self, record_id: int, data: Dict) -> bool:
        try:
            affected = self.db.update('data_records', data, {'id': record_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"更新数据失败: {e}", exc_info=True)
            return False

    def delete_data_record(self, record_id: int) -> bool:
        try:
            affected = self.db.delete('data_records', {'id': record_id})
            return affected > 0
        except Exception as e:
            Logger.error(f"删除数据失败: {e}", exc_info=True)
            return False

    # ============ 统计查询 ============

    def get_data_count(self, filters: Dict = None) -> int:
        try:
            sql = "SELECT COUNT(*) as count FROM data_records"
            params: List[Any] = []
            if filters:
                conds = []
                for k, v in filters.items():
                    conds.append(f"{k}=?")
                    params.append(v)
                sql += " WHERE " + " AND ".join(conds)
            res = self.db.query(sql, tuple(params) if params else None)
            if res and isinstance(res, list):
                # 兼容不同实现返回的键名
                first = res[0]
                return int(first.get('count') or first.get('c') or list(first.values())[0])
            return 0
        except Exception as e:
            Logger.error(f"查询数据总数失败: {e}", exc_info=True)
            return 0

    def get_category_statistics(self) -> List[Dict]:
        try:
            sql = "SELECT category, COUNT(*) as count FROM data_records GROUP BY category"
            return self.db.query(sql)
        except Exception as e:
            Logger.error(f"查询分类统计失败: {e}", exc_info=True)
            return []

    # ============ 操作日志 ============

    def log_operation(self, user_id: int, action: str, target: str, details: str = None, ip_address: str = None):
        try:
            log_data = {
                'user_id': user_id,
                'action': action,
                'target': target,
                'details': details,
                'ip_address': ip_address,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            self.db.insert('operation_logs', log_data)
        except Exception as e:
            Logger.error(f"记录操作日志失败: {e}", exc_info=True)

    def close(self):
        """关闭数据库连接"""
        try:
            if self.db:
                self.db.close()
                Logger.info("数据库连接已关闭")
        except Exception as e:
            Logger.error(f"关闭数据库连接失败: {e}", exc_info=True)


# 使用示例（保持原行为）
if __name__ == "__main__":
    try:
        db_config = {}
        if Config:
            try:
                Config.load('config/config.yaml')
                db_config['path'] = Config.get('database.path') or Config.get('database.file')
            except Exception:
                pass
        di = DatabaseInterface(db_config)
        user = di.query_user_by_username('admin')
        print(f"查询结果: {user}")
    finally:
        try:
            di.close()
        except Exception:
            pass

