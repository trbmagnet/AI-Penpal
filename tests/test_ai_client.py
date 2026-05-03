from unittest.mock import patch, MagicMock

from ai_client import create_client, OpenAIClient, AnthropicClient


def test_openai_generate_reply_with_history():
    client = OpenAIClient(api_key="sk-test", model_name="gpt-4o")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Reply with context"))]

    with patch.object(client.client.chat.completions, "create", return_value=mock_response) as mock_create:
        history = [
            {"role": "user", "content": "Previous email"},
            {"role": "assistant", "content": "Previous reply"},
        ]
        result = client.generate_reply("System prompt", "New email", history=history)

        assert result == "Reply with context"
        call_args = mock_create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "Previous email"
        assert messages[2]["content"] == "Previous reply"
        assert messages[3]["content"] == "New email"


def test_anthropic_generate_reply_with_history():
    client = AnthropicClient(api_key="sk-ant-test", model_name="claude-sonnet-4-20250514")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Reply with context")]

    with patch.object(client.client.messages, "create", return_value=mock_response) as mock_create:
        history = [
            {"role": "user", "content": "Previous email"},
            {"role": "assistant", "content": "Previous reply"},
        ]
        result = client.generate_reply("System prompt", "New email", history=history)

        assert result == "Reply with context"
        call_args = mock_create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 3
        assert messages[0]["content"] == "Previous email"
        assert messages[1]["content"] == "Previous reply"
        assert messages[2]["content"] == "New email"
        assert call_args[1]["system"] == "System prompt"


def test_generate_reply_without_history_still_works():
    client = OpenAIClient(api_key="sk-test", model_name="gpt-4o")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Simple reply"))]

    with patch.object(client.client.chat.completions, "create", return_value=mock_response) as mock_create:
        result = client.generate_reply("System prompt", "New email")

        assert result == "Simple reply"
        call_args = mock_create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) == 2


def test_create_openai_client():
    client = create_client(
        provider="openai",
        api_key="sk-test",
        model_name="gpt-4o",
    )
    assert isinstance(client, OpenAIClient)


def test_create_anthropic_client():
    client = create_client(
        provider="anthropic",
        api_key="sk-ant-test",
        model_name="claude-sonnet-4-20250514",
    )
    assert isinstance(client, AnthropicClient)


def test_create_unsupported_provider():
    try:
        create_client(provider="gemini", api_key="test", model_name="test")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported provider" in str(e)


def test_openai_summarize_history():
    client = OpenAIClient(api_key="sk-test", model_name="gpt-4o")

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Alice discussed hiking plans."))]

    with patch.object(client.client.chat.completions, "create", return_value=mock_response) as mock_create:
        messages = [
            {"role": "user", "content": "I love hiking!"},
            {"role": "assistant", "content": "That's great! Where do you like to hike?"},
        ]
        result = client.summarize_history(messages)

        assert result == "Alice discussed hiking plans."
        call_args = mock_create.call_args
        assert call_args[1]["temperature"] == 0.3
        messages_sent = call_args[1]["messages"]
        assert messages_sent[0]["role"] == "system"
        assert "摘要" in messages_sent[0]["content"]


def test_anthropic_summarize_history():
    client = AnthropicClient(api_key="sk-ant-test", model_name="claude-sonnet-4-20250514")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Alice discussed hiking plans.")]

    with patch.object(client.client.messages, "create", return_value=mock_response) as mock_create:
        messages = [
            {"role": "user", "content": "I love hiking!"},
            {"role": "assistant", "content": "That's great! Where do you like to hike?"},
        ]
        result = client.summarize_history(messages)

        assert result == "Alice discussed hiking plans."
        call_args = mock_create.call_args
        assert call_args[1]["temperature"] == 0.3
