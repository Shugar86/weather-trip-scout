from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import TelegramError

from app.domain.models import ReportPayload
from app.services.telegram_service import TelegramService


async def test_send_report_without_image_sends_message() -> None:
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock()
    mock_bot.send_photo = AsyncMock()

    with patch("app.services.telegram_service.Bot", return_value=mock_bot):
        service = TelegramService(bot_token="token", chat_id="123")

    payload = ReportPayload(text="Hello!")
    await service.send_report(payload)

    mock_bot.send_message.assert_awaited_once_with(chat_id="123", text="Hello!")
    mock_bot.send_photo.assert_not_awaited()


async def test_send_report_with_image_sends_photo(tmp_path) -> None:
    image_path = tmp_path / "map.png"
    image_path.write_bytes(b"pngdata")

    mock_bot = MagicMock()
    mock_bot.send_photo = AsyncMock()

    with patch("app.services.telegram_service.Bot", return_value=mock_bot):
        service = TelegramService(bot_token="token", chat_id="123")

    payload = ReportPayload(text="See map", image_path=str(image_path))
    await service.send_report(payload)

    mock_bot.send_photo.assert_awaited_once()
    call_kwargs = mock_bot.send_photo.await_args.kwargs
    assert call_kwargs["chat_id"] == "123"
    assert call_kwargs["caption"] == "See map"
    assert call_kwargs["photo"].name == str(image_path)


async def test_send_report_logs_and_re_raises_telegram_error() -> None:
    mock_bot = MagicMock()
    mock_bot.send_message = AsyncMock(side_effect=TelegramError("API down"))

    with (
        patch("app.services.telegram_service.Bot", return_value=mock_bot),
        patch("app.services.telegram_service.logger") as mock_logger,
    ):
        service = TelegramService(bot_token="token", chat_id="123")
        payload = ReportPayload(text="Hello!")

        with pytest.raises(TelegramError, match="API down"):
            await service.send_report(payload)

    mock_logger.error.assert_called_once()
