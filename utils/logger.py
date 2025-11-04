"""
日志系统模块
提供统一的日志记录功能
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """日志管理类"""
    
    _logger = None
    _initialized = False
    
    @classmethod
    def init(cls, log_file='logs/app.log', level=logging.INFO):
        """
        初始化日志系统
        
        Args:
            log_file: 日志文件路径
            level: 日志级别
        """
        if cls._initialized:
            return
        
        # 确保日志目录存在
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        # 创建logger
        cls._logger = logging.getLogger('IDMS')
        cls._logger.setLevel(logging.DEBUG)
        
        # 文件处理器（自动轮转）
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        cls._logger.addHandler(file_handler)
        cls._logger.addHandler(console_handler)
        
        cls._initialized = True
    
    @classmethod
    def _ensure_initialized(cls):
        """确保日志系统已初始化"""
        if not cls._initialized:
            cls.init()
    
    @classmethod
    def debug(cls, message, *args, **kwargs):
        """调试日志"""
        cls._ensure_initialized()
        cls._logger.debug(message, *args, **kwargs)
    
    @classmethod
    def info(cls, message, *args, **kwargs):
        """信息日志"""
        cls._ensure_initialized()
        cls._logger.info(message, *args, **kwargs)
    
    @classmethod
    def warning(cls, message, *args, **kwargs):
        """警告日志"""
        cls._ensure_initialized()
        cls._logger.warning(message, *args, **kwargs)
    
    @classmethod
    def error(cls, message, *args, **kwargs):
        """错误日志"""
        cls._ensure_initialized()
        cls._logger.error(message, *args, **kwargs)
    
    @classmethod
    def critical(cls, message, *args, **kwargs):
        """严重错误日志"""
        cls._ensure_initialized()
        cls._logger.critical(message, *args, **kwargs)


# 使用示例
if __name__ == "__main__":
    Logger.init()
    Logger.info("这是一条信息日志")
    Logger.warning("这是一条警告日志")
    Logger.error("这是一条错误日志")

