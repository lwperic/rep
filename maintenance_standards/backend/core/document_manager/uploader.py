import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
from loguru import logger

import tempfile
from ...config import settings
from ...models.document import Document, DocumentMetadata
from .validator import DocumentValidator
from .cleaner import DocumentCleaner
from ...utils.error_handler import DocumentError
from ..knowledge_graph.extractor import KnowledgeExtractor
from ..knowledge_graph.neo4j_manager import Neo4jManager

class DocumentUploader:
    """文档上传处理器"""
    
    def __init__(self):
        self.validator = DocumentValidator()
        self.cleaner = DocumentCleaner()
        self.knowledge_extractor = KnowledgeExtractor()
        self.neo4j_manager = Neo4jManager()
    
    def _generate_file_hash(self, file_content: bytes) -> str:
        """生成文件内容的哈希值"""
        return hashlib.sha256(file_content).hexdigest()
    
    def _save_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """保存文件到磁盘"""
        # 生成唯一的文件ID
        file_id = hashlib.md5(f"{filename}_{datetime.now()}".encode()).hexdigest()
        
        # 构建保存路径
        save_dir = Path(settings.UPLOAD_FOLDER) / datetime.now().strftime("%Y%m")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = save_dir / f"{file_id}_{filename}"
        
        # 保存文件
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path), file_id
    
    def _extract_metadata(self, file_path: str) -> DocumentMetadata:
        """从文档中提取元数据"""
        # TODO: 实现从docx文件中提取元数据的逻辑
        return DocumentMetadata(
            title=Path(file_path).stem,
            version="1.0",
            created_date=datetime.now(),
            last_modified=datetime.now()
        )
        
    def _extract_knowledge_graph(self, file_path: str, doc_id: str) -> None:
        """从文档中提取知识图谱
        
        Args:
            file_path: 文档路径
            doc_id: 文档ID
            
        Raises:
            KnowledgeExtractionError: 知识图谱提取失败
            Neo4jConnectionError: Neo4j数据库连接失败
            KnowledgeValidationError: 知识内容验证失败
        """
        try:
            # 首先验证文档内容
            if not self._validate_document_content(file_path):
                raise KnowledgeValidationError("文档内容不符合知识图谱提取要求")
            
            # 从文档中抽取知识并生成 Cypher 语句
            logger.info(f"从文档 {doc_id} 中抽取知识图谱")
            try:
                cypher_script = self.knowledge_extractor.extract_from_document(file_path, doc_id)
            except Exception as e:
                raise KnowledgeExtractionError(f"知识图谱提取失败: {str(e)}")
            
            # 验证生成的知识图谱
            if not self._validate_knowledge_graph(cypher_script):
                raise KnowledgeValidationError("生成的知识图谱不符合规范要求")
            
            # 连接到 Neo4j 并执行 Cypher 语句
            try:
                self.neo4j_manager.execute_cypher_script(cypher_script)
                logger.info(f"文档 {doc_id} 的知识图谱已存储到数据库")
            except Exception as e:
                raise Neo4jConnectionError(f"Neo4j数据库操作失败: {str(e)}")
                
        except (KnowledgeExtractionError, Neo4jConnectionError, KnowledgeValidationError) as e:
            logger.error(f"知识图谱处理失败: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"未预期的错误: {str(e)}")
            raise KnowledgeExtractionError(f"知识图谱提取过程中发生错误: {str(e)}")
            
    def _validate_document_content(self, file_path: str) -> bool:
        """验证文档内容是否适合进行知识图谱提取
        
        Args:
            file_path: 文档路径
            
        Returns:
            bool: 文档内容是否有效
        """
        try:
            # 使用DocumentValidator进行内容验证
            return self.validator.validate_content_for_extraction(file_path)
        except Exception as e:
            logger.warning(f"文档内容验证失败: {str(e)}")
            return False
            
    def _validate_knowledge_graph(self, cypher_script: str) -> bool:
        """验证生成的知识图谱是否符合规范
        
        Args:
            cypher_script: 生成的Cypher脚本
            
        Returns:
            bool: 知识图谱是否有效
        """
        try:
            # 检查必需的节点类型
            required_node_types = ['MaintenanceStep', 'Tool', 'SafetyPrecaution']
            for node_type in required_node_types:
                if f":{node_type}" not in cypher_script:
                    logger.warning(f"缺少必需的节点类型: {node_type}")
                    return False
                    
            # 检查必需的关系类型
            required_relations = ['NEXT_STEP', 'REQUIRES', 'RELATED_TO']
            for relation in required_relations:
                if f":{relation}" not in cypher_script:
                    logger.warning(f"缺少必需的关系类型: {relation}")
                    return False
                    
            return True
        except Exception as e:
            logger.warning(f"知识图谱验证失败: {str(e)}")
            return False
    
    def upload(self, file_content: bytes, filename: str, extract_knowledge: bool = False) -> Document:
        """处理文档上传
        
        Args:
            file_content: 文件内容
            filename: 文件名
            extract_knowledge: 是否从文档中提取知识图谱
            
        Returns:
            Document: 文档模型实例
            
        Raises:
            DocumentError: 当文档验证失败或上传过程出错时
        """
        try:
            # 验证文件
            self.validator.validate_file(filename, file_content)
            
            # 保存原始文件
            file_path, file_id = self._save_file(file_content, filename)
            
            # 清洗文档
            cleaned_doc, cleaning_stats = self.cleaner.clean_document(file_path)
            
            # 保存清洗后的文档
            cleaned_path = str(Path(file_path).parent / f"cleaned_{Path(file_path).name}")
            cleaned_doc.save(cleaned_path)
            
            # 提取元数据
            metadata = self._extract_metadata(cleaned_path)
            metadata.keywords.extend([
                "cleaned",
                f"removed_paragraphs:{cleaning_stats['removed_paragraphs']}",
                f"cleaned_paragraphs:{cleaning_stats['cleaned_paragraphs']}"
            ])
            
            # 创建文档记录
            document = Document(
                id=file_id,
                filename=filename,
                file_path=cleaned_path,
                file_size=len(file_content),
                content_hash=self._generate_file_hash(file_content),
                metadata=metadata
            )
            
            # 如果需要，提取知识图谱
            if extract_knowledge:
                try:
                    self._extract_knowledge_graph(cleaned_path, file_id)
                    document.metadata.keywords.append("knowledge_graph_extracted")
                    document.metadata.knowledge_graph_status = "success"
                except Exception as e:
                    logger.warning(f"知识图谱提取失败: {str(e)}")
                    document.metadata.keywords.append("knowledge_graph_failed")
                    document.metadata.knowledge_graph_status = "failed"
                    document.metadata.knowledge_graph_error = str(e)
            
            logger.info(f"Document uploaded successfully: {filename}")
            return document
            
        except Exception as e:
            logger.error(f"Error uploading document {filename}: {str(e)}")
            raise DocumentError(f"Failed to upload document: {str(e)}")
            
    def extract_knowledge_from_document(self, document: Document) -> None:
        """从已上传的文档中提取知识图谱
        
        Args:
            document: 文档对象
            
        Raises:
            DocumentError: 当知识图谱提取失败时
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(document.file_path):
                raise DocumentError(f"文档文件不存在: {document.file_path}")
                
            # 提取知识图谱
            self._extract_knowledge_graph(document.file_path, document.id)
            
            # 更新文档元数据
            document.metadata.keywords = [k for k in document.metadata.keywords if k != "knowledge_graph_failed"]
            document.metadata.keywords.append("knowledge_graph_extracted")
            document.metadata.knowledge_graph_status = "success"
            document.metadata.knowledge_graph_error = None
            
            logger.info(f"Successfully extracted knowledge graph from document: {document.filename}")
            
        except Exception as e:
            error_message = f"Failed to extract knowledge graph: {str(e)}"
            logger.error(error_message)
            document.metadata.keywords = [k for k in document.metadata.keywords if k != "knowledge_graph_extracted"]
            document.metadata.keywords.append("knowledge_graph_failed")
            document.metadata.knowledge_graph_status = "failed"
            document.metadata.knowledge_graph_error = str(e)
            raise DocumentError(error_message)