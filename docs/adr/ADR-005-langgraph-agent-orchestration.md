# ADR-005: Agent 编排采用 LangGraph

## 状态
已采纳

## 背景

AgentOS 是 Drama Factory 平台的核心引擎，负责驱动 InvestMind 的多步投资分析工作流和 EduStar 的个性化学习路径规划。与简单的单轮问答不同，平台的核心 Agent 场景具有以下复杂性：

1. **多步任务规划**：一次投资研究可能需要 5-8 个步骤（获取行情 → 搜索新闻 → 分析财报 → 调用估值模型 → 综合判断 → 生成报告），每步的输入依赖上一步的输出，且步骤数在运行时动态决定。

2. **条件分支与循环**：Agent 需要根据中间结果改变执行路径（如：数据不足时触发额外搜索；生成的内容质量不达标时触发自我修正循环）。这种条件分支在简单的链式（Chain）设计中难以优雅实现。

3. **人机协作暂停（Human-in-the-Loop）**：某些场景需要 Agent 在执行关键操作前暂停并等待用户确认（如：生成课程大纲后等待教师审核再继续生成具体内容）。暂停点的状态需要持久化存储，以支持用户在几小时后继续工作流。

4. **并行执行**：部分步骤可以并行（如同时检索多个数据源），串行等待会显著增加延迟。

5. **工具调用可视化**：用户需要在前端实时看到 Agent 在做什么（类似 ChatGPT Plugins 的调用展示），这要求 Agent 执行过程中能流式地发出结构化的状态事件。

6. **错误恢复**：工具调用失败时，Agent 需要决策是重试、换一个工具、还是告知用户——这是复杂的状态转移逻辑，不是简单的 try-catch 可以处理的。

## 决策

选择 **LangGraph** 作为 Agent 编排框架。

核心实现模式：
- 每个 Agent 场景定义为一个 `StateGraph`，节点（Node）为具体的处理函数，边（Edge）为状态转移条件
- 使用 `MemorySaver`（生产环境用 PostgreSQL Checkpointer）持久化图状态，支持暂停/恢复
- 通过 `astream_events` API 流式获取节点执行事件，转换为 SSE 推送给前端
- 工具调用使用 LangGraph 的 `ToolNode` 标准化处理，包含统一的错误处理和重试逻辑

典型的 InvestMind 研究 Agent 图结构：

```
START
  └── intent_classifier         # 判断任务类型
        ├── (simple_qa)── llm_node ──→ END
        └── (research)──┐
                        ├── data_fetcher     # 并行：获取行情/新闻
                        ├── memory_recall    # 并行：召回相关记忆
                        └── join_node
                              └── analyst_node    # LLM分析
                                    ├── (need_more_data)──→ data_fetcher (循环)
                                    ├── (human_review)──→ INTERRUPT（暂停）
                                    └── (complete)──→ report_writer ──→ END
```

## 选项对比

| 选项 | 状态机支持 | Human-in-Loop | 并行执行 | 流式事件 | 调试工具 | 学习曲线 | 社区生态 |
|------|---------|--------------|---------|---------|---------|---------|---------|
| **LangGraph** | ⭐⭐⭐⭐⭐ 原生图状态机 | ⭐⭐⭐⭐⭐ INTERRUPT 原生支持 | ⭐⭐⭐⭐⭐ 原生并行节点 | ⭐⭐⭐⭐⭐ astream_events | ⭐⭐⭐⭐⭐ LangSmith Studio | 中高 | 增长最快 |
| **AutoGen（微软）** | ⭐⭐⭐ 基于消息传递 | ⭐⭐⭐ 需自定义 | ⭐⭐⭐ 多 Agent 并发 | ⭐⭐ 需适配 | ⭐⭐⭐ 有 Studio | 中 | 企业客户多 |
| **LangChain Agents（ReAct）** | ⭐⭐ 线性 ReAct 循环 | ⭐ 不支持 | ⭐⭐ 有限 | ⭐⭐⭐ 部分支持 | ⭐⭐⭐ | 低 | 成熟但老化 |
| **自研状态机（基于 Python asyncio）** | ⭐⭐⭐⭐⭐ 完全可控 | ⭐⭐⭐⭐⭐ 完全可控 | ⭐⭐⭐⭐⭐ asyncio 原生 | ⭐⭐⭐⭐⭐ 完全可控 | ⭐（需自建） | 极高（需自建所有） | 无 |
| **CrewAI** | ⭐⭐⭐ 角色导向 | ⭐⭐ 有限 | ⭐⭐⭐ 并行任务 | ⭐⭐⭐ | ⭐⭐ | 低 | 增长中 |
| **Semantic Kernel（微软）** | ⭐⭐⭐ Planner 模式 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | 中（.NET 为主） | 企业 .NET 生态 |

## 结论

选择 LangGraph 的核心理由是：**其图状态机模型与 AgentOS 的需求模型高度同构，避免了在其他框架上"对抗设计"的工程浪费**。

关键决策依据：

1. **Human-in-the-Loop 是硬需求**：LangGraph 的 `INTERRUPT` 机制是框架原生能力，只需在边定义中标记中断点，框架自动处理状态序列化和恢复。其他框架（如 AutoGen）实现同等能力需要大量自定义代码，且持久化方案不成熟。在评估测试中，用 AutoGen 实现相同的"生成大纲→等待审核→继续生成"流程需要约 500 行代码，而 LangGraph 只需约 80 行。

2. **LangSmith Studio 可视化图调试**：LangGraph 与 LangSmith 深度集成，每次 Agent 执行的图状态转移路径都可以在 LangSmith Studio 中可视化回放。这对于调试"Agent 为什么选择了 A 路径而不是 B 路径"这类问题极为高效。在 AutoGen 中类似的调试需要依赖日志文本，效率差几个量级。

3. **自研状态机的隐性成本**：自研状态机在技术上完全可行（Python asyncio + PostgreSQL 持久化），但需要自建：图执行引擎、状态序列化、并行节点协调、流式事件总线、断点续跑逻辑、可视化工具。保守估计工程量为 2-3 个月，且后续维护成本持续存在。而这些能力 LangGraph 已经提供并经过 Anthropic、OpenAI 等多家公司的生产验证。

4. **Checkpointer 解决持久化暂停**：LangGraph 的 `PostgresSaver` Checkpointer 将图状态序列化存入 PostgreSQL，这意味着用户可以在发起工作流的 24 小时后回来继续，服务器重启也不会丢失进行中的 Agent 任务。这是一个生产级功能，自研代价高。

5. **社区发展势头**：LangGraph 在 2024 年 Q1 后发展迅速，Anthropic 官方将其作为工具调用 Agent 的推荐编排方案，有大量参考实现和最佳实践可以复用。

## 后果

**正面影响：**
- `astream_events` 流式 API 与 SSE 推送结合，前端工具调用可视化的实现时间从预估的 2 周缩短到 3 天
- LangSmith 集成覆盖所有 Agent 执行，Token 用量、延迟、节点耗时全链路可观测
- Human-in-the-Loop 功能上线时间提前 6 周（相比自研路线）
- PostgreSQL Checkpointer 与现有 Supabase 数据库复用，零额外基础设施成本

**需要接受的负面影响：**
- **框架版本演进风险**：LangGraph 在 2024-2025 年间 API 变更频繁（从 0.x 到 1.x 有破坏性变更），需要投入精力跟踪版本升级和适配。建议锁定次版本号（`langgraph>=0.2,<0.3`）并在独立测试环境验证后再升级。
- **抽象层学习曲线**：图状态机的心智模型与普通 Python 代码差异较大，新团队成员上手 LangGraph 需要约 1 周时间，调试复杂图的跨节点状态问题需要学习 LangSmith 工具。
- **图执行开销**：对于简单的单轮问答，LangGraph 的节点调度开销（约 10-20ms）相比直接调用 LLM 有额外延迟。解决方案：在 `intent_classifier` 节点快速判断，简单问答绕过完整图直接走轻量路径。
- **供应商耦合**：如果未来 LangChain/LangGraph 商业模式调整（如强制 LangSmith 付费才能使用全部特性），需要评估解耦成本。缓解措施：AgentOS 内部对 LangGraph 做了适配层封装，对上层业务代码屏蔽框架细节，替换框架的改动范围控制在 AgentOS 模块内部。
