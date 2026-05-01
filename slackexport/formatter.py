"""
Slack mrkdwn to Markdown/plain text formatter.

Converts Slack's mrkdwn formatting to standard Markdown.
"""

from __future__ import annotations

import re


def slack_to_markdown(text: str) -> str:
    """Convert Slack mrkdwn formatting to standard Markdown.

    Handles:
    - ``*bold*``       -> ``**bold**``
    - ``_italic_``     -> ``*italic*``
    - ``~strike~``     -> ``~~strike~~``
    - `` `code` ``     -> `` `code` `` (unchanged)
    - ``<URL|label>``  -> ``[label](URL)``
    - ``<URL>``        -> ``<URL>``
    - ``<@USERID>``    -> ``@USERID``
    - ``<!channel>``   -> ``@channel``
    - ``&amp;``        -> ``&``
    - ``&lt;``         -> ``<``
    - ``&gt;``         -> ``>``

    Parameters
    ----------
    text:
        Slack mrkdwn string.

    Returns
    -------
    str
        Standard Markdown string.
    """
    if not text:
        return ""

    # HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

    # Links: <URL|label> -> [label](URL)
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", r"[\2](\1)", text)
    # Plain links: <URL>
    text = re.sub(r"<(https?://[^>]+)>", r"<\1>", text)

    # User mentions: <@USERID> -> @USERID
    text = re.sub(r"<@([A-Z0-9]+)>", r"@\1", text)

    # Channel mentions: <!channel>, <!here>
    text = re.sub(r"<!(\w+)>", r"@\1", text)

    # Bold: *text* -> **text** (avoid matching * in code blocks)
    text = re.sub(r"(?<![`*])\*([^*\n]+)\*(?![`*])", r"**\1**", text)

    # Italic: _text_ -> *text*
    text = re.sub(r"(?<![_`])_([^_\n]+)_(?![_`])", r"*\1*", text)

    # Strikethrough: ~text~ -> ~~text~~
    text = re.sub(r"~([^~\n]+)~", r"~~\1~~", text)

    return text


def ts_to_datetime(ts: str) -> str:
    """Convert a Slack timestamp to a human-readable datetime string.

    Parameters
    ----------
    ts:
        Slack timestamp string (e.g. ``"1714500000.000100"``).

    Returns
    -------
    str
        Formatted datetime string (UTC).
    """
    import datetime
    try:
        epoch = float(ts.split(".")[0])
        dt = datetime.datetime.utcfromtimestamp(epoch)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return ts
