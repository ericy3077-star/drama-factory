# Drama Factory — AI Product Matrix

投资行业（InvestMind）+ 教育行业（EduStar）双垂直 AI 平台，共享四大 AI 引擎基础设施。

## 项目结构

```
drama-factory/
├── backend/          # FastAPI 后端（Python 3.11）
├── frontend/         # Next.js 14 前端（TypeScript）
├── docker-compose.yml
└── .env.example
```

## 快速启动

```bash
cp .env.example .env   # 填写 API Keys
docker compose up      # 启动所有服务
```

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 后端架构

### AI 平台层（`backend/app/platform/`）
| 引擎 | 职责 |
|------|------|
| `memory/` MemoryOS | 用户记忆持久化、向量检索、知识图谱 |
| `agent/` AgentOS | LangGraph 状态机、任务规划、工具调用 |
| `avatar/` AvatarOS | 数字人训练、视频生成（HeyGen） |
| `percept/` PerceptOS | 多模态理解，模型路由（haiku/sonnet/gemini） |

### 垂直应用层（`backend/app/verticals/`）
- `invest/` — InvestMind：信息流、研究工作台、投资助手
- `edu/` — EduStar：课程工厂、学习平台、数据分析

### 异步 Worker（`backend/app/workers/`）
- `avatar_worker.py` — 处理数字人视频生成任务
- `feed_worker.py` — 定时抓取投资信息流

## 前端架构

### 路由结构
```
/                    落地页
/login, /register    认证
/invest/*            InvestMind Dashboard
/edu/*               EduStar Dashboard
```

### 核心 Hooks
- `useChat` — SSE 流式对话，支持 Agent 工具调用可视化
- `useWebSocket` — 实时任务状态推送
- `useTaskStatus` — 异步任务追踪（数字人生成等）
- `useMemory` — 用户记忆读写

## 数据库

运行初始化 Schema：
```bash
psql $DATABASE_URL < backend/migrations/versions/001_initial_schema.sql
```

核心表：`users`, `memories`（含 vector 索引）, `avatars`, `courses`, `lessons`, `learner_events`, `research_notes`, `watchlists`

## 模型路由策略

| 场景 | 模型 |
|------|------|
| 简单问答（< 2k chars） | claude-haiku-4-5 |
| 文档分析 / 含图像 | claude-sonnet-4-6 |
| 长视频 / 超长文档（> 50k） | gemini-1.5-pro |

## 开发规范

- 后端：所有函数 `async/await`，Pydantic v2 模型，完整类型注解
- 前端：TypeScript strict mode，TanStack Query 管理服务端状态
- AI 调用：通过 LangSmith 追踪，开发环境设置 `LANGSMITH_TRACING=true`
- 安全：所有数据库查询强制 RLS，用户输入严格校验
