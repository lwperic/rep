"""
Neo4j 数据库管理模块
主要功能：执行 Cypher 语句，管理图数据库连接
"""
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, Session
from loguru import logger
from ...config.settings import settings
from ...models.knowledge_graph import KnowledgeGraph

class Neo4jManager:
    """Neo4j 数据库管理器 - 专注于 Cypher 语句执行"""
    
    def __init__(self):
        """初始化数据库连接"""
        self._driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        
    def close(self):
        """关闭数据库连接"""
        self._driver.close()
        
    def execute_cypher(self, cypher: str, params: Dict = None) -> List[Dict]:
        """执行 Cypher 语句
        
        Args:
            cypher: Cypher 查询语句
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        with self._driver.session() as session:
            try:
                logger.debug(f"执行 Cypher 语句: {cypher}")
                if params:
                    logger.debug(f"参数: {params}")
                result = session.run(cypher, parameters=params or {})
                return [dict(record) for record in result]
            except Exception as e:
                logger.error(f"执行 Cypher 语句失败: {str(e)}")
                raise

    def execute_cypher_script(self, script: str) -> None:
        """执行多条 Cypher 语句
        
        Args:
            script: 包含多条 Cypher 语句的脚本
        """
        # 分割脚本为单独的语句
        statements = [stmt.strip() for stmt in script.split(';') if stmt.strip()]
        
        with self._driver.session() as session:
            try:
                # 开启事务
                with session.begin_transaction() as tx:
                    for statement in statements:
                        logger.debug(f"执行语句: {statement}")
                        tx.run(statement)
                    tx.commit()
                logger.info("Cypher 脚本执行成功")
            except Exception as e:
                logger.error(f"执行 Cypher 脚本失败: {str(e)}")
                raise
            
    def search_entities(self, label: str, properties: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索实体
        
        Args:
            label: 实体类型标签
            properties: 属性过滤条件
            
        Returns:
            符合条件的实体列表
        """
        with self._driver.session() as session:
            # 构建属性匹配条件
            conditions = []
            params = {}
            if properties:
                for key, value in properties.items():
                    conditions.append(f"n.{key} = ${key}")
                    params[key] = value
                    
            # 构建查询
            query = f"MATCH (n:{label})"
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " RETURN n"
            
            results = []
            for record in session.run(query, **params):
                node = record['n']
                entity_data = dict(node.items())
                entity_data['id'] = str(node.id)
                results.append(entity_data)
            return results
            
    def create_knowledge_graph(self, kg: KnowledgeGraph):
        """批量创建知识图谱
        
        Args:
            kg: 知识图谱对象
        """
        # 首先创建所有实体
        entity_id_map = {}  # 用于存储原始ID到数据库ID的映射
        for entity in kg.entities:
            db_id = self.create_entity(entity)
            if entity.id:  # 如果实体有原始ID，记录映射关系
                entity_id_map[entity.id] = db_id
            
        # 然后创建所有关系
        for rel in kg.relationships:
            # 使用映射转换原始ID到数据库ID
            source_id = entity_id_map.get(rel.source, rel.source)
            target_id = entity_id_map.get(rel.target, rel.target)
            rel.source = source_id
            rel.target = target_id
            self.create_relationship(rel)
            
    def delete_all(self):
        """清空数据库（仅用于测试）"""
        with self._driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")