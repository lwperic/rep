import pytest
import os
from pathlib import Path
from backend.core.document_manager.uploader import DocumentUploader
from backend.core.knowledge_graph.extractor import KnowledgeExtractor
from backend.core.knowledge_graph.neo4j_manager import Neo4jManager

def test_document_knowledge_extraction():
    """测试从文档中提取知识图谱"""
    
    # 准备测试文档
    test_doc_path = Path(__file__).parent / "test_document.docx"
    assert test_doc_path.exists(), "测试文档不存在"
    
    try:
        # 创建上传器
        uploader = DocumentUploader()
        
        # 读取测试文档
        with open(test_doc_path, "rb") as f:
            file_content = f.read()
            
        # 上传文档（会自动触发知识图谱提取）
        document = uploader.upload(file_content, "test_document.docx")
        
        # 验证文档上传成功
        assert document.id is not None
        assert "knowledge_graph_extracted" in document.metadata.keywords
        
        # 连接到 Neo4j 验证图谱数据
        neo4j = Neo4jManager()
        try:
            # 查询与文档相关的节点数量
            result = neo4j.execute_cypher(
                f"""
                MATCH (n)
                WHERE n.doc_id = '{document.id}'
                RETURN count(n) as node_count
                """
            )
            assert result[0]['node_count'] > 0, "未找到知识图谱节点"
            
            # 查询关系数量
            result = neo4j.execute_cypher(
                f"""
                MATCH (n)-[r]->(m)
                WHERE n.doc_id = '{document.id}'
                RETURN count(r) as rel_count
                """
            )
            assert result[0]['rel_count'] > 0, "未找到知识图谱关系"
            
        finally:
            # 清理测试数据
            neo4j.execute_cypher(
                f"""
                MATCH (n)
                WHERE n.doc_id = '{document.id}'
                DETACH DELETE n
                """
            )
            neo4j.close()
            
    except Exception as e:
        pytest.fail(f"测试失败: {str(e)}")
        
def test_cypher_generation():
    """测试 Cypher 语句生成"""
    
    # 测试文本
    test_text = """
    发动机机油更换步骤：

    1. 准备工作
    - 确保发动机处于冷态
    - 准备工具：扳手（17mm）、机油滤清器扳手、接油盆
    - 准备4L 5W-30机油
    - 穿戴防护手套和护目镜

    2. 更换步骤
    a) 找到放油螺栓，位于油底壳最低点
    b) 放置接油盆在放油螺栓下方
    c) 使用17mm扳手拆下放油螺栓
    d) 等待机油完全放出
    e) 使用机油滤清器扳手更换机油滤清器
    f) 重新安装放油螺栓（扭矩：30N·m）
    g) 添加新机油

    安全注意事项：
    - 高度注意！热机油可能导致严重烫伤
    - 废机油应妥善收集，避免环境污染
    - 更换过程中避免机油溅到皮肤或眼睛

    所需工具：
    1. 17mm扳手：用于拆装放油螺栓
    2. 机油滤清器扳手：拆装机油滤清器
    3. 接油盆：收集废机油
    4. 扭力扳手：确保放油螺栓安装扭矩正确

    预计完成时间：30-45分钟
    难度级别：初级维修工即可完成
    """
    
    try:
        # 创建知识抽取器
        extractor = KnowledgeExtractor()
        
        # 从文本中抽取知识
        knowledge_graph = extractor.extract_from_text(test_text)
        
        # 验证抽取的知识
        assert len(knowledge_graph.entities) > 0
        assert len(knowledge_graph.relationships) > 0
        
        # 创建数据库管理器
        neo4j_manager = Neo4jManager()
        
        try:
            # 清空数据库（仅用于测试）
            neo4j_manager.delete_all()
            
            # 存储知识图谱
            neo4j_manager.create_knowledge_graph(knowledge_graph)
            
            # 验证存储结果
            # 查找维修任务
            tasks = neo4j_manager.search_entities("MaintenanceTask")
            assert len(tasks) > 0
            
            # 查找工具
            tools = neo4j_manager.search_entities("Tool")
            assert len(tools) > 0
            assert any("扳手" in tool['name'] for tool in tools)
            
            # 查找安全注意事项
            precautions = neo4j_manager.search_entities("SafetyPrecaution")
            assert len(precautions) > 0
            
        finally:
            # 清理数据库
            neo4j_manager.delete_all()
            neo4j_manager.close()
            
    except Exception as e:
        pytest.fail(f"测试失败: {str(e)}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])