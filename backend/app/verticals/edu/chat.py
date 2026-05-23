"""EduStar — memory-augmented agentic streaming chat."""
from __future__ import annotations

import json
import time
from collections.abc import AsyncGenerator
from typing import Any

import anthropic
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.platform.memory.engine import memory_engine

log = structlog.get_logger()

# ── Tool definitions ──────────────────────────────────────────────────────────

EDU_TOOLS: list[dict[str, Any]] = [
    {
        "name": "recall_memories",
        "description": (
            "Search the user's teaching knowledge base for past course designs, "
            "lesson plans, learner feedback, and pedagogy notes. Always call this "
            "before designing new content for a topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "save_teaching_insight",
        "description": (
            "Save a teaching methodology insight, learner pattern, or course design "
            "decision to permanent memory. Use proactively when the conversation "
            "surfaces a valuable pedagogical conclusion."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "topic": {"type": "string", "description": "Subject area or course name"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "generate_lesson_outline",
        "description": (
            "Generate a structured lesson outline with learning objectives, key points, "
            "exercises, and estimated timing for a given topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Lesson topic"},
                "target_audience": {
                    "type": "string",
                    "description": "Who the learners are, e.g. '初级Python学员', '销售新人'",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Target lesson length in minutes",
                    "default": 30,
                },
                "style": {
                    "type": "string",
                    "description": "Teaching style: lecture / workshop / case-study / flipped",
                    "default": "lecture",
                },
            },
            "required": ["topic", "target_audience"],
        },
    },
    {
        "name": "generate_script_segment",
        "description": (
            "Write a narration script segment for a digital-human lecture video. "
            "Output is optimized for TTS and HeyGen avatar delivery: "
            "clear sentence breaks, no markdown, natural speaking pace."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content_point": {
                    "type": "string",
                    "description": "The key point or concept to explain",
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Target speaking duration in seconds (150 words ≈ 60s)",
                    "default": 60,
                },
                "tone": {
                    "type": "string",
                    "description": "Tone: professional / friendly / energetic",
                    "default": "friendly",
                },
            },
            "required": ["content_point"],
        },
    },
]

_SYSTEM_TEMPLATE = """\
你是 EduStar 助手，专门帮助知识付费讲师和企业培训师创作高质量课程内容。

你的核心能力：
- 调取讲师历史课程设计和教学洞察（recall_memories）—— **设计新内容前必须先调用**
- 保存重要教学方法和学员反馈（save_teaching_insight）—— 主动积累教学知识库
- 生成结构化课程大纲（generate_lesson_outline）
- 生成数字人视频旁白脚本（generate_script_segment）—— 为 HeyGen 优化，口语化表达

工作原则：
- 内容要有层次感：先建立Why，再讲What，最后给How
- 脚本语言口语化，避免书面腔，适合数字人播报
- 好的课程设计从学员的痛点出发，不从知识点出发
- 主动利用讲师历史经验，减少重复建设

{memory_context}\
"""


# ── Tool executor ─────────────────────────────────────────────────────────────

async def _execute_tool(
    name: str,
    tool_input: dict[str, Any],
    session: AsyncSession,
    user_id: str,
) -> Any:
    if name == "recall_memories":
        mems = await memory_engine.recall(
            session, user_id, tool_input["query"], top_k=tool_input.get("top_k", 5)
        )
        return [m.to_dict() for m in mems]

    if name == "save_teaching_insight":
        await memory_engine.store(
            session,
            user_id,
            tool_input["content"],
            content_type="teaching_insight",
            topic=tool_input.get("topic"),
        )
        return {"saved": True, "preview": tool_input["content"][:120]}

    if name == "generate_lesson_outline":
        return await _ai_lesson_outline(tool_input)

    if name == "generate_script_segment":
        return await _ai_script_segment(tool_input)

    return {"error": f"unknown tool: {name}"}


async def _ai_lesson_outline(params: dict[str, Any]) -> dict[str, Any]:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = (
        f"为以下课程生成结构化大纲，以JSON返回。\n\n"
        f"主题: {params['topic']}\n"
        f"目标学员: {params['target_audience']}\n"
        f"课程时长: {params.get('duration_minutes', 30)} 分钟\n"
        f"教学风格: {params.get('style', 'lecture')}\n\n"
        "返回JSON格式:\n"
        "{\n"
        '  "title": "课程标题",\n'
        '  "learning_objectives": ["目标1", "目标2"],\n'
        '  "sections": [\n'
        '    {"title": "章节标题", "key_points": ["要点"], "duration_minutes": 5, "activities": ["活动"]}\n'
        "  ],\n"
        '  "assessment": "考核方式"\n'
        "}"
    )
    msg = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text  # type: ignore[union-attr]
    try:
        start, end = text.find("{"), text.rfind("}") + 1
        return json.loads(text[start:end])
    except Exception:
        return {"raw": text}


async def _ai_script_segment(params: dict[str, Any]) -> dict[str, Any]:
    seconds = params.get("duration_seconds", 60)
    word_target = int(seconds * 2.5)  # ~150 words/min Chinese
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    prompt = (
        f"写一段数字人视频的旁白脚本，语言口语化，适合TTS朗读。\n\n"
        f"内容要点: {params['content_point']}\n"
        f"语气风格: {params.get('tone', 'friendly')}\n"
        f"目标字数: 约{word_target}字\n\n"
        "要求：\n"
        "- 不用markdown标记\n"
        "- 自然的说话节奏，短句为主\n"
        "- 开头直接进入主题，不要'大家好'之类的套话\n"
        "- 结尾有一个自然的收尾"
    )
    msg = await client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    script = msg.content[0].text  # type: ignore[union-attr]
    return {
        "script": script,
        "estimated_seconds": int(len(script) / 2.5),
        "word_count": len(script),
    }


# ── SSE helper ────────────────────────────────────────────────────────────────

def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# ── Core streaming generator ──────────────────────────────────────────────────

async def chat_stream(
    session: AsyncSession,
    user_id: str,
    message: str,
    history: list[dict[str, str]],
) -> AsyncGenerator[str, None]:
    """
    Memory-augmented agentic chat for EduStar.

    Same agentic loop as InvestMind, but with edu-domain tools.
    """
    memories = await memory_engine.recall(session, user_id, message, top_k=5)
    memory_context = ""
    if memories:
        lines = [f"- [{m.topic or '通用'}] {m.content[:300]}" for m in memories]
        memory_context = "【自动召回的历史教学记录，供参考】\n" + "\n".join(lines) + "\n"

    system = _SYSTEM_TEMPLATE.format(memory_context=memory_context)

    msgs: list[dict[str, Any]] = [
        {"role": h["role"], "content": h["content"]}
        for h in history[-20:]
    ]
    msgs.append({"role": "user", "content": message})

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    full_response = ""

    while True:
        pending_tools: dict[str, dict[str, Any]] = {}
        current_tool_id: str | None = None

        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            tools=EDU_TOOLS,  # type: ignore[arg-type]
            messages=msgs,
        ) as stream:
            async for event in stream:
                etype = event.type

                if etype == "content_block_start":
                    block = event.content_block
                    if block.type == "tool_use":
                        current_tool_id = block.id
                        pending_tools[block.id] = {
                            "name": block.name,
                            "input_str": "",
                            "input": {},
                            "start_time": time.monotonic(),
                        }
                        yield _sse({
                            "type": "tool_use",
                            "id": block.id,
                            "name": block.name,
                            "input": {},
                            "status": "running",
                        })

                elif etype == "content_block_delta":
                    delta = event.delta
                    if delta.type == "text_delta":
                        full_response += delta.text
                        yield _sse({"type": "content_delta", "delta": {"text": delta.text}})
                    elif delta.type == "input_json_delta" and current_tool_id:
                        pending_tools[current_tool_id]["input_str"] += delta.partial_json

                elif etype == "content_block_stop":
                    if current_tool_id and current_tool_id in pending_tools:
                        try:
                            pending_tools[current_tool_id]["input"] = json.loads(
                                pending_tools[current_tool_id]["input_str"]
                            )
                        except Exception:
                            pass
                        current_tool_id = None

            final_msg = await stream.get_final_message()

        if final_msg.stop_reason != "tool_use":
            break

        assistant_content: list[dict[str, Any]] = []
        for block in final_msg.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
        msgs.append({"role": "assistant", "content": assistant_content})

        tool_results: list[dict[str, Any]] = []
        for tool_id, info in pending_tools.items():
            try:
                result = await _execute_tool(info["name"], info["input"], session, user_id)
                status = "completed"
            except Exception as exc:
                result = {"error": str(exc)}
                status = "failed"
                log.error("edu_chat.tool_failed", tool=info["name"], error=str(exc))

            duration_ms = int((time.monotonic() - info["start_time"]) * 1000)
            yield _sse({
                "type": "tool_use",
                "id": tool_id,
                "name": info["name"],
                "input": info["input"],
                "status": status,
                "output": result,
                "duration_ms": duration_ms,
            })
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })

        msgs.append({"role": "user", "content": tool_results})

    if full_response and len(full_response) > 80:
        summary = f"Q: {message[:200]}\nA: {full_response[:600]}"
        await memory_engine.store(
            session, user_id, summary, content_type="conversation"
        )

    yield "data: [DONE]\n\n"
