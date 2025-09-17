"""
知识图谱提取模块
主要功能：从文档文本中提取知识并生成 Cypher 语句
"""
from typing import List, Dict, Any
from loguru import logger
import json
import requests
from ...config.settings import settings

class KnowledgeExtractor:
    """知识抽取器 - 使用大模型从文本生成 Cypher 语句"""
    
    def __init__(self):
        """初始化"""
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = "https://api.deepseek.com/v1/chat/completions"
        
    def _call_api(self, prompt: str) -> Dict[str, Any]:
        """调用DeepSeek API
        
        Args:
            prompt: 提示文本
            
        Returns:
            API响应
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            "model": "deepseek-chat",
            "temperature": 0.1
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            raise
            
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的知识图谱构建专家。请从维修文档中抽取知识并直接生成 Neo4j 的 Cypher 语句。

规则：
1. 使用 CREATE 语句创建节点和关系
2. 为节点添加合适的标签和属性
3. 使用有意义的关系类型
4. 确保生成的是可执行的 Cypher 语句

节点类型：
- MaintenanceStep: 维修步骤
- Tool: 工具
- Part: 零件
- MaintenanceTask: 维修任务
- SafetyPrecaution: 安全注意事项

关系类型：
- NEXT_STEP: 步骤顺序
- REQUIRES: 需要（工具/零件）
- PART_OF: 属于
- RELATED_TO: 相关

输出格式示例：
```cypher
// 创建维修步骤节点
CREATE (step1:MaintenanceStep {
    id: 'step1',
    name: '准备工作',
    description: '确保发动机冷却',
    order: 1
});

// 创建工具节点
CREATE (tool1:Tool {
    id: 'tool1',
    name: '扳手',
    purpose: '拆卸螺丝'
});

// 创建关系
CREATE (step1)-[:REQUIRES]->(tool1);
```

请分析输入的维修文档，识别所有相关实体和关系，并生成完整的 Cypher 语句。确保语句可以直接在 Neo4j 中执行。"""
        
    def _parse_api_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析API响应
        
        Args:
            response: API响应
            
        Returns:
            解析后的知识数据
        """
        try:
            content = response['choices'][0]['message']['content']
            # 记录原始响应内容以便调试
            logger.debug(f"API原始响应: {content}")
            
            # 尝试从内容中提取JSON部分
            try:
                start = content.index('{')
                end = content.rindex('}') + 1
                json_content = content[start:end]
                data = json.loads(json_content)
                
                # 将结构化的API响应转换为统一格式
                entities = []
                # 处理维修步骤
                for step in data['entities'].get('MaintenanceStep', []):
                    entities.append({
                        'type': 'MaintenanceStep',
                        'id': step['id'],
                        'name': f"步骤 {step['step_order']}: {step['description'][:30]}...",
                        'order': step['step_order'],
                        'description': step['description'],
                        'tools': step.get('required_tools', []),
                        'precautions': [step.get('notes', '')]
                    })
                
                # 处理工具
                for tool in data['entities'].get('Tool', []):
                    entities.append({
                        'type': 'Tool',
                        'id': tool['id'],
                        'name': tool['name'],
                        'purpose': tool['purpose'],
                        'specifications': tool.get('specification')
                    })
                
                # 处理零件
                for part in data['entities'].get('Part', []):
                    entities.append({
                        'type': 'Part',
                        'id': part['id'],
                        'name': part['name'],
                        'function': part['function'],
                        'location': part.get('location'),
                        'specifications': part.get('specification')
                    })
                
                # 处理维修任务
                for task in data['entities'].get('MaintenanceTask', []):
                    entities.append({
                        'type': 'MaintenanceTask',
                        'id': task['id'],
                        'name': task['description'],
                        'difficulty': task.get('difficulty', ''),
                        'estimated_time': task.get('estimated_time', ''),
                        'required_skills': task.get('required_skills', '')
                    })
                
                # 处理安全注意事项
                for safety in data['entities'].get('SafetyPrecaution', []):
                    entities.append({
                        'type': 'SafetyPrecaution',
                        'id': safety['id'],
                        'name': safety['description'][:50],
                        'category': safety['category'],
                        'severity': safety['severity'],
                        'description': safety['description']
                    })
                
                # 处理关系
                relationships = []
                for rel in data['relations']:
                    relationships.append({
                        'source': rel['from'],
                        'target': rel['to'],
                        'type': rel['type'],
                        'properties': {}
                    })
                
                return {
                    'entities': entities,
                    'relationships': relationships
                }
                
            except (ValueError, json.JSONDecodeError) as e:
                # 如果无法解析JSON，则构建结构化的知识
                logger.warning(f"无法解析JSON响应，将进行手动结构化: {str(e)}")
                return self._structure_knowledge_from_text(content)
        except Exception as e:
            logger.error(f"解析API响应失败: {str(e)}")
            raise
            
    def _structure_knowledge_from_text(self, text: str) -> Dict[str, Any]:
        """从文本响应中构建结构化知识
        
        Args:
            text: API响应文本
            
        Returns:
            结构化的知识数据
        """
        # 从文本中识别实体和关系
        entities = []
        relationships = []
        
        # 处理维修步骤
        steps = []
        current_step = None
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 识别维修步骤
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_step:
                    steps.append(current_step)
                current_step = {
                    'type': 'MaintenanceStep',
                    'id': f'step_{len(steps)}',
                    'name': line,
                    'description': line,
                    'order': len(steps) + 1,
                    'tools': [],
                    'precautions': []
                }
                entities.append(current_step)
                
            # 识别工具
            elif '扳手' in line or '工具' in line:
                tool = {
                    'type': 'Tool',
                    'id': f'tool_{len(entities)}',
                    'name': line.split('：')[0] if '：' in line else line,
                    'purpose': line.split('：')[1] if '：' in line else '',
                    'specifications': None
                }
                entities.append(tool)
                
                # 添加工具和步骤的关系
                if current_step:
                    relationships.append({
                        'source': current_step['id'],
                        'target': tool['id'],
                        'type': 'REQUIRES',
                        'properties': {}
                    })
                    
            # 识别安全注意事项
            elif '注意' in line or '警告' in line or '禁止' in line:
                precaution = {
                    'type': 'SafetyPrecaution',
                    'id': f'safety_{len(entities)}',
                    'name': line,
                    'category': 'Safety',
                    'severity': 'High' if '高度' in line or '严重' in line else 'Medium',
                    'description': line
                }
                entities.append(precaution)
        
        # 添加最后一个步骤
        if current_step:
            steps.append(current_step)
            
        # 添加步骤之间的顺序关系
        for i in range(len(steps) - 1):
            relationships.append({
                'source': steps[i]['id'],
                'target': steps[i + 1]['id'],
                'type': 'NEXT_STEP',
                'properties': {}
            })
            
        return {
            'entities': entities,
            'relationships': relationships
        }
            
    def _extract_cypher(self, response: Dict[str, Any]) -> str:
        """从 API 响应中提取 Cypher 语句
        
        Args:
            response: API 响应
            
        Returns:
            Cypher 语句
        """
        try:
            content = response['choices'][0]['message']['content']
            # 提取 Cypher 代码块
            if '```cypher' in content:
                start = content.index('```cypher') + 8
                end = content.rindex('```')
                cypher = content[start:end].strip()
            elif '```' in content:
                start = content.index('```') + 3
                end = content.rindex('```')
                cypher = content[start:end].strip()
            else:
                cypher = content.strip()
                
            # 添加调试日志
            logger.debug(f"提取的原始 Cypher: [{cypher[:50]}...]")
                
            # 去掉可能存在的前导 'r' 字符
            if cypher.startswith('r"') or cypher.startswith("r'") or cypher.startswith('r'):
                cypher = cypher[1:].strip()
                
            # 添加更多调试日志
            logger.debug(f"处理后的 Cypher: [{cypher[:50]}...]")
            
            return cypher
        except Exception as e:
            logger.error(f"提取 Cypher 语句失败: {str(e)}")
            raise

    def extract_from_text(self, text: str) -> str:
        """从文本中提取知识并生成 Cypher 语句
        
        Args:
            text: 输入文本
            
        Returns:
            Cypher 语句
        """
        # 调用 API 进行知识抽取
        response = self._call_api(text)
        
        # 提取 Cypher 语句
        cypher = self._extract_cypher(response)
        logger.debug(f"生成的 Cypher 语句:\n{cypher}")
        
        return cypher

    def extract_from_document(self, doc_path: str, doc_id: str) -> str:
        """从文档中提取知识并生成 Cypher 语句
        
        Args:
            doc_path: 文档路径
            doc_id: 文档ID
            
        Returns:
            Cypher 语句
        """
        from ...core.document_manager.parser import DocumentParser
        
        # 解析文档获取文本内容
        parser = DocumentParser()
        doc_content = parser.parse(doc_path)
        
        # 在提示词中添加文档信息
        doc_info = f"""
文档ID: {doc_id}
---
{doc_content}
"""
        
        # 从文本中提取知识
        return self.extract_from_text(doc_info)
        
        # 处理所有实体
        for entity_type, items in entities_data.items():
            for item in items:
                properties = {}
                if entity_type == 'MaintenanceStep':
                    name = f"步骤 {item['step_order']}: {item['description'][:30]}..."
                    properties = {
                        'order': item['step_order'],
                        'description': item['description'],
                        'tools': item.get('required_tools', []),
                        'precautions': [item.get('notes', '')]
                    }
                elif entity_type == 'Tool':
                    name = item['name']
                    properties = {
                        'purpose': item['purpose'],
                        'specifications': item.get('specification')
                    }
                elif entity_type == 'Part':
                    name = item['name']
                    properties = {
                        'function': item['function'],
                        'location': item.get('location'),
                        'specifications': item.get('specification')
                    }
                elif entity_type == 'MaintenanceTask':
                    name = item['description'][:50]
                    properties = {
                        'description': item['description'],
                        'difficulty': item.get('difficulty', ''),
                        'estimated_time': item.get('estimated_time', ''),
                        'required_skills': [item.get('required_skills')] if item.get('required_skills') else []
                    }
                elif entity_type == 'SafetyPrecaution':
                    name = item['description'][:50]
                    properties = {
                        'category': item['category'],
                        'severity': item['severity'],
                        'description': item['description']
                    }
                else:
                    logger.warning(f"未知的实体类型: {entity_type}")
                    continue
                    
                entities.append({
                    'id': item['id'],
                    'type': entity_type,
                    'name': name,
                    'properties': properties
                })
                
            else:
                logger.warning(f"未知的实体类型: {entity_type}")
                continue
        # 创建关系
        relationships = []
        for rel in data.get('relationships', []):
            relationship = Relationship(
                source=rel['source'],
                target=rel['target'],
                type=rel['type'],
                properties=rel.get('properties', {})
            )
            relationships.append(relationship)
            
        return KnowledgeGraph(
            entities=entities,
            relationships=relationships
        )