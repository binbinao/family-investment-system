"""Push notification service: Server酱 + Bark + Email."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting

logger = logging.getLogger(__name__)


async def _get_setting(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(Setting).where(Setting.key == key))
    s = result.scalar_one_or_none()
    return s.value if s else None


async def send_serverchan(db: AsyncSession, title: str, content: str) -> bool:
    """Send via Server酱 (https://sct.ftqq.com)."""
    key = await _get_setting(db, "serverchan_key")
    if not key:
        logger.info("Server酱 key not configured, skipping")
        return False

    url = f"https://sctapi.ftqq.com/{key}.send"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, data={"title": title, "desp": content})
            if resp.status_code == 200:
                logger.info("Server酱 push sent")
                return True
            logger.warning(f"Server酱 push failed: {resp.text}")
        except Exception as e:
            logger.error(f"Server酱 error: {e}")
    return False


async def send_bark(db: AsyncSession, title: str, content: str) -> bool:
    """Send via Bark (https://github.com/Finb/Bark)."""
    bark_url = await _get_setting(db, "bark_url")
    if not bark_url:
        logger.info("Bark URL not configured, skipping")
        return False

    url = f"{bark_url.rstrip('/')}/{title}/{content}"
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                logger.info("Bark push sent")
                return True
            logger.warning(f"Bark push failed: {resp.text}")
        except Exception as e:
            logger.error(f"Bark error: {e}")
    return False


async def send_email(db: AsyncSession, subject: str, html_content: str) -> bool:
    """Send email notification."""
    smtp_host = await _get_setting(db, "smtp_host")
    smtp_port = await _get_setting(db, "smtp_port")
    smtp_user = await _get_setting(db, "smtp_user")
    smtp_pass = await _get_setting(db, "smtp_pass")
    email_to = await _get_setting(db, "email_to")

    if not all([smtp_host, smtp_user, smtp_pass, email_to]):
        logger.info("Email not fully configured, skipping")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = email_to
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP_SSL(smtp_host, int(smtp_port or 465)) as server:
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f"Email sent to {email_to}")
        return True
    except Exception as e:
        logger.error(f"Email error: {e}")
        return False


async def push_daily_report(db: AsyncSession, summary: str, full_content: str):
    """Push daily report via all configured channels."""
    title = f"齐家晨报 · {summary[:50]}"

    await send_serverchan(db, title, full_content)
    await send_bark(db, "齐家晨报", summary[:100])
    await send_email(db, title, f"<pre>{full_content}</pre>")
