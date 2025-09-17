class DocumentError(Exception):
    """文档处理相关错误的基类"""
    pass

class ValidationError(DocumentError):
    """文档验证错误"""
    pass

class ProcessingError(DocumentError):
    """文档处理错误"""
    pass

class UploadError(DocumentError):
    """文档上传错误"""
    pass

class KnowledgeExtractionError(DocumentError):
    """知识图谱提取错误"""
    pass

class Neo4jConnectionError(DocumentError):
    """Neo4j数据库连接错误"""
    pass

class KnowledgeValidationError(DocumentError):
    """知识内容验证错误"""
    pass