"""
配置管理模块
负责加载和管理系统配置
"""

import yaml
from pathlib import Path
from typing import Any, Dict


class Config:
    """配置管理类"""
    
    _config: Dict[str, Any] = {}
    _config_file = None
    
    @classmethod
    def load(cls, config_file: str):
        """
        加载配置文件
        
        Args:
            config_file: 配置文件路径
        """
        cls._config_file = config_file
        config_path = Path(config_file)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            cls._config = yaml.safe_load(f) or {}
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        获取配置项（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，如 'database.host'
            default: 默认值
        
        Returns:
            配置值
        
        Example:
            >>> Config.get('database.host')
            'localhost'
        """
        keys = key.split('.')
        value = cls._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    @classmethod
    def set(cls, key: str, value: Any):
        """
        设置配置项
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = cls._config
        
        # 导航到倒数第二层
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置最后一层的值
        config[keys[-1]] = value
    
    @classmethod
    def save(cls):
        """保存配置到文件"""
        if cls._config_file is None:
            raise ValueError("未指定配置文件")
        
        with open(cls._config_file, 'w', encoding='utf-8') as f:
            yaml.dump(cls._config, f, allow_unicode=True)
    
    @classmethod
    def get_all(cls) -> dict:
        """获取所有配置"""
        return cls._config.copy()


# 使用示例
if __name__ == "__main__":
    Config.load('config/config.yaml')
    print(f"应用名称: {Config.get('app.name')}")
    print(f"数据库类型: {Config.get('database.type')}")
    print(f"服务器端口: {Config.get('network.server.port')}")

