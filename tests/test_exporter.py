"""Tests for slack-thread-exporter."""

import pytest
from slackexport.client import MockSlackClient, SlackMessage
from slackexport.formatter import slack_to_markdown, ts_to_datetime
from slackexport.exporter import ThreadExporter


class TestFormatter:
    def test_bold(self):
        assert slack_to_markdown("*hello*") == "**hello**"

    def test_italic(self):
        assert slack_to_markdown("_world_") == "*world*"

    def test_strikethrough(self):
        assert slack_to_markdown("~text~") == "~~text~~"

    def test_link_with_label(self):
        result = slack_to_markdown("<https://example.com|click here>")
        assert result == "[click here](https://example.com)"

    def test_user_mention(self):
        assert slack_to_markdown("<@U01234>") == "@U01234"

    def test_channel_mention(self):
        assert slack_to_markdown("<!channel>") == "@channel"

    def test_html_entities(self):
        assert slack_to_markdown("a &amp; b &lt;c&gt;") == "a & b <c>"

    def test_empty_string(self):
        assert slack_to_markdown("") == ""

    def test_ts_to_datetime(self):
        result = ts_to_datetime("1714500000.000100")
        assert "2024" in result or "UTC" in result

    def test_ts_invalid(self):
        result = ts_to_datetime("invalid")
        assert result == "invalid"


class TestThreadExporter:
    def test_fetch_returns_messages(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        assert len(msgs) == 4

    def test_usernames_resolved(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        assert msgs[0].username == "Alice"
        assert msgs[1].username == "Bob"

    def test_to_markdown_contains_title(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        md = exp.to_markdown(msgs, title="Test Thread")
        assert "# Test Thread" in md

    def test_to_markdown_contains_usernames(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        md = exp.to_markdown(msgs)
        assert "Alice" in md
        assert "Bob" in md

    def test_to_markdown_contains_text(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        md = exp.to_markdown(msgs)
        assert "memory leak" in md

    def test_to_html_is_valid_html(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        html = exp.to_html(msgs, title="Test")
        assert "<!DOCTYPE html>" in html
        assert "<title>Test</title>" in html
        assert "Alice" in html

    def test_reactions_in_markdown(self):
        mock = MockSlackClient()
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        md = exp.to_markdown(msgs)
        assert "white_check_mark" in md

    def test_empty_thread(self):
        mock = MockSlackClient()
        mock._messages = []
        exp = ThreadExporter(mock)
        msgs = exp.fetch(mock.MOCK_CHANNEL, mock.MOCK_THREAD_TS)
        md = exp.to_markdown(msgs)
        assert "# Slack Thread" in md
