# ADR-003: 数据库选 Supabase（PostgreSQL + pgvector）

## 状态
已采纳

## 背景

Drama Factory 的数据层面临独特的多元需求，不同于典型的纯关系型业务：

1. **关系型数据**：用户表、课程/课时、订阅计费、观察列表等标准 CRUD 业务数据，需要事务完整性和复杂 JOIN 查询。
2. **向量数据**：MemoryOS 需要存储用户记忆的嵌入向量（1536 维，text-embedding-3-small），支持近似最近邻（ANN）语义检索。预估 18 个月内，每活跃用户平均积累 500 条记忆，10万用户规模下需存储约 5000万维度的向量数据。
3. **认证系统**：需要支持 Email/Password、OAuth（Google/GitHub）、JWT 签发和刷新，以及 Row Level Security（RLS）策略。
4. **文件存储**：用户上传的课程素材、数字人视频文件、研报 PDF，需要可靠的对象存储和 CDN 加速。
5. **实时订阅**：前端需要监听数据库变更（如数字人任务状态更新），用于实时 UI 更新。

早期评估时，团队需要在 **减少自建基础设施** 和 **保留未来扩展能力** 之间找到平衡点。

## 决策

选择 **Supabase** 作为一体化数据平台：
- PostgreSQL 15 作为主数据库
- pgvector 扩展处理向量检索（HNSW 索引）
- Supabase Auth 处理用户认证和 RLS
- Supabase Storage 处理文件对象存储
- Supabase Realtime 处理数据库变更订阅

补充组件：
- **Neo4j**（独立部署）：处理知识图谱的实体关系查询，pgvector 不擅长图遍历场景
- **Redis**（独立部署）：任务队列（BullMQ）+ 会话缓存 + WebSocket 状态，高频读写场景

## 选项对比

| 方案 | 向量检索 | 关系查询 | Auth | 文件存储 | 运维复杂度 | 规模上限 | 成本（月） |
|------|---------|---------|------|---------|-----------|---------|-----------|
| **Supabase（PostgreSQL + pgvector）** | HNSW ANN，中等性能 | 完整 SQL | 内置 Auth + RLS | 内置 Storage + CDN | 极低（托管服务） | ~500万向量（pgvector 推荐） | $25-100（成长期） |
| **Pinecone + 独立 PostgreSQL** | 专用向量引擎，高性能 | 完整 SQL | 自建或第三方 | 自建 S3 | 中（两套系统同步） | 10亿+向量 | $70+（Pinecone Starter） |
| **Weaviate（全托管）** | 原生向量 + 图混合 | 有限 GraphQL | 需外部集成 | 需外部 S3 | 中低 | 高 | $100+（WCS） |
| **Qdrant + PostgreSQL** | 高性能，Rust 实现 | 完整 SQL | 自建 | 自建 S3 | 中高（4 个系统） | 极高 | 按量计费 |
| **全自建（PG + pgvector + MinIO + Keycloak）** | 中等 | 完整 SQL | Keycloak | MinIO | 极高 | 取决于硬件 | 低（但人力成本高） |

**pgvector vs 专用向量数据库性能对比（1M 向量，1536维）：**

| 指标 | pgvector HNSW | Pinecone | Qdrant |
|------|--------------|---------|-------|
| 查询延迟（P99） | ~50ms | ~10ms | ~15ms |
| 吞吐量（QPS） | ~500 | ~5000 | ~3000 |
| 精确率（Recall@10） | ~95% | ~99% | ~98% |

## 结论

选择 Supabase 的核心逻辑是：**在 500万向量规模以下，一体化平台节省的运维成本远超专用向量数据库的性能优势**。

关键决策依据：

1. **规模判断**：产品 PMF 验证阶段（0-10万用户），内存向量量级不超过 500万条，pgvector HNSW 完全满足需求，50ms P99 延迟在 RAG 场景下可接受（LLM 推理本身延迟已在秒级）。

2. **运维成本量化**：如果选择 Pinecone + PG + Clerk + S3 四套系统，需要处理向量与关系数据的一致性同步（用户删除时需同时删除 PG 和 Pinecone 中的数据）、四套监控、四套计费。团队规模下，这些运维工作预计占用 30% 的工程时间。

3. **RLS 是关键特性**：Supabase 的 Row Level Security 与 Auth 深度集成，可以在数据库层面强制执行 `user_id = auth.uid()` 的数据隔离，而不需要在每个 API 端点手动添加过滤条件，大幅降低数据泄漏风险。

4. **迁移路径清晰**：如果未来向量规模超过 500万，可以将 `memories` 表的向量列迁移到专用 Pinecone，而其他业务数据保留在 PostgreSQL，迁移边界清晰。

## 后果

**正面影响：**
- 开发者体验极佳：Supabase Dashboard 提供 SQL 编辑器、向量可视化、Auth 管理、存储浏览器，大幅降低运维认知负担
- RLS 策略统一管理用户数据隔离，安全性高且代码侵入小
- Supabase Realtime 为 WebSocket 推送提供了额外的备用方案（补充 Redis Pub/Sub）
- pgvector 与业务数据在同一事务中操作，避免双写一致性问题（如插入记忆时同时写向量和元数据）

**需要接受的负面影响：**
- **pgvector 在高并发下性能瓶颈**：当向量检索 QPS 超过 500 时，PostgreSQL 的连接池和 HNSW 索引会成为瓶颈。届时需要引入专用向量数据库或使用 pgvector 的分片方案。
- **Supabase 供应商锁定**：Supabase Auth、Storage API、Realtime 协议都有一定的 Supabase 私有实现，完全迁移到自建 PG 需要替换这些组件。
- **Neo4j 独立运维**：知识图谱需求无法用 pgvector 满足，仍需维护独立的 Neo4j 实例，是本方案中唯一的"异构数据库"。

**性能优化预案：**
- 当 `memories` 表超过 100万行时，启用 pgvector 的 HNSW 参数调优（`m=16, ef_construction=64`）
- 对向量检索添加 `user_id` 前置过滤，将全局搜索空间缩小到单用户维度
- 当 P99 延迟超过 100ms 时，启动向量数据库迁移评估
