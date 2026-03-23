"""DeepSeek AI service: quick chat + deep analysis with portfolio context."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import date, datetime, timedelta
from decimal import Decimal

from openai import AsyncOpenAI
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai_conversation import AIConversation
from app.models.holding import Holding

logger = logging.getLogger(__name__)

DISCLAIMER = "\n\n---\n*以上内容仅供参考，不构成投资建议。*"


def _get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.DEEPSEEK_API_KEY,
        base_url=settings.DEEPSEEK_BASE_URL,
    )


async def _build_portfolio_context(db: AsyncSession) -> str:
    """Build a text summary of current holdings for AI context."""
    result = await db.execute(select(Holding))
    holdings = result.scalars().all()

    if not holdings:
        return "用户当前没有任何持仓。"

    lines = ["用户当前持仓如下：", ""]
    total_cost = Decimal("0")
    total_value = Decimal("0")

    for h in holdings:
        cost = h.quantity * h.cost_price
        total_cost += cost
        if h.latest_price is not None:
            mv = h.quantity * h.latest_price
            pnl = mv - cost
            pnl_pct = (pnl / cost * 100) if cost > 0 else Decimal("0")
            price_info = f"最新价 {h.latest_price}"
            if h.latest_price_updated_at:
                price_info += f"（{h.latest_price_updated_at.strftime('%m-%d %H:%M')} 更新）"
            lines.append(
                f"- {h.name}（{h.symbol}，{h.asset_type}）：持有 {h.quantity} 份，"
                f"成本价 {h.cost_price}，{price_info}，"
                f"市值 {mv:.2f}，盈亏 {pnl:+.2f}（{pnl_pct:+.2f}%）"
            )
            total_value += mv
        else:
            lines.append(
                f"- {h.name}（{h.symbol}，{h.asset_type}）：持有 {h.quantity} 份，"
                f"成本价 {h.cost_price}，暂无最新行情"
            )
            total_value += cost

    lines.append("")
    profit = total_value - total_cost
    lines.append(f"总成本 {total_cost:.2f}，总市值 {total_value:.2f}，总盈亏 {profit:+.2f}")

    return "\n".join(lines)


SYSTEM_PROMPT_QUICK = """你是"齐家"家庭投资助手的 AI 分析师。
你的角色是帮助普通家庭理解和分析他们的投资组合。

规则：
1. 用通俗易懂的中文回答，避免过于专业的术语
2. 回答要简洁实用，直击要点
3. 基于用户的实际持仓数据给出分析
4. 永远不要给出具体的买卖时机建议
5. 所有回复末尾必须注明"以上内容仅供参考，不构成投资建议"

以下是用户的持仓情况：
{portfolio_context}
"""


DEEP_ANALYSIS_PROMPTS = {
    "fundamental": """你是一位基本面分析师。请从基本面角度分析用户的提问。
重点关注：公司/基金的财务状况、行业前景、估值水平、竞争优势等。

用户持仓：
{portfolio_context}

用户提问：{question}

请给出基本面角度的分析（300-500字）。""",

    "technical": """你是一位技术面分析师。请从技术面角度分析用户的提问。
重点关注：价格趋势、成交量变化、关键支撑/阻力位、技术指标信号等。

用户持仓：
{portfolio_context}

用户提问：{question}

请给出技术面角度的分析（300-500字）。""",

    "risk": """你是一位风险管理分析师。请从风险角度分析用户的提问。
重点关注：下行风险、仓位集中度、市场系统性风险、流动性风险等。

用户持仓：
{portfolio_context}

用户提问：{question}

请给出风险角度的分析（300-500字）。""",

    "summary": """你是"齐家"家庭投资助手的首席分析师。
请根据以下三个角度的分析结果，给出一个综合结论。

用户提问：{question}

基本面分析：
{fundamental}

技术面分析：
{technical}

风险分析：
{risk}

请给出：
1. 总体建议（2-3句话）
2. 各角度要点汇总
3. 风险提示

格式要求：用 markdown 格式，结构清晰。
末尾必须注明"以上内容仅供参考，不构成投资建议"。""",
}


async def check_daily_limit(db: AsyncSession, user_id) -> bool:
    """Check if user has exceeded daily AI usage limit."""
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = await db.execute(
        select(func.count(AIConversation.id)).where(
            AIConversation.user_id == user_id,
            AIConversation.created_at >= today_start,
        )
    )
    count = result.scalar() or 0
    return count < settings.AI_DAILY_LIMIT


async def quick_chat_stream(
    db: AsyncSession,
    user_id,
    question: str,
) -> AsyncGenerator[str, None]:
    """Quick chat with streaming response."""
    if not settings.DEEPSEEK_API_KEY:
        yield "data: " + json.dumps({"error": "AI 服务未配置，请设置 DEEPSEEK_API_KEY"}) + "\n\n"
        return

    if not await check_daily_limit(db, user_id):
        yield "data: " + json.dumps({"error": "今日对话次数已达上限（100次）"}) + "\n\n"
        return

    portfolio_context = await _build_portfolio_context(db)
    system_prompt = SYSTEM_PROMPT_QUICK.format(portfolio_context=portfolio_context)

    client = _get_client()
    full_answer = ""

    try:
        stream = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
            stream=True,
            max_tokens=4096,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_answer += delta.content
                yield "data: " + json.dumps({"content": delta.content}) + "\n\n"

        full_answer += DISCLAIMER
        yield "data: " + json.dumps({"content": DISCLAIMER}) + "\n\n"

        conversation = AIConversation(
            user_id=user_id,
            mode="quick",
            question=question,
            answer=full_answer,
        )
        db.add(conversation)
        await db.commit()

        yield "data: " + json.dumps({"done": True}) + "\n\n"

    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        yield "data: " + json.dumps({"error": f"AI 服务暂时不可用，请稍后再试"}) + "\n\n"


async def deep_analysis_stream(
    db: AsyncSession,
    user_id,
    question: str,
) -> AsyncGenerator[str, None]:
    """Deep analysis with multi-perspective approach and progress updates."""
    if not settings.DEEPSEEK_API_KEY:
        yield "data: " + json.dumps({"error": "AI 服务未配置，请设置 DEEPSEEK_API_KEY"}) + "\n\n"
        return

    if not await check_daily_limit(db, user_id):
        yield "data: " + json.dumps({"error": "今日对话次数已达上限（100次）"}) + "\n\n"
        return

    portfolio_context = await _build_portfolio_context(db)
    client = _get_client()

    perspectives = [
        ("fundamental", "正在分析基本面..."),
        ("technical", "正在分析技术面..."),
        ("risk", "正在分析风险..."),
    ]

    results = {}

    for key, progress_msg in perspectives:
        yield "data: " + json.dumps({"progress": progress_msg}) + "\n\n"

        prompt = DEEP_ANALYSIS_PROMPTS[key].format(
            portfolio_context=portfolio_context,
            question=question,
        )

        try:
            response = await client.chat.completions.create(
                model=settings.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.AI_DEEP_MAX_TOKENS // 4,
            )
            results[key] = response.choices[0].message.content or ""
        except Exception as e:
            logger.warning(f"Deep analysis {key} failed: {e}")
            label = {"fundamental": "基本面", "technical": "技术面", "risk": "风险"}[key]
            results[key] = f"（{label}分析暂不可用）"

    yield "data: " + json.dumps({"progress": "正在汇总结论..."}) + "\n\n"

    summary_prompt = DEEP_ANALYSIS_PROMPTS["summary"].format(
        question=question,
        fundamental=results.get("fundamental", "暂不可用"),
        technical=results.get("technical", "暂不可用"),
        risk=results.get("risk", "暂不可用"),
    )

    full_answer = ""
    try:
        stream = await client.chat.completions.create(
            model=settings.DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": summary_prompt}],
            stream=True,
            max_tokens=settings.AI_DEEP_MAX_TOKENS // 4,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                full_answer += delta.content
                yield "data: " + json.dumps({"content": delta.content}) + "\n\n"

    except Exception as e:
        logger.error(f"Deep analysis summary failed: {e}")
        full_answer = "综合分析暂时不可用，以下是各角度分析结果：\n\n"
        for key, label in [("fundamental", "基本面"), ("technical", "技术面"), ("risk", "风险")]:
            full_answer += f"### {label}\n{results.get(key, '暂不可用')}\n\n"
        yield "data: " + json.dumps({"content": full_answer}) + "\n\n"

    full_answer += DISCLAIMER
    yield "data: " + json.dumps({"content": DISCLAIMER}) + "\n\n"

    conversation = AIConversation(
        user_id=user_id,
        mode="deep",
        question=question,
        answer=full_answer,
    )
    db.add(conversation)
    await db.commit()

    yield "data: " + json.dumps({"done": True}) + "\n\n"


async def get_conversation_history(
    db: AsyncSession,
    user_id,
    limit: int = 50,
) -> list[AIConversation]:
    """Get recent conversation history for user."""
    result = await db.execute(
        select(AIConversation)
        .where(AIConversation.user_id == user_id)
        .order_by(AIConversation.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def cleanup_old_conversations(db: AsyncSession) -> int:
    """Delete conversations older than 30 days. Returns count deleted."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    result = await db.execute(
        delete(AIConversation).where(AIConversation.created_at < cutoff)
    )
    await db.commit()
    deleted = result.rowcount
    if deleted:
        logger.info(f"Cleaned up {deleted} old AI conversations")
    return deleted
