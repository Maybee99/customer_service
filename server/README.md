 # Customer Service Agent

 AI 智能客服后端系统，基于 Agent 架构 + RAG 检索增强生成。

 ## 技术栈

 - **后端框架**: Python FastAPI
 - **Agent 引擎**: LangGraph 风格 Function Calling
 - **向量数据库**: Milvus 2.5
 - **关键词检索**: BM25
 - **LLM**: 通义千问 (DashScope OpenAI-Compatible API)
 - **数据库**: MySQL 8.0 + Redis 7
 - **前端**: React 19 + Vite (位于 `../Ai_customer`)

 ## 快速启动

 ### 1. 启动依赖服务 (Milvus + MySQL + Redis)
 ```bash
 docker-compose up -d
 ```

 ### 2. 安装 Python 依赖
 ```bash
 pip install -r requirements.txt
 ```

 ### 3. 配置环境变量
 ```bash
 cp .env.example .env
 # 编辑 .env 填入 LLM_API_KEY 等配置
 ```

 ### 4. 启动后端
 ```bash
 uvicorn app.main:app --reload --port 8000
 ```

 ### 5. 启动前端
 ```bash
 cd ../Ai_customer
 npm install
 npm run dev
 ```

 ## 项目结构

 ```
 customer_service_agent/
 ├── app/
 │   ├── api/            # FastAPI 路由
 │   ├── agents/         # Agent 调度 + 工具
 │   ├── rag/            # RAG 检索 (Milvus + BM25)
 │   ├── models/         # SQLAlchemy 模型
 │   ├── services/       # 业务逻辑
 │   └── utils/          # 工具函数
 ├── docker-compose.yml  # Milvus + MySQL + Redis
 ├── docker/Dockerfile   # 后端镜像
 └── requirements.txt
 ```
 
 ## API 接口
 
 - `POST /api/chat` — 对话（Agent 处理）
 - `GET /api/conversations` — 会话列表
 - `GET /api/conversations/{id}` — 会话详情
 - `POST /api/knowledge/import` — 导入知识文档
 - `GET /api/knowledge/files` — 知识文件列表
 - `GET /health` — 健康检查
 - `GET /` — API 信息
