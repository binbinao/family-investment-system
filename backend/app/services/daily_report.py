"""Daily AI morning report service."""

import logging
from datetime import date

from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.daily_report import DailyReport
from app.services.ai import _build_portfolio_context

logger = logging.getLogger(__name__)

REPORT_PROMPT = """你是"齐家"家庭投资助手。请根据用户的持仓情况，生成一份简洁的每日投资晨报。

格式要求（Markdown）：
## 📊 齐家晨报 · {date}

### 市场情绪
（一句话概括今日A股/基金市场的整体氛围）

### 持仓关注
（如果持仓标的有值得关注的信息就写，没有就说"今日无重要关联资讯"）

### 关注提示
（1-2条简短的投资关注建议）

---
*本晨报由 AI 自动生成，仅供参考，不构成投资建议。*

用户持仓情况：
{portfolio_context}

今日新闻摘要：
{news_summary}
"""


async def _fetch_news_summary() -> str:
    """Fetch market news via AKShare."""
    try:
        import asyncio
        import akshare as ak

        df = await asyncio.to_thread(ak.stock_zh_a_alerts_cls)
        if df is not None and not df.empty:
            headlines = df.head(10).to_string(index=False)
            return headlines
    except Exception as e:
        logger.warning(f"Failed to fetch news: {e}")

    return "暂无法获取今日新闻，请基于持仓数据给出一般性分析。"


async def generate_daily_report(db: AsyncSession) -> DailyReport | None:
    """Generate the daily morning report using AI."""
    today = date.today()

    existing = await db.execute(
        select(DailyReport).where(DailyReport.date == today)
    )
    if existing.scalar_one_or_none():
        logger.info(f"Report for {today} already exists")
        return None

    if not settings.resolved_llm_api_key():
        logger.warning("LLM API key not set, skipping report generation")
        return None

    portfolio_context = await _build_portfolio_context(db)
    news_summary = await _fetch_news_summary()

    prompt = REPORT_PROMPT.format(
        date=today.isoformat(),
        portfolio_context=portfolio_context,
        news_summary=news_summary,
    )

    client = AsyncOpenAI(
        api_key=settings.resolved_llm_api_key(),
        base_url=settings.resolved_llm_base_url(),
    )

    try:
        response = await client.chat.completions.create(
            model=settings.resolved_llm_model(),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        content = response.choices[0].message.content or ""
    except Exception as e:
        logger.error(f"Failed to generate daily report: {e}")
        return None

    first_line = content.split("\n")[0].strip("# ").strip()
    summary = first_line[:200] if first_line else f"齐家晨报 · {today}"

    report = DailyReport(
        date=today,
        content_markdown=content,
        summary=summary,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    logger.info(f"Daily report generated for {today}")
    return report


async def get_latest_report(db: AsyncSession) -> DailyReport | None:
    result = await db.execute(
        select(DailyReport).order_by(DailyReport.date.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def list_reports(
    db: AsyncSession, limit: int = 30
) -> list[DailyReport]:
    result = await db.execute(
        select(DailyReport).order_by(DailyReport.date.desc()).limit(limit)
    )
    return list(result.scalars().all())
