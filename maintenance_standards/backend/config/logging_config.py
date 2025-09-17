from loguru import logger
import sys
import os
from .settings import settings

def setup_logging():
    """配置日志系统"""
    
    # 清除默认的处理器
    logger.remove()
    
    # 配置控制台日志
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )
    
    # 配置文件日志
    log_file = os.path.join(settings.LOG_PATH, "app.log")
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.LOG_LEVEL,
        rotation="500 MB",
        retention="10 days",
        compression="zip"
    )
    
    # 设置异常处理
    def handle_exception(exc_type, exc_value, exc_traceback):
        """处理未捕获的异常"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.opt(exception=(exc_type, exc_value, exc_traceback)).error("Uncaught exception:")
    
    sys.excepthook = handle_exception
    
    logger.info("Logging system initialized")