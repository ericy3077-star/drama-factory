"""InvestMind API routes."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import CurrentUserId, DBSession
from app.verticals.invest import service
from app.verticals.invest.chat import chat_stream
from app.verticals.invest.schemas import (
    AgentTaskRequest,
    AgentTaskResponse,
    FeedItemSchema,
    FeedRequest,
    ResearchNote,
    ResearchNoteCreate,
    ResearchNoteUpdate,
    ResearchReport,
    ResearchRequest,
    WatchlistItem,
    WatchlistItemCreate,
)

log = structlog.get_logger()

# ── Quota helpers ─────────────────────────────────────────────────────────────

_FREE_TIER_DAILY_LIMIT = 50


async def check_chat_quota(session: AsyncSession, user_id: str) -> None:
    """Raise HTTP 402 if the user has exhausted their free daily chat quota.

    Gracefully degrades when the usage_events table does not yet exist or the
    query fails for any other reason — we never block the user due to infra issues.
    """
    try:
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        result = await session.execute(
            text(
                "SELECT COUNT(*) FROM usage_events "
                "WHERE user_id = :uid AND created_at > :today"
            ),
            {"uid": user_id, "today": today_start},
        )
        count: int = result.scalar_one_or_none() or 0
        if count >= _FREE_TIER_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="每日对话配额已用尽，请升级 Pro 解锁无限对话",
            )
    except HTTPException:
        raise
    except Exception:
        # Table may not exist yet — allow through
        log.warning("invest.quota_check.failed", user_id=user_id, exc_info=True)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    history: list[dict[str, str]] = Field(default_factory=list)


# ── Chat (memory-augmented agentic SSE) ──────────────────────────────────────

@router.post("/chat")
async def invest_chat(
    request: ChatRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> StreamingResponse:
    await check_chat_quota(session, user_id)
    return StreamingResponse(
        chat_stream(session, user_id, request.message, request.history),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Watchlist ─────────────────────────────────────────────────────────────────

@router.get("/watchlist", response_model=list[WatchlistItem])
async def list_watchlist(user_id: CurrentUserId, session: DBSession) -> list[WatchlistItem]:
    return await service.get_watchlist(session, user_id)


@router.post("/watchlist", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
async def add_watchlist_item(
    data: WatchlistItemCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> WatchlistItem:
    return await service.add_to_watchlist(session, user_id, data)


@router.delete("/watchlist/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_watchlist_item(
    symbol: str,
    user_id: CurrentUserId,
    session: DBSession,
) -> None:
    removed = await service.remove_from_watchlist(session, user_id, symbol)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not in watchlist")


# ── Research notes ────────────────────────────────────────────────────────────

@router.get("/notes", response_model=list[ResearchNote])
async def list_notes(
    user_id: CurrentUserId,
    session: DBSession,
    symbol: str | None = None,
    limit: int = 50,
) -> list[ResearchNote]:
    return await service.list_research_notes(session, user_id, symbol, limit)


@router.post("/notes", response_model=ResearchNote, status_code=status.HTTP_201_CREATED)
async def create_note(
    data: ResearchNoteCreate,
    user_id: CurrentUserId,
    session: DBSession,
) -> ResearchNote:
    return await service.create_research_note(session, user_id, data)


@router.patch("/notes/{note_id}", response_model=ResearchNote)
async def update_note(
    note_id: UUID,
    data: ResearchNoteUpdate,
    user_id: CurrentUserId,
    session: DBSession,
) -> ResearchNote:
    note = await service.update_research_note(session, user_id, note_id, data)
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


# ── Feed ──────────────────────────────────────────────────────────────────────

@router.post("/feed", response_model=list[FeedItemSchema])
async def get_feed(
    request: FeedRequest,
    user_id: CurrentUserId,
    session: DBSession,
) -> list[FeedItemSchema]:
    return await service.get_feed(session, user_id, request)


# ── Research ──────────────────────────────────────────────────────────────────

_MOCK_RESEARCH_REPORTS: list[ResearchReport] = [
    ResearchReport(
        symbol="NVDA",
        company_name="NVIDIA Corporation",
        summary=(
            "英伟达在 AI 算力基础设施领域保持绝对领导地位。数据中心业务营收同比增长 409%，"
            "H100/H200 GPU 供不应求，未来 Blackwell 架构产品周期有望延续高速增长。"
            "估值处于历史高位，短期回调风险存在，但中长期 AI 资本开支浪潮将持续受益。"
        ),
        current_price=875.40,
        key_ratios={
            "PE": 68.2,
            "PS": 32.1,
            "EV_EBITDA": 54.7,
            "gross_margin": "74.6%",
            "revenue_growth_yoy": "409%",
            "free_cash_flow_ttm": "$26.9B",
            "analyst_target_price": 950.0,
            "buy_rating_pct": "92%",
        },
        recent_news=[
            {
                "title": "英伟达 Q4 营收 221 亿美元，超出市场预期 18%",
                "url": "https://example.com/nvda-q4",
                "sentiment": "positive",
            },
            {
                "title": "Blackwell GPU 量产爬坡顺利，台积电 CoWoS 产能保障充足",
                "url": "https://example.com/nvda-blackwell",
                "sentiment": "positive",
            },
            {
                "title": "美国对华 AI 芯片出口管制升级，影响英伟达中国市场约 15% 营收",
                "url": "https://example.com/nvda-china",
                "sentiment": "negative",
            },
        ],
        risks=[
            "出口管制政策收紧可能削减中国市场份额",
            "AMD MI300X 及定制 ASIC（Google TPU、AWS Trainium）竞争加剧",
            "估值过高，PE>60x 对利率敏感",
            "台积电先进封装产能瓶颈可能制约出货",
        ],
        opportunities=[
            "全球 AI 数据中心建设投资预计 2025-2027 年 CAGR > 35%",
            "推理端算力需求爆发，H200/Blackwell 单价更高",
            "CUDA 生态护城河深厚，软件壁垒难以复制",
            "汽车自动驾驶与机器人新兴业务提供第二增长曲线",
        ],
        generated_at=datetime(2026, 5, 28, 9, 30, 0, tzinfo=timezone.utc),
    ),
    ResearchReport(
        symbol="BYD",
        company_name="比亚迪股份有限公司",
        summary=(
            "比亚迪是全球新能源汽车销量冠军，刀片电池与 DM5.0 混动技术构建强大护城河。"
            "2025 年海外销量加速突破，东南亚、巴西、欧洲市场持续放量。"
            "电池垂直整合优势叠加规模效应，单车毛利率持续改善。"
            "关注欧盟反补贴关税落地进度及人民币汇率波动风险。"
        ),
        current_price=298.50,
        key_ratios={
            "PE": 22.4,
            "PS": 0.9,
            "EV_EBITDA": 14.2,
            "gross_margin": "21.9%",
            "revenue_growth_yoy": "28%",
            "new_energy_sales_monthly": "420,000辆",
            "analyst_target_price": 360.0,
            "buy_rating_pct": "78%",
        },
        recent_news=[
            {
                "title": "比亚迪 4 月新能源销量 42 万辆，同比增长 51%",
                "url": "https://example.com/byd-april",
                "sentiment": "positive",
            },
            {
                "title": "海豹 U DM 登陆巴西市场，首月订单超 8000 台",
                "url": "https://example.com/byd-brazil",
                "sentiment": "positive",
            },
            {
                "title": "欧盟最终确认对比亚迪加征 17.4% 反补贴关税",
                "url": "https://example.com/byd-eu-tariff",
                "sentiment": "negative",
            },
        ],
        risks=[
            "欧盟反补贴关税侵蚀欧洲市场利润空间",
            "国内价格战持续，行业整体盈利承压",
            "锂价下行周期中电池业务毛利率面临压力",
            "人民币升值对出口竞争力的潜在影响",
        ],
        opportunities=[
            "全球新能源渗透率提升，2026 年预计超 40%",
            "东南亚建厂本土化生产规避关税壁垒",
            "仰望高端品牌溢价与海洋网产品矩阵持续完善",
            "储能业务高速增长，成为新的利润来源",
        ],
        generated_at=datetime(2026, 5, 27, 8, 0, 0, tzinfo=timezone.utc),
    ),
    ResearchReport(
        symbol="AI-SECTOR",
        company_name="人工智能行业全景分析",
        summary=(
            "2026 年 AI 行业进入应用落地加速期。大模型能力趋于商品化，竞争焦点从参数量转向"
            "推理效率、垂直场景深度整合和企业级安全合规。RAG+Agent 架构成为企业 AI 落地主流路径，"
            "国内厂商在中文语料和本土监管合规方面具备差异化优势。"
            "预计 2026 年中国 AI 应用市场规模突破 4000 亿元，同比增速 62%。"
        ),
        current_price=None,
        key_ratios={
            "market_size_2026E": "¥4,000亿",
            "yoy_growth": "62%",
            "key_sub_sectors": "大模型API/Agent应用/AI基础设施/垂直SaaS",
            "top_players": "百度/阿里/字节/华为/科大讯飞",
            "vc_investment_2025": "$180亿",
            "enterprise_adoption_rate": "34%",
        },
        recent_news=[
            {
                "title": "DeepSeek R2 发布，推理成本较 GPT-4o 降低 95%",
                "url": "https://example.com/deepseek-r2",
                "sentiment": "positive",
            },
            {
                "title": "国家数据局发布 AI 数据合规新规，明确训练数据权属",
                "url": "https://example.com/ai-regulation",
                "sentiment": "neutral",
            },
            {
                "title": "阿里云百炼平台 API 调用量突破日均千亿次",
                "url": "https://example.com/aliyun-bailian",
                "sentiment": "positive",
            },
        ],
        risks=[
            "大模型能力同质化加剧，价格战侵蚀上游 API 利润",
            "监管政策不确定性，算法备案与数据合规成本上升",
            "算力瓶颈制约国内厂商训练更大规模模型的速度",
            "海外先进模型封锁风险",
        ],
        opportunities=[
            "政务、金融、医疗等高价值垂直行业大规模采购启动",
            "端侧推理芯片成熟推动 AI 手机/PC 渗透率跃升",
            "AI Agent 自动化工作流替代传统 RPA，市场规模超千亿",
            "中国 AI 出海：东南亚、中东、拉美市场竞争窗口",
        ],
        generated_at=datetime(2026, 5, 26, 10, 0, 0, tzinfo=timezone.utc),
    ),
]


@router.get("/research", response_model=list[ResearchReport])
async def list_research_reports(
    user_id: CurrentUserId,
) -> list[ResearchReport]:
    """Return a list of pre-generated research reports (demo data)."""
    return _MOCK_RESEARCH_REPORTS


@router.post("/research", response_model=ResearchReport)
async def research_stock(
    request: ResearchRequest,
    user_id: CurrentUserId,
) -> ResearchReport:
    return await service.run_research(request)


# ── Agent ─────────────────────────────────────────────────────────────────────

@router.post("/agent", response_model=AgentTaskResponse)
async def run_agent(
    request: AgentTaskRequest,
    user_id: CurrentUserId,
) -> AgentTaskResponse:
    return await service.run_invest_agent(user_id, request.task, request.context)


@router.post("/agent/stream")
async def stream_agent(
    request: AgentTaskRequest,
    user_id: CurrentUserId,
) -> StreamingResponse:
    import json
    from app.platform.agent.orchestrator import agent_orchestrator

    async def event_stream():  # type: ignore[return]
        async for update in agent_orchestrator.stream(user_id, request.task, "invest", request.context):
            yield f"data: {json.dumps(update)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
