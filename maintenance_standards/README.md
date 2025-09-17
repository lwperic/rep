# 维标管理工具

维修标准文档的智能管理与知识图谱构建工具。

## 功能特点

- 文档管理：支持维修标准文档的上传、验证和清洗
- 知识抽取：自动从文档中抽取关键知识并构建知识图谱
- 图谱查询：支持自然语言查询和知识图谱可视化
- 增量更新：支持知识图谱的增量更新

## 安装说明

1. 克隆项目：
```bash
git clone [repository_url]
cd maintenance_standards
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 设置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入必要的配置信息
```

4. 启动服务：
```bash
python main.py
```

## 使用指南

1. 文档上传：
   - 支持 .docx 格式的维修标准文档
   - 自动验证文档格式和内容

2. 知识抽取：
   - 自动抽取文档中的关键知识
   - 构建和更新知识图谱

3. 知识查询：
   - 支持自然语言查询
   - 图形化展示查询结果

## 项目结构

```
maintenance_standards/
├── backend/          # 后端核心功能
├── frontend/         # 前端界面
├── tests/           # 测试用例
└── docs/            # 文档
```

## 开发指南

1. 代码规范：
   - 使用 black 进行代码格式化
   - 使用 flake8 进行代码检查

2. 测试：
   - 使用 pytest 运行测试
   - 确保测试覆盖率达到标准

## 许可证

[许可证类型]

## 贡献指南

欢迎提交 Issue 和 Pull Request