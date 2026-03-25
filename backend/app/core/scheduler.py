"""APScheduler integration for periodic tasks."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.database import async_session
from app.services.ai import cleanup_old_conversations
from app.services.daily_report import generate_daily_report
from app.services.market import refresh_all_prices
from app.services.notification import push_daily_report
from app.services.snapshot import create_daily_snapshot

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _refresh_stock_prices():
    """Scheduled task: refresh stock prices during trading hours."""
    logger.info("Scheduled: refreshing stock prices")
    async with async_session() as db:
        result = await refresh_all_prices(db)
        logger.info(f"Stock price refresh: {result}")


async def _refresh_fund_nav():
    """Scheduled task: refresh fund NAV (daily at 20:00)."""
    logger.info("Scheduled: refreshing fund NAV")
    async with async_session() as db:
        result = await refresh_all_prices(db)
        logger.info(f"Fund NAV refresh: {result}")


async def _create_snapshot():
    """Scheduled task: create daily portfolio snapshot."""
    logger.info("Scheduled: creating daily snapshot")
    async with async_session() as db:
        snapshot = await create_daily_snapshot(db)
        if snapshot:
            logger.info(f"Snapshot created: {snapshot.date}")


async def _generate_morning_report():
    """Scheduled task: generate daily AI morning report."""
    logger.info("Scheduled: generating daily report")
    async with async_session() as db:
        report = await generate_daily_report(db)
        if report:
            await push_daily_report(db, report.summary, report.content_markdown)
            logger.info(f"Daily report generated and pushed: {report.date}")


async def _cleanup_conversations():
    """Scheduled task: clean up conversations older than 30 days."""
    logger.info("Scheduled: cleaning up old AI conversations")
    async with async_session() as db:
        deleted = await cleanup_old_conversations(db)
        logger.info(f"Cleaned up {deleted} old conversations")


def start_scheduler():
    """Start all scheduled tasks."""
    # Stock prices: every 5 minutes during trading hours (weekdays)
    scheduler.add_job(
        _refresh_stock_prices,
        CronTrigger(
            day_of_week="mon-fri",
            hour="9-11,13-14",
            minute="*/5",
        ),
        id="refresh_stock_prices",
        replace_existing=True,
    )

    # Additional run at 9:30 and 15:00
    scheduler.add_job(
        _refresh_stock_prices,
        CronTrigger(day_of_week="mon-fri", hour=9, minute=30),
        id="refresh_stock_open",
        replace_existing=True,
    )

    # Fund NAV: daily at 20:00
    scheduler.add_job(
        _refresh_fund_nav,
        CronTrigger(hour=20, minute=0),
        id="refresh_fund_nav",
        replace_existing=True,
    )

    # Daily snapshot: weekdays at 15:30 (after market close)
    scheduler.add_job(
        _create_snapshot,
        CronTrigger(day_of_week="mon-fri", hour=15, minute=30),
        id="daily_snapshot",
        replace_existing=True,
    )

    # Daily morning report at 08:00
    scheduler.add_job(
        _generate_morning_report,
        CronTrigger(hour=8, minute=0),
        id="morning_report",
        replace_existing=True,
    )

    # Clean up old AI conversations daily at 03:00
    scheduler.add_job(
        _cleanup_conversations,
        CronTrigger(hour=3, minute=0),
        id="cleanup_conversations",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with 6 jobs")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
