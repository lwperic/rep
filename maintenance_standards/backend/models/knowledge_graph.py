from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Entity(BaseModel):
    """知识图谱实体基类"""
    id: Optional[str] = None
    type: str
    name: str
    properties: Dict[str, Any] = {}

class Relationship(BaseModel):
    """知识图谱关系基类"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}

class MaintenanceStep(Entity):
    """维修步骤实体"""
    order: int
    description: str
    tools: List[str] = []
    precautions: List[str] = []

class Tool(Entity):
    """工具实体"""
    purpose: str
    specifications: Optional[str] = None

class Part(Entity):
    """零件实体"""
    function: str
    location: Optional[str] = None
    specifications: Optional[str] = None

class MaintenanceTask(Entity):
    """维修任务实体"""
    description: str
    difficulty: Optional[str] = None
    estimated_time: Optional[str] = None
    required_skills: List[str] = []

class SafetyPrecaution(Entity):
    """安全注意事项实体"""
    category: str
    severity: str
    description: str

class KnowledgeGraph(BaseModel):
    """知识图谱模型"""
    entities: List[Entity] = []
    relationships: List[Relationship] = []