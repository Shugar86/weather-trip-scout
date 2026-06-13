import logging

from telegram import Bot
from telegram.error import TelegramError

from app.domain.models import ReportPayload

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    async def send_report(self, payload: ReportPayload) -> None:
        try:
            if payload.image_path:
                with open(payload.image_path, "rb") as photo:
                    await self.bot.send_photo(
                        chat_id=self.chat_id,
                        photo=photo,
                        caption=payload.text,
                    )
            else:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=payload.text,
                )
            logger.info("Report sent to %s", self.chat_id)
        except TelegramError as exc:
            logger.error("Failed to send report to %s: %s", self.chat_id, exc)
            raise
