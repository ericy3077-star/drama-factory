# Drama Factory — 系统架构图集

本文档包含 Drama Factory 平台的 6 张核心架构图，覆盖系统全景、数据流、异步流水线、数据模型、AI 检索机制和产品分层结构。所有图使用 Mermaid 语法，可在 GitHub / Notion / VS Code 中直接渲染。

---

## 图1：系统架构全景（C4 Container 风格）

**说明：** 采用分层视角展示整个平台的容器关系。从用户端浏览器/移动端出发，经过统一网关进入两条垂直业务线（InvestMind / EduStar），业务线共享同一套 AI 平台引擎，最终连接多类存储和外部 AI 服务。关键设计原则：垂直业务层共享 AI 平台层，但各自拥有独立的业务逻辑和数据表。

```mermaid
graph TD
    subgraph CLIENT["客户端层"]
        WEB["🌐 Web Browser\nNext.js 14 SPA"]
        MOB["📱 Mobile\nPWA / Future Native"]
    end

    subgraph GATEWAY["网关层"]
        APIGW["API Gateway\nFastAPI · /api/v1/*\n鉴权 · 限流 · 路由"]
        WSGW["WebSocket Gateway\nFastAPI WebSocket\n实时任务推送"]
    end

    subgraph APP["应用层"]
        INVEST["InvestMind Service\n信息流 · 研究工作台\n投资助手 · 行情监控"]
        EDU["EduStar Service\n课程工厂 · 学习平台\n数据分析 · 进度追踪"]
        SHARED["Shared Services\n用户认证 · 订阅计费\n通知 · 文件上传"]
    end

    subgraph AIPLATFORM["AI 平台层"]
        MEMORY["MemoryOS\n向量检索 · 知识图谱\n长期记忆持久化"]
        AGENT["AgentOS\nLangGraph 状态机\n任务规划 · 工具调用"]
        AVATAR["AvatarOS\n数字人训练\n视频生成调度"]
        PERCEPT["PerceptOS\n多模态理解\n模型路由 · 文档解析"]
    end

    subgraph DATA["数据层"]
        PG["PostgreSQL 15\n+ pgvector 扩展\n关系数据 + 向量索引"]
        NEO["Neo4j\n知识图谱\n实体关系网络"]
        REDIS["Redis 7\n任务队列 · 会话缓存\nWebSocket 状态"]
        S3["S3 / Supabase Storage\n视频文件 · 文档\n用户上传素材"]
    end

    subgraph EXTERNAL["外部 AI 服务"]
        CLAUDE["Anthropic Claude API\nHaiku · Sonnet\n主力推理引擎"]
        GEMINI["Google Gemini API\nGemini 1.5 Pro\n超长文档 · 视频理解"]
        HEYGEN["HeyGen API\n数字人视频生成\n口型同步渲染"]
        ELEVEN["ElevenLabs API\n语音合成 TTS\n多语言 · 声色克隆"]
    end

    WEB -->|"HTTPS / SSE"| APIGW
    MOB -->|"HTTPS / SSE"| APIGW
    WEB -->|"WSS"| WSGW
    MOB -->|"WSS"| WSGW

    APIGW --> INVEST
    APIGW --> EDU
    APIGW --> SHARED
    WSGW --> SHARED

    INVEST --> AGENT
    INVEST --> MEMORY
    INVEST --> PERCEPT
    EDU --> AGENT
    EDU --> MEMORY
    EDU --> PERCEPT
    SHARED --> AVATAR

    AGENT --> PERCEPT
    AGENT --> MEMORY
    AVATAR --> REDIS

    MEMORY --> PG
    MEMORY --> NEO
    AGENT --> REDIS
    SHARED --> PG
    AVATAR --> S3
    INVEST --> PG
    EDU --> PG

    PERCEPT -->|"haiku / sonnet"| CLAUDE
    PERCEPT -->|"> 50k tokens"| GEMINI
    AVATAR -->|"视频合成任务"| HEYGEN
    AVATAR -->|"语音生成任务"| ELEVEN

    style CLIENT fill:#dbeafe,stroke:#3b82f6
    style GATEWAY fill:#fef3c7,stroke:#f59e0b
    style APP fill:#dcfce7,stroke:#16a34a
    style AIPLATFORM fill:#f3e8ff,stroke:#9333ea
    style DATA fill:#fee2e2,stroke:#dc2626
    style EXTERNAL fill:#f1f5f9,stroke:#64748b
```

---

## 图2：数据流图 — 用户消息完整生命周期

**说明：** 描述从用户发送一条消息到收到 AI 回复的完整链路。核心设计：AgentOS 先做任务规划，PerceptOS 做语义理解和模型路由，MemoryOS 在推理前召回相关记忆（RAG），推理后将新对话写入长期记忆，最终通过 SSE 流式返回。整个链路通过 LangSmith 全程追踪。

```mermaid
sequenceDiagram
    actor User as 用户
    participant FE as Next.js 前端
    participant GW as API Gateway
    participant Auth as 认证中间件
    participant Agent as AgentOS<br/>(LangGraph)
    participant Percept as PerceptOS<br/>(模型路由)
    participant Memory as MemoryOS<br/>(记忆引擎)
    participant Tool as 工具层<br/>(外部数据源)
    participant LLM as LLM<br/>(Claude/Gemini)
    participant LS as LangSmith<br/>(追踪)

    User->>FE: 输入消息，点击发送
    FE->>GW: POST /api/v1/chat/stream<br/>{ message, session_id, vertical }
    GW->>Auth: 验证 JWT Token
    Auth-->>GW: user_id + 权限范围

    GW->>Agent: 创建 LangGraph Run<br/>注入 user_id, message, context
    Agent->>LS: 开始追踪 Trace

    Note over Agent: 任务规划节点<br/>判断意图：问答/分析/生成

    Agent->>Percept: 语义理解请求<br/>{ text, images?, doc_refs? }
    Percept->>Percept: 判断输入复杂度<br/>选择模型路由

    par 并行执行记忆召回
        Agent->>Memory: 向量检索 Top-5 相关记忆<br/>query_embedding(message)
        Memory->>Memory: pgvector ANN 搜索<br/>+ BM25 关键词融合
        Memory-->>Agent: 返回相关记忆片段
    and 检索知识图谱
        Agent->>Memory: 实体关系查询<br/>Neo4j Cypher
        Memory-->>Agent: 返回关联实体链
    end

    alt 需要工具调用（如查行情、搜文档）
        Agent->>Tool: 调用工具<br/>{ tool_name, parameters }
        Tool->>Tool: 执行外部 API 调用<br/>（Wind/Bloomberg/搜索引擎）
        Tool-->>Agent: 工具结果
        Agent->>FE: SSE event: tool_call<br/>{ tool, status: "running" }
    end

    Agent->>LLM: 构造最终 Prompt<br/>system + memories + tools_result + user_msg
    LLM-->>Agent: 流式 Token 输出

    loop 每个 Token Chunk
        Agent->>FE: SSE event: delta<br/>{ content_chunk }
        FE->>User: 实时渲染流式文字
    end

    Agent->>Memory: 异步写入长期记忆<br/>{ user_id, turn, summary, embedding }
    Memory->>Memory: 更新知识图谱实体
    Agent->>LS: 结束追踪，记录延迟/Token 用量

    Agent->>FE: SSE event: done<br/>{ message_id, usage, tool_calls }
    FE->>User: 渲染完整回复 + 工具调用详情
```

---

## 图3：数字人视频生成流水线

**说明：** 数字人视频生成是典型的长时异步任务（通常需要 3-10 分钟）。设计要点：API 立即返回 task_id，客户端通过 WebSocket 订阅任务状态，后端 Worker 独立处理生成逻辑并轮询 HeyGen，完成后通过 Redis Pub/Sub 触发 WebSocket 推送，避免前端轮询浪费资源。

```mermaid
sequenceDiagram
    actor User as 用户
    participant FE as Next.js 前端
    participant API as FastAPI<br/>/api/v1/avatars
    participant DB as PostgreSQL<br/>avatars 表
    participant Queue as Redis Queue<br/>avatar_tasks
    participant Worker as Avatar Worker<br/>(后台进程)
    participant HeyGen as HeyGen API
    participant S3 as Supabase Storage<br/>/ S3
    participant WS as WebSocket Gateway
    participant Pub as Redis Pub/Sub<br/>task_updates

    User->>FE: 填写脚本、选择数字人形象<br/>点击"生成视频"
    FE->>API: POST /api/v1/avatars/generate<br/>{ script, avatar_id, voice_id, language }
    API->>DB: INSERT avatars<br/>{ status: "pending", user_id, script }
    DB-->>API: task_id (UUID)
    API-->>FE: 202 Accepted<br/>{ task_id, status: "pending" }

    FE->>WS: WebSocket 连接<br/>订阅 task:{task_id}
    FE->>User: 显示"生成中"进度条

    API->>Queue: RPUSH avatar_tasks<br/>{ task_id, avatar_id, script, voice_id }

    Note over Worker: Worker 持续 BLPOP 监听队列

    Worker->>Queue: BLPOP avatar_tasks（阻塞等待）
    Queue-->>Worker: 取出任务 { task_id, ... }
    Worker->>DB: UPDATE status = "processing"
    Worker->>Pub: PUBLISH task_updates<br/>{ task_id, status: "processing", progress: 10 }
    Pub->>WS: 推送状态
    WS->>FE: ws message: { status: "processing", progress: 10 }
    FE->>User: 更新进度条 10%

    Worker->>HeyGen: POST /v2/video/generate<br/>{ script, avatar_id, voice_settings }
    HeyGen-->>Worker: { heygen_video_id, status: "pending" }
    Worker->>DB: UPDATE heygen_video_id

    loop 每隔 30 秒轮询（最多 20 次）
        Worker->>HeyGen: GET /v1/video_status/{heygen_video_id}
        HeyGen-->>Worker: { status, progress }

        alt 生成中
            Worker->>Pub: PUBLISH task_updates<br/>{ task_id, status: "processing", progress }
            Pub->>WS: 推送进度
            WS->>FE: ws message: { progress }
            FE->>User: 更新进度条
        else 生成完成
            HeyGen-->>Worker: { status: "completed", video_url }
            Worker->>S3: 下载并转存视频文件<br/>避免 HeyGen URL 过期
            S3-->>Worker: 内部存储 URL
            Worker->>DB: UPDATE status = "completed"<br/>video_url, completed_at
            Worker->>Pub: PUBLISH task_updates<br/>{ task_id, status: "completed", video_url }
        else 生成失败
            HeyGen-->>Worker: { status: "failed", error }
            Worker->>DB: UPDATE status = "failed", error_msg
            Worker->>Pub: PUBLISH task_updates<br/>{ task_id, status: "failed", error }
        end
    end

    Pub->>WS: 推送最终状态
    WS->>FE: ws message: { status: "completed", video_url }
    FE->>User: 隐藏进度条，显示视频播放器
    User->>FE: 点击播放，观看生成的数字人视频
```

---

## 图4：数据库 ERD（核心表关系）

**说明：** 以 `users` 表为中心的星形关系模型。`memories` 表使用 pgvector 的 `vector(1536)` 类型存储嵌入向量，支持 ANN 近似最近邻查询。`learner_events` 是事件溯源表，记录所有学习行为用于分析。`subscriptions` 控制功能访问权限和 API 用量上限。

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        string avatar_url
        timestamp created_at
    }

    user_profiles {
        uuid id PK
        uuid user_id FK
        string vertical
        jsonb preferences
        jsonb onboarding_state
    }

    memories {
        uuid id PK
        uuid user_id FK
        text content
        vector embedding
        float importance_score
        string memory_type
        timestamp created_at
        timestamp last_accessed_at
    }

    avatars {
        uuid id PK
        uuid user_id FK
        string name
        string heygen_avatar_id
        string status
        string video_url
        text script
        timestamp completed_at
    }

    research_notes {
        uuid id PK
        uuid user_id FK
        string title
        text content
        string[] tags
        jsonb source_refs
        timestamp updated_at
    }

    watchlists {
        uuid id PK
        uuid user_id FK
        string symbol
        string asset_type
        jsonb alert_config
        timestamp added_at
    }

    courses {
        uuid id PK
        uuid creator_id FK
        string title
        text description
        string status
        int lesson_count
        timestamp published_at
    }

    lessons {
        uuid id PK
        uuid course_id FK
        string title
        int order_index
        string content_type
        text content_url
        int duration_seconds
    }

    learner_events {
        uuid id PK
        uuid user_id FK
        uuid lesson_id FK
        string event_type
        jsonb payload
        timestamp occurred_at
    }

    subscriptions {
        uuid id PK
        uuid user_id FK
        string plan_id
        string status
        int monthly_token_limit
        timestamp expires_at
    }

    users ||--o{ user_profiles : "has"
    users ||--o{ memories : "owns"
    users ||--o{ avatars : "creates"
    users ||--o{ research_notes : "writes"
    users ||--o{ watchlists : "manages"
    users ||--o{ courses : "creator_id"
    users ||--o{ learner_events : "triggers"
    users ||--|| subscriptions : "holds"
    courses ||--o{ lessons : "contains"
    lessons ||--o{ learner_events : "generates"
```

---

## 图5：MemoryOS 混合检索流程

**说明：** MemoryOS 采用三阶段混合检索策略以兼顾精确性和召回率。第一阶段并行执行向量语义检索（pgvector HNSW 索引）和关键词精确检索（BM25），通过 RRF（Reciprocal Rank Fusion）算法融合双路结果；第二阶段用知识图谱扩展相关实体；第三阶段执行置信度过滤和时间衰减评分后返回 Top-K 结果。

```mermaid
flowchart LR
    INPUT["用户查询\nquery: string"]

    subgraph EMBED["嵌入处理"]
        EMB["文本嵌入\ntext-embedding-3-small\n→ vector(1536)"]
    end

    subgraph PARALLEL["并行检索（两路）"]
        direction TB
        VEC["向量语义检索\npgvector HNSW\ncosine similarity\nTop-20 候选"]
        BM25["关键词检索\nBM25 全文索引\nPostgreSQL tsvector\nTop-20 候选"]
    end

    subgraph FUSION["排名融合"]
        RRF["RRF 融合算法\nReciprocal Rank Fusion\nscore = Σ 1/(k + rank_i)\nk=60（标准参数）"]
    end

    subgraph FILTER["评分过滤"]
        CONF["置信度过滤\nmin_score ≥ 0.65\n低质量记忆剪枝"]
        DECAY["时间衰减\nscore × e^(-λ×days)\nλ=0.01（半衰期≈69天）\n近期记忆加权"]
        RERANK["综合评分\n0.6×relevance\n+ 0.2×importance\n+ 0.2×recency"]
    end

    subgraph GRAPH["知识图谱扩展"]
        NEO["Neo4j 实体查询\nCypher: MATCH (n)-[r*1..2]-(m)\n提取关联实体"]
        EXPAND["上下文扩展\n补充实体相关记忆\n填充知识空白"]
    end

    TOPK["Top-K 记忆片段\nK=5（默认）\n含相关性分值"]

    INPUT --> EMBED
    EMBED --> EMB
    EMB --> VEC
    INPUT --> BM25

    VEC --> RRF
    BM25 --> RRF

    RRF --> CONF
    CONF --> DECAY
    DECAY --> RERANK

    RERANK --> NEO
    NEO --> EXPAND

    EXPAND --> TOPK

    style INPUT fill:#dbeafe,stroke:#3b82f6
    style PARALLEL fill:#f0fdf4,stroke:#16a34a
    style FUSION fill:#fef9c3,stroke:#ca8a04
    style FILTER fill:#fef3c7,stroke:#f59e0b
    style GRAPH fill:#f3e8ff,stroke:#9333ea
    style TOPK fill:#dcfce7,stroke:#16a34a
```

---

## 图6：产品矩阵三层架构

**说明：** 从下往上读：底层是难以复制的核心壁垒（数据和 AI 能力），中间层是共享的 AI 平台基础设施，顶层是面向用户的差异化产品入口。数据从上层产品流向下层沉淀，AI 能力从下层向上层赋能，形成飞轮效应。两个垂直产品共享同一 AI 平台层，降低边际成本。

```mermaid
graph BT
    subgraph MOAT["壁垒层（核心资产）"]
        direction LR
        UD["用户数据资产\n行为数据·偏好·记忆\n持续积累难以迁移"]
        KG["领域知识图谱\n投资实体关系网络\n教育知识体系"]
        DM["数字人资产库\n定制形象·声音克隆\n个人品牌沉淀"]
        FM["Fine-tuned 模型\n垂直领域微调\n专有训练数据"]
    end

    subgraph PLATFORM["平台层（共享基础设施）"]
        direction LR
        MOS["MemoryOS\n用户记忆持久化\n混合检索引擎"]
        AOS["AgentOS\nLangGraph 工作流\n工具调用编排"]
        AVOS["AvatarOS\n数字人生成调度\n多引擎路由"]
        POS["PerceptOS\n多模态理解\n智能模型路由"]
    end

    subgraph ENTRY["入口层（用户产品）"]
        direction LR
        subgraph INVEST["InvestMind — 投资行业"]
            IF["信息流\n个性化资讯聚合"]
            RW["研究工作台\n深度分析·笔记"]
            IA["投资助手\n智能问答·策略"]
        end
        subgraph EDU["EduStar — 教育行业"]
            CF["课程工厂\nAI 辅助课程生成"]
            LP["学习平台\n自适应学习路径"]
            DA["数据分析\n学员行为洞察"]
        end
    end

    %% 平台层赋能入口层
    MOS -->|"个性化记忆赋能"| IF
    MOS -->|"学习记忆追踪"| LP
    AOS -->|"智能分析 Agent"| RW
    AOS -->|"课程生成 Agent"| CF
    AVOS -->|"数字人讲师"| CF
    AVOS -->|"分析师化身"| IA
    POS -->|"文档/图表理解"| RW
    POS -->|"多模态内容解析"| LP

    %% 壁垒层支撑平台层
    UD -->|"个性化训练数据"| MOS
    KG -->|"图谱增强检索"| MOS
    KG -->|"专业知识注入"| AOS
    DM -->|"数字人素材库"| AVOS
    FM -->|"垂直领域推理"| POS

    %% 入口层数据沉淀到壁垒层
    IF -.->|"行为数据回流"| UD
    RW -.->|"笔记沉淀知识图谱"| KG
    LP -.->|"学习行为分析"| UD
    DA -.->|"机构数据积累"| FM

    style MOAT fill:#fef3c7,stroke:#f59e0b,color:#000
    style PLATFORM fill:#f3e8ff,stroke:#9333ea,color:#000
    style ENTRY fill:#dbeafe,stroke:#3b82f6,color:#000
    style INVEST fill:#dcfce7,stroke:#16a34a,color:#000
    style EDU fill:#fee2e2,stroke:#dc2626,color:#000
```

---

*最后更新：2026-05-22 | 维护者：Architecture Team*
