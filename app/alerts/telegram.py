import httpx
from pydantic import SecretStr
from app.config import Settings

API_URL = "https://api.telegram.org"
MAX_MESSAGE_LENGTH = 4096

settings = Settings()

class NotificationError(Exception):
    pass


class TelegramNotifier:
    def __init__(self, client: httpx.Client, token: SecretStr, chat_id: int) -> None:
        self._client = client
        self._token = token
        self._chat_id = chat_id

    def send(self, text: str) -> None:
        url = f"{API_URL}/bot{self._token.get_secret_value()}/sendMessage"
        payload = {"chat_id": self._chat_id, "text": text[:MAX_MESSAGE_LENGTH]}
        try:
            response = self._client.post(url, json=payload, timeout=10)
        except httpx.HTTPError as error:
            raise NotificationError(f"Telegram request failed: {type(error).__name__}") from None
        if response.status_code != 200:
            raise NotificationError(
                f"Telegram returned HTTP {response.status_code}: {response.text[:200]}"
            )

def create_notifier(settings: Settings) -> TelegramNotifier | None:
    if settings.telegram_bot_token is None or settings.telegram_chat_id is None:
        return None
    return TelegramNotifier(
        httpx.Client(), settings.telegram_bot_token, settings.telegram_chat_id
    )


if __name__ == "__main__":
    notifier = create_notifier(Settings())
    if notifier is None:
        raise SystemExit("Telegram is not configured: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
    notifier.send("CS2 Market Agent: test message")
    print("Sent")