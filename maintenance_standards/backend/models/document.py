from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    """文档元数据模型"""
    title: str = Field(..., description="文档标题")
    version: str = Field(..., description="文档版本")
    author: Optional[str] = Field(None, description="文档作者")
    department: Optional[str] = Field(None, description="所属部门")
    created_date: Optional[datetime] = Field(None, description="创建日期")
    last_modified: Optional[datetime] = Field(None, description="最后修改日期")
    keywords: List[str] = Field(default_factory=list, description="关键词")

class Document(BaseModel):
    """文档模型"""
    id: str = Field(..., description="文档唯一标识符")
    filename: str = Field(..., description="文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小（字节）")
    content_hash: str = Field(..., description="文件内容哈希值")
    metadata: DocumentMetadata = Field(..., description="文档元数据")
    upload_time: datetime = Field(default_factory=datetime.now, description="上传时间")
    processed: bool = Field(default=False, description="是否已处理")
    status: str = Field(default="pending", description="文档状态")