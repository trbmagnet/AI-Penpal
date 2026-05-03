import tempfile
from pathlib import Path

from tracker import ReplyTracker


def test_mark_and_check():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    msg_id = "<test-message-id@example.com>"

    assert not tracker.has_replied(msg_id)
    tracker.mark_replied(msg_id)
    assert tracker.has_replied(msg_id)

    tracker.close()


def test_has_replied_returns_false_for_unknown():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    assert not tracker.has_replied("<unknown@example.com>")
    tracker.close()


def test_mark_replied_idempotent():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    msg_id = "<duplicate@test.com>"

    tracker.mark_replied(msg_id)
    tracker.mark_replied(msg_id)
    assert tracker.has_replied(msg_id)
    tracker.close()


def test_store_and_get_exchange():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    tracker.store_exchange(
        sender="alice@example.com",
        role="user",
        content="Hello, how are you?",
        subject="Hi",
        message_id="<msg1@test.com>",
    )
    tracker.store_exchange(
        sender="alice@example.com",
        role="assistant",
        content="I'm great, thanks!",
        subject="Re: Hi",
        message_id="<reply1@test.com>",
    )

    history = tracker.get_history("alice@example.com", limit=10)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello, how are you?"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "I'm great, thanks!"

    tracker.close()


def test_get_history_returns_recent_first():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    for i in range(5):
        tracker.store_exchange(
            sender="bob@example.com",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            subject="Test",
            message_id=f"<msg{i}@test.com>",
        )

    history = tracker.get_history("bob@example.com", limit=3)
    assert len(history) == 3
    assert history[0]["content"] == "Message 2"
    assert history[1]["content"] == "Message 3"
    assert history[2]["content"] == "Message 4"

    tracker.close()


def test_get_history_empty_for_unknown_sender():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    history = tracker.get_history("nobody@example.com", limit=10)
    assert history == []
    tracker.close()


def test_get_exchange_count():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    assert tracker.get_exchange_count("alice@example.com") == 0
    tracker.store_exchange(
        sender="alice@example.com",
        role="user",
        content="Test",
        subject="Test",
        message_id="<msg@test.com>",
    )
    assert tracker.get_exchange_count("alice@example.com") == 1
    tracker.close()


def test_get_and_update_summary():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)

    summary = tracker.get_summary("alice@example.com")
    assert summary is None

    tracker.update_summary(
        sender="alice@example.com",
        summary_text="Alice likes hiking and cooking.",
        up_to_count=5,
    )

    summary = tracker.get_summary("alice@example.com")
    assert summary is not None
    assert summary["summary_text"] == "Alice likes hiking and cooking."
    assert summary["up_to_count"] == 5

    tracker.close()


def test_update_summary_replaces_existing():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    tracker.update_summary("bob@example.com", "Old summary", 3)
    tracker.update_summary("bob@example.com", "New summary", 6)

    summary = tracker.get_summary("bob@example.com")
    assert summary["summary_text"] == "New summary"
    assert summary["up_to_count"] == 6

    tracker.close()


def test_get_old_messages_for_sender():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    tracker = ReplyTracker(db_path)
    for i in range(8):
        tracker.store_exchange(
            sender="carol@example.com",
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}",
            subject="Test",
            message_id=f"<msg{i}@test.com>",
        )

    old_messages = tracker.get_old_messages_for_sender("carol@example.com", exclude_recent=3)
    assert len(old_messages) == 5
    assert old_messages[0]["content"] == "Message 0"
    assert old_messages[4]["content"] == "Message 4"

    tracker.close()
