from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=7860)
    
    # 数据库配置
    NEO4J_URI: str = Field(default="bolt://124.223.52.226:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="neo4jneo4j")
    
    # API配置
    DEEPSEEK_API_KEY: str = Field(default="")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO")
    LOG_PATH: str = Field(default="./logs")
    
    # 文档处理配置
    MAX_FILE_SIZE: int = Field(default=10 * 1024 * 1024)  # 10MB
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".docx"])
    UPLOAD_FOLDER: str = Field(default="./uploads")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局配置实例
settings = Settings()

def get_settings() -> Settings:
    """获取应用配置"""
    return settings

# 确保上传和日志目录存在
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(settings.LOG_PATH, exist_ok=True)