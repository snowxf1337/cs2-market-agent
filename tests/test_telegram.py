import json

import httpx
import pytest
from pydantic import SecretStr

from app.alerts.telegram import MAX_MESSAGE_LENGTH, NotificationError, TelegramNotifier

FAKE_TOKEN = SecretStr("123:FAKE")


def make_notifier(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return TelegramNotifier(client, FAKE_TOKEN, chat_id=42)


def test_sends_message_to_chat():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    make_notifier(handler).send("hello")

    [request] = requests
    assert request.method == "POST"
    assert request.url.path == "/bot123:FAKE/sendMessage"
    assert json.loads(request.content) == {"chat_id": 42, "text": "hello"}


def test_long_message_is_truncated():
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={"ok": True})

    make_notifier(handler).send("x" * 5000)

    assert len(json.loads(requests[0].content)["text"]) == MAX_MESSAGE_LENGTH


def test_http_error_does_not_leak_token():
    def handler(request):
        return httpx.Response(400, json={"ok": False, "description": "Bad Request: chat not found"})

    with pytest.raises(NotificationError) as error:
        make_notifier(handler).send("hello")

    assert "400" in str(error.value)
    assert "chat not found" in str(error.value)
    assert "FAKE" not in str(error.value)


def test_network_error_does_not_leak_token():
    def handler(request):
        raise httpx.ConnectError("connection failed", request=request)

    with pytest.raises(NotificationError) as error:
        make_notifier(handler).send("hello")

    assert "FAKE" not in str(error.value)
    assert error.value.__suppress_context__


from app.alerts.telegram import create_notifier
from app.config import Settings


def make_settings(**overrides):
    return Settings(
        _env_file=None,
        db_user="user",
        db_password="secret",
        db_name="db",
        db_test_name="db_test",
        **overrides,
    )


def test_no_notifier_when_telegram_is_not_configured():
    assert create_notifier(make_settings()) is None


def test_notifier_is_created_when_configured():
    notifier = create_notifier(
        make_settings(telegram_bot_token="123:FAKE", telegram_chat_id=42)
    )
    assert isinstance(notifier, TelegramNotifier)