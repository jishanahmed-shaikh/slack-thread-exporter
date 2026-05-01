"""
Slack API client wrapper.

Wraps the Slack Web API into a minimal interface.
Uses only ``urllib`` from the standard library — no ``slack_sdk`` required.

To use with a real Slack workspace:
1. Create a Slack App at https://api.slack.com/apps
2. Add OAuth scopes: ``channels:history``, ``users:read``
3. Install the app and copy the Bot Token (``xoxb-...``)
4. Pass it as ``token`` to :class:`SlackClient`
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


SLACK_API_BASE = "https://slack.com/api"


@dataclass
class SlackMessage:
    """A single Slack message.

    Attributes
    ----------
    ts:
        Message timestamp (also used as unique ID in Slack).
    user:
        User ID of the sender.
    username:
        Display name of the sender (resolved separately).
    text:
        Message text (may contain Slack mrkdwn formatting).
    thread_ts:
        Thread timestamp (same as ``ts`` for the parent message).
    reply_count:
        Number of replies (0 for non-parent messages).
    reactions:
        List of reaction dicts with ``name`` and ``count``.
    files:
        List of attached file dicts.
    """

    ts: str
    user: str
    username: str = ""
    text: str = ""
    thread_ts: str = ""
    reply_count: int = 0
    reactions: List[Dict] = field(default_factory=list)
    files: List[Dict] = field(default_factory=list)


class SlackClient:
    """Minimal Slack Web API client.

    Parameters
    ----------
    token:
        Slack Bot Token (``xoxb-...``).  Pass a mock token for testing.
    base_url:
        API base URL (override for testing).
    """

    def __init__(
        self,
        token: str,
        base_url: str = SLACK_API_BASE,
    ) -> None:
        self.token    = token
        self.base_url = base_url.rstrip("/")

    def _get(self, method: str, params: Dict[str, str]) -> Dict:
        """Make a GET request to the Slack API.

        Parameters
        ----------
        method:
            Slack API method name (e.g. ``"conversations.replies"``).
        params:
            Query parameters.

        Returns
        -------
        Dict
            Parsed JSON response.

        Raises
        ------
        ConnectionError
            If the API is unreachable.
        PermissionError
            If the token is invalid or missing scopes.
        RuntimeError
            If the API returns an error.
        """
        from urllib.parse import urlencode
        url = f"{self.base_url}/{method}?{urlencode(params)}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {self.token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            raise ConnectionError(f"Cannot reach Slack API: {exc}") from exc

        if not data.get("ok"):
            error = data.get("error", "unknown_error")
            if error in ("invalid_auth", "not_authed", "token_revoked"):
                raise PermissionError(f"Slack auth error: {error}")
            raise RuntimeError(f"Slack API error: {error}")

        return data

    def get_thread_replies(self, channel: str, thread_ts: str) -> List[SlackMessage]:
        """Fetch all messages in a thread.

        Parameters
        ----------
        channel:
            Channel ID (e.g. ``"C01234567"``).
        thread_ts:
            Timestamp of the parent message.

        Returns
        -------
        List[SlackMessage]
            All messages in the thread, including the parent.
        """
        data = self._get("conversations.replies", {
            "channel":   channel,
            "ts":        thread_ts,
            "limit":     "200",
        })
        messages = []
        for m in data.get("messages", []):
            messages.append(SlackMessage(
                ts=m.get("ts", ""),
                user=m.get("user", ""),
                text=m.get("text", ""),
                thread_ts=m.get("thread_ts", ""),
                reply_count=int(m.get("reply_count", 0)),
                reactions=m.get("reactions", []),
                files=m.get("files", []),
            ))
        return messages

    def get_user_name(self, user_id: str) -> str:
        """Resolve a user ID to a display name.

        Parameters
        ----------
        user_id:
            Slack user ID (e.g. ``"U01234567"``).

        Returns
        -------
        str
            Display name, or the user ID if resolution fails.
        """
        try:
            data = self._get("users.info", {"user": user_id})
            profile = data.get("user", {}).get("profile", {})
            return profile.get("display_name") or profile.get("real_name") or user_id
        except Exception:
            return user_id


# ---------------------------------------------------------------------------
# Mock client for testing (no Slack token required)
# ---------------------------------------------------------------------------

class MockSlackClient:
    """In-memory Slack mock for unit testing.

    Pre-loads a thread with realistic fake messages.
    No Slack token or network access required.
    """

    MOCK_CHANNEL = "C01MOCK001"
    MOCK_THREAD_TS = "1714500000.000100"

    def __init__(self) -> None:
        self._messages = [
            SlackMessage(
                ts="1714500000.000100",
                user="U001",
                username="Alice",
                text="Has anyone looked into the memory leak in the auth service?",
                thread_ts="1714500000.000100",
                reply_count=3,
            ),
            SlackMessage(
                ts="1714500060.000200",
                user="U002",
                username="Bob",
                text="Yes, I traced it to the JWT cache not being cleared on logout. "
                     "The `token_cache` dict grows unbounded.",
                thread_ts="1714500000.000100",
            ),
            SlackMessage(
                ts="1714500120.000300",
                user="U003",
                username="Carol",
                text="We should add a TTL or use `functools.lru_cache` with `maxsize`. "
                     "I can open a PR today.",
                thread_ts="1714500000.000100",
            ),
            SlackMessage(
                ts="1714500180.000400",
                user="U001",
                username="Alice",
                text="That would be great Carol. Let's also add a unit test for the "
                     "cache eviction. Tagging this as P1.",
                thread_ts="1714500000.000100",
                reactions=[{"name": "white_check_mark", "count": 2}],
            ),
        ]
        self._users = {"U001": "Alice", "U002": "Bob", "U003": "Carol"}

    def get_thread_replies(self, channel: str, thread_ts: str) -> List[SlackMessage]:
        return list(self._messages)

    def get_user_name(self, user_id: str) -> str:
        return self._users.get(user_id, user_id)
