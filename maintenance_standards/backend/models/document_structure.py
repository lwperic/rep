from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ParagraphType(str, Enum):
    """段落类型枚举"""
    TITLE = "title"          # 标题
    CONTENT = "content"      # 正文内容
    LIST_ITEM = "list_item"  # 列表项
    TABLE = "table"          # 表格
    IMAGE = "image"          # 图片
    REFERENCE = "reference"  # 引用
    UNKNOWN = "unknown"      # 未知类型

class TableCell(BaseModel):
    """表格单元格"""
    text: str = Field(..., description="单元格文本内容")
    row: int = Field(..., description="行号")
    col: int = Field(..., description="列号")
    is_header: bool = Field(default=False, description="是否为表头")
    rowspan: int = Field(default=1, description="跨行数")
    colspan: int = Field(default=1, description="跨列数")

class Table(BaseModel):
    """表格"""
    cells: List[TableCell] = Field(default_factory=list, description="单元格列表")
    num_rows: int = Field(..., description="行数")
    num_cols: int = Field(..., description="列数")
    caption: Optional[str] = Field(None, description="表格标题")

class Image(BaseModel):
    """图片"""
    path: str = Field(..., description="图片路径")
    caption: Optional[str] = Field(None, description="图片标题")
    width: Optional[int] = Field(None, description="图片宽度")
    height: Optional[int] = Field(None, description="图片高度")

class Paragraph(BaseModel):
    """段落"""
    text: str = Field(..., description="段落文本")
    type: ParagraphType = Field(..., description="段落类型")
    level: int = Field(default=0, description="标题层级（仅对标题类型有效）")
    index: int = Field(..., description="段落在文档中的索引")
    style: Optional[str] = Field(None, description="段落样式名称")
    table: Optional[Table] = Field(None, description="表格数据（仅对表格类型有效）")
    image: Optional[Image] = Field(None, description="图片数据（仅对图片类型有效）")

class Section(BaseModel):
    """文档章节"""
    title: Optional[Paragraph] = Field(None, description="章节标题")
    level: int = Field(..., description="章节层级")
    paragraphs: List[Paragraph] = Field(default_factory=list, description="章节段落")
    subsections: List["Section"] = Field(default_factory=list, description="子章节")
    start_index: int = Field(..., description="章节开始索引")
    end_index: int = Field(..., description="章节结束索引")

class DocumentStructure(BaseModel):
    """文档结构"""
    title: Optional[str] = Field(None, description="文档标题")
    sections: List[Section] = Field(default_factory=list, description="文档章节")
    paragraphs: List[Paragraph] = Field(default_factory=list, description="所有段落")
    tables: List[Table] = Field(default_factory=list, description="所有表格")
    images: List[Image] = Field(default_factory=list, description="所有图片")
    metadata: Dict = Field(default_factory=dict, description="文档元数据")