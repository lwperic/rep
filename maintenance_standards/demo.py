from backend.core.knowledge_graph.extractor import KnowledgeExtractor
from backend.core.knowledge_graph.neo4j_manager import Neo4jManager

def main():
    # 测试文本 - 包含维修步骤、工具、安全注意事项等
    test_text = """
    发动机皮带更换维修指南

    1. 安全准备
       - 确保发动机完全冷却
       - 断开蓄电池负极
       - 准备好个人防护装备
       - 检查工作区域照明

    2. 工具准备
       - 14mm套筒扳手：用于松动皮带张紧器
       - 检测尺：测量皮带张力
       - 头灯：照明使用
       - 记号笔：标记皮带走向

    3. 拆卸步骤
       a) 观察并记录皮带走向
       b) 找到自动张紧器位置
       c) 使用14mm套筒扳手顺时针转动张紧器
       d) 小心取下旧皮带
       e) 检查各皮带轮是否磨损

    4. 安装新皮带
       a) 对照记录的走向
       b) 从最底部的皮带轮开始安装
       c) 确保皮带正确嵌入各导轮槽
       d) 缓慢释放张紧器
       e) 人工转动曲轴2圈检查

    安全注意事项：
    - 警告！操作张紧器时注意手指安全
    - 更换时发动机必须处于冷态
    - 避免皮带接触油污
    - 安装时严禁使用尖锐工具

    质量要求：
    - 皮带安装必须对准各皮带轮槽
    - 张力需符合规范要求
    - 确保无扭曲和反转

    预计工时：45-60分钟
    技能要求：中级维修技工
    """

    try:
        # 创建知识抽取器
        extractor = KnowledgeExtractor()
        print("\n1. 开始从文本中抽取知识...")
        
        # 从文本中抽取知识
        print("\n调用API...")
        knowledge_graph = extractor.extract_from_text(test_text)
        print("\n已获取API响应")
        
        print("\n处理实体数据...")
        print(f"总实体数: {len(knowledge_graph.entities)}")
        
        # 打印抽取的实体
        print("\n2. 抽取的实体:")
        for i, entity in enumerate(knowledge_graph.entities, 1):
            print(f"\n实体 {i}:")
            print(f"类型: {entity.type}")
            print(f"ID: {entity.id}")
            print(f"名称: {entity.name}")
            print("属性:", entity.properties)
            
        print("\n处理关系数据...")
        print(f"总关系数: {len(knowledge_graph.relationships)}")
        
        # 打印抽取的关系
        print("\n3. 抽取的关系:")
        for i, rel in enumerate(knowledge_graph.relationships, 1):
            print(f"\n关系 {i}:")
            print(f"类型: {rel.type}")
            print(f"从: {rel.source} -> 到: {rel.target}")
            if rel.properties:
                print("属性:", rel.properties)
                
        # 创建Neo4j管理器
        print("\n4. 连接到Neo4j数据库...")
        neo4j_manager = Neo4jManager()
        
        try:
            # 清空数据库（仅用于演示）
            print("清空已有数据...")
            neo4j_manager.delete_all()
            
            # 存储知识图谱
            print("存储新的知识图谱...")
            neo4j_manager.create_knowledge_graph(knowledge_graph)
            
            # 查询示例
            print("\n5. 查询示例:")
            
            # 查找维修步骤
            print("\n维修步骤:")
            steps = neo4j_manager.search_entities("MaintenanceStep")
            for step in steps:
                print(f"- {step['name']}")
            
            # 查找工具
            print("\n工具:")
            tools = neo4j_manager.search_entities("Tool")
            for tool in tools:
                print(f"- {tool['name']}")
            
            # 查找安全注意事项
            print("\n安全注意事项:")
            precautions = neo4j_manager.search_entities("SafetyPrecaution")
            for precaution in precautions:
                print(f"- {precaution['name']}")
                
        finally:
            # 关闭数据库连接
            neo4j_manager.close()
            
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print(f"\n发生错误: {str(e)}")
        print("\n详细错误信息:")
        print(traceback.format_exc())