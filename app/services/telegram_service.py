import logging

from telegram import Bot

from app.domain.models import ReportPayload

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def send_report(self, payload: ReportPayload) -> None:
        if payload.image_path:
            with open(payload.image_path, "rb") as photo:
                self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=payload.text,
                )
        else:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=payload.text,
            )
        logger.info("Report sent to %s", self.chat_id)
