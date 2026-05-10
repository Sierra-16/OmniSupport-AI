# OmniSupport AI

全链路智能客服系统，核心技术栈：**LangGraph + RAG + FastAPI + Vue 3**。
![alt text](<ChatGPT Image 2026年5月10日 15_36_15.png>)
一套完整的 **Agentic Workflow** 系统——AI 自动理解用户意图、调度多个子 Agent 协作、查询数据库、操作业务系统，并在涉及资金安全等关键节点自动挂起等待人工审批。

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                   前端 (Vue 3)                    │
│  ┌──────────────┐   ┌─────────────────────────┐ │
│  │  用户端 Chat  │   │  管理后台 Admin Panel    │ │
│  │  · 流式打字   │   │  · 待处理审批队列        │ │
│  │  · 工作流可视化│   │  · 干预工作台            │ │
│  │              │   │  · 审批/驳回/接管对话     │ │
│  └──────┬───────┘   └───────────┬─────────────┘ │
└─────────┼───────────────────────┼───────────────┘
          │     WebSocket          │
          ▼                        ▼
┌─────────────────────────────────────────────────┐
│                后端 (FastAPI)                    │
│  · JWT 认证中间件 (user/admin 双角色)            │
│  · WebSocket 流式推送 (asyncio.Queue)            │
│  · REST API (auth / history / admin reviews)    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│              AI 编排层 (LangGraph)                │
│                                                  │
│  Supervisor → PreSales / AfterSales / Complaint  │
│                    ↓                             │
│              HITL 人工审批 (interrupt)            │
│                    ↓                             │
│                Finalize 回复合成                  │
│                                                  │
│  挂载能力:                                        │
│  · RAG 混合检索 (向量 + BM25 + RRF + Reranker)    │
│  · Tool Calling (查商品/查订单/退款/建工单)       │
│  · 三层记忆引擎 (Redis + PG + LLM摘要)            │
│  · Checkpoint 持久化 (对话中断可恢复)             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│                  数据持久层                       │
│  · PostgreSQL: 用户/商品/订单/对话/消息/审批      │
│  · ChromaDB: 向量存储 (本地文件持久化)            │
│  · Redis: 会话缓存 / 短期记忆                     │
└─────────────────────────────────────────────────┘
```

## 核心功能

### Multi-Agent 协作

Agent 按**客服业务线**划分，每个 Agent 是客服团队中的"虚拟员工"：

| Agent | 职责 | 挂载工具 |
|-------|------|---------|
| **Supervisor** | 意图识别、任务分发 | LLM 分类器 |
| **PreSales** | 产品推荐、规格答疑、库存查询 | RAG检索、ILIKE搜索、库存查询 |
| **AfterSales** | 订单查询、物流追踪、退款申请 | 查订单、查物流、申请退款 |
| **Complaint** | 投诉处理、创建工单、转人工 | 创建工单、升级人工 |

协作流程：Supervisor 意图分类 → 并行/串行调度子 Agent → 条件路由 → Finalize 汇总回复。

### RAG 混合检索

```
用户问题
  ├─→ 向量检索 (ChromaDB, cosine距离, Top-20)
  ├─→ BM25 关键词检索 (rank-bm25 Okapi算法, Top-20)
  ├─→ RRF 融合排序 (Reciprocal Rank Fusion, k=60, Top-10)
  ├─→ Reranker 精排 (LLM 相关性打分 1-10, Top-5)
  └─→ 从 PG 取完整文档 → 拼接 Prompt → LLM 生成回答
```

### Human-in-the-Loop 人工干预

LangGraph `interrupt()` 在以下场景自动挂起：

- 退款金额 > 500 元
- RAG 检索置信度 < 0.7
- 用户输入"转人工""人工客服"
- LLM 主动标识超出能力范围

管理员通过 WebSocket 实时收到通知，查看对话历史和 AI 决策链路后审批/驳回/接管。

### 三层记忆引擎

| 层级 | 存储 | 生命周期 | 内容 |
|------|------|---------|------|
| 短期记忆 | Redis List | 会话期间 + 30min | 最近 20 条消息 |
| 长期记忆 | PostgreSQL | 永久 | 用户画像标签、对话摘要 |
| 摘要记忆 | LLM 实时生成 | 每次对话结束 | 压缩为简短摘要节省 Token |

### 流式输出

用户消息 → `graph.astream()` → `asyncio.Queue` → WebSocket 逐 Token 推送 → 前端打字机效果 + 工作流节点实时着色。

### Tool Calling 安全

| 维度 | 措施 |
|------|------|
| 权限分级 | 只读工具直接执行，写入工具触发 HITL |
| 参数校验 | Pydantic 模型校验所有入参 |
| 审计日志 | tool_logs 表记录每次调用 |
| 超时熔断 | 外部 API 10s 超时友好降级 |
| 认证鉴权 | JWT 角色校验 (user 聊天 / admin 管理) |

## 技术栈

| 层面 | 技术选型 |
|------|---------|
| 前端框架 | Vue 3, Tailwind CSS, Pinia, Vite |
| 后端框架 | FastAPI, SQLAlchemy (async), Pydantic |
| AI 编排 | LangGraph (StateGraph, 条件边, interrupt/checkpoint) |
| 大模型 | 通义千问 Qwen-Plus (DashScope, OpenAI 兼容协议) |
| Embedding | text-embedding-v2 (DashScope) |
| 向量存储 | ChromaDB (本地持久化) |
| 关键词检索 | rank-bm25 (BM25Okapi) |
| 业务数据库 | PostgreSQL (asyncpg) |
| 缓存 | Redis |
| 认证 | JWT (HS256) + bcrypt |
| 通信 | WebSocket (双向实时) |

## 快速启动

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL
- Redis

### 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-username/omnisupport-ai.git
cd omnisupport-ai

# 2. 配置后端环境变量
cd backend
cp .env.example .env
# 编辑 .env 填入 API Key、数据库连接、JWT 密钥

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 初始化数据库并灌入演示数据
python -m app.seed

# 5. 启动后端
python -m app.main

# 6. 启动前端（新终端）
cd frontend
npm install
npm run dev
```


## 环境变量

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
DATABASE_URL_SYNC=postgresql+psycopg2://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
JWT_SECRET=你的随机密钥
LLM_API_KEY=你的DashScope-API-Key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v2
REFUND_APPROVAL_THRESHOLD=500.0
RAG_CONFIDENCE_THRESHOLD=0.7
```

## 项目结构

```
├── backend/
│   ├── .env                          # 环境变量示例
│   ├── requirements.txt
│   └── app/
│       ├── main.py                   # FastAPI 入口, CORS, 路由注册
│       ├── config.py                 # pydantic-settings 配置管理
│       ├── database.py               # SQLAlchemy 异步引擎
│       ├── seed.py                   # 演示数据灌入 (25商品+8文档+6订单)
│       ├── models/                   # ORM 数据模型
│       ├── api/                      # REST + WebSocket 接口
│       │   ├── auth.py               # 登录/注册 (JWT)
│       │   ├── chat.py               # WebSocket 聊天 (核心)
│       │   ├── admin.py              # 管理后台 API + WebSocket
│       │   └── history.py            # 对话历史查询
│       ├── ai/
│       │   ├── graph.py              # LangGraph 状态机 (核心编排)
│       │   ├── memory.py             # 三层记忆引擎
│       │   ├── agents/               # Agent 实现
│       │   │   ├── supervisor.py     # 意图分类 + 路由
│       │   │   ├── presales.py       # 售前: RAG检索 + 商品查询
│       │   │   ├── aftersales.py     # 售后: 订单/物流/退款
│       │   │   └── complaint.py      # 投诉: 工单 + 转人工
│       │   ├── rag/                  # RAG 检索子系统
│       │   │   ├── chroma_store.py   # ChromaDB 向量存储
│       │   │   ├── retriever.py      # 混合检索编排 (向量+BM25+RRF+Reranker)
│       │   │   ├── bm25.py           # BM25 关键词检索
│       │   │   ├── reranker.py       # LLM 重排序
│       │   │   └── embedder.py       # 文本向量化
│       │   └── tools/                # Agent Tool Calling
│       │       ├── product_tools.py  # 商品搜索/库存查询
│       │       ├── order_tools.py    # 订单查询/物流/退款
│       │       └── ticket_tools.py   # 工单创建/转人工
│       ├── services/
│       │   ├── auth_service.py       # 密码哈希/用户认证
│       │   └── review_queue.py       # HITL 审批队列 + WebSocket 推送
│       ├── middleware/
│       │   └── auth.py               # JWT 签发/验证/角色校验
│       └── schemas/                  # Pydantic 请求/响应模型
├── frontend/
│   ├── vite.config.ts
│   └── src/
│       ├── App.vue
│       ├── router/index.ts           # 路由配置
│       ├── stores/auth.ts            # Pinia 认证状态管理
│       ├── api/client.ts             # Axios HTTP + 拦截器
│       ├── composables/useWebSocket.ts
│       ├── views/
│       │   ├── ChatView.vue          # 用户聊天页
│       │   ├── AdminView.vue         # 管理后台页
│       │   └── LoginView.vue         # 登录页
│       └── components/
│           ├── chat/
│           │   ├── ChatCanvas.vue    # 消息列表 (自动滚动)
│           │   ├── ChatInput.vue     # 输入框
│           │   └── MessageBubble.vue # 消息气泡 (Markdown 渲染)
│           ├── workflow/
│           │   └── WorkflowVisualizer.vue  # SVG 工作流可视化
│           └── admin/
│               ├── PendingQueue.vue       # 待处理审批列表
│               └── InterventionPanel.vue  # 干预工作台
└── README.md
```
![alt text](<屏幕截图 2026-05-09 163833.png>) ![alt text](<屏幕截图 2026-05-09 163847.png>) ![alt text](<屏幕截图 2026-05-09 163947.png>)
![alt text](<屏幕截图 2026-05-09 164001.png>)

## 许可证

MIT
