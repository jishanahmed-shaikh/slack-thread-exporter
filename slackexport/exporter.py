"""
Thread export logic — produces Markdown or HTML output.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from slackexport.client import SlackClient, SlackMessage
from slackexport.formatter import slack_to_markdown, ts_to_datetime


class ThreadExporter:
    """Exports a Slack thread to Markdown or HTML.

    Parameters
    ----------
    client:
        A :class:`~slackexport.client.SlackClient` or mock instance.
    resolve_usernames:
        If ``True`` (default), resolve user IDs to display names.
    """

    def __init__(self, client: SlackClient, resolve_usernames: bool = True) -> None:
        self.client            = client
        self.resolve_usernames = resolve_usernames
        self._user_cache: dict = {}

    def _resolve(self, user_id: str) -> str:
        if not self.resolve_usernames:
            return user_id
        if user_id not in self._user_cache:
            self._user_cache[user_id] = self.client.get_user_name(user_id)
        return self._user_cache[user_id]

    def fetch(self, channel: str, thread_ts: str) -> List[SlackMessage]:
        """Fetch all messages in a thread and resolve usernames.

        Parameters
        ----------
        channel:
            Slack channel ID.
        thread_ts:
            Thread parent message timestamp.

        Returns
        -------
        List[SlackMessage]
            Messages with ``username`` populated.
        """
        messages = self.client.get_thread_replies(channel, thread_ts)
        for msg in messages:
            msg.username = self._resolve(msg.user)
        return messages

    def to_markdown(self, messages: List[SlackMessage], title: str = "Slack Thread") -> str:
        """Render messages as a Markdown document.

        Parameters
        ----------
        messages:
            List of :class:`~slackexport.client.SlackMessage` objects.
        title:
            Document title used as the H1 heading.

        Returns
        -------
        str
            Markdown string.
        """
        lines = [f"# {title}\n"]

        for i, msg in enumerate(messages):
            dt = ts_to_datetime(msg.ts)
            author = msg.username or msg.user
            text   = slack_to_markdown(msg.text)

            if i == 0:
                lines.append(f"**{author}** — {dt}\n")
            else:
                lines.append(f"---\n\n**{author}** — {dt}\n")

            lines.append(f"{text}\n")

            if msg.reactions:
                rxns = "  ".join(f":{r['name']}: ×{r['count']}" for r in msg.reactions)
                lines.append(f"\n> {rxns}\n")

            if msg.files:
                for f in msg.files:
                    name = f.get("name", "attachment")
                    url  = f.get("url_private", "")
                    lines.append(f"\n📎 [{name}]({url})\n")

        return "\n".join(lines)

    def to_html(self, messages: List[SlackMessage], title: str = "Slack Thread") -> str:
        """Render messages as a self-contained HTML document.

        Parameters
        ----------
        messages:
            List of :class:`~slackexport.client.SlackMessage` objects.
        title:
            Document title.

        Returns
        -------
        str
            HTML string.
        """
        import html as html_mod

        def md_to_html(text: str) -> str:
            """Very minimal Markdown-to-HTML for the exported content."""
            text = html_mod.escape(text)
            # Bold
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            # Italic
            text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
            # Code
            text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
            # Links
            text = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', text)
            # Line breaks
            text = text.replace("\n", "<br>")
            return text

        import re

        msg_html = []
        for i, msg in enumerate(messages):
            dt     = ts_to_datetime(msg.ts)
            author = html_mod.escape(msg.username or msg.user)
            text   = md_to_html(slack_to_markdown(msg.text))
            cls    = "message parent" if i == 0 else "message reply"
            rxns   = ""
            if msg.reactions:
                rxns = "<div class='reactions'>" + "".join(
                    f"<span class='reaction'>:{r['name']}: {r['count']}</span>"
                    for r in msg.reactions
                ) + "</div>"
            msg_html.append(
                f'<div class="{cls}">'
                f'<div class="meta"><strong>{author}</strong> <span class="ts">{dt}</span></div>'
                f'<div class="body">{text}</div>'
                f'{rxns}'
                f'</div>'
            )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<title>{html_mod.escape(title)}</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem;color:#1d1c1d;line-height:1.5}}
  h1{{font-size:1.4rem;margin-bottom:1.5rem;border-bottom:2px solid #e8e8e8;padding-bottom:.75rem}}
  .message{{padding:1rem;margin-bottom:.75rem;border-radius:8px;background:#f8f8f8}}
  .parent{{background:#fff;border:1px solid #e8e8e8}}
  .reply{{margin-left:2rem;border-left:3px solid #4a154b}}
  .meta{{font-size:.85rem;margin-bottom:.4rem}}
  .ts{{color:#888;font-size:.8rem}}
  .reactions{{margin-top:.5rem;font-size:.8rem;color:#555}}
  .reaction{{background:#e8e8e8;border-radius:4px;padding:.1rem .4rem;margin-right:.3rem}}
  code{{background:#f0f0f0;padding:.1rem .3rem;border-radius:3px;font-size:.9em}}
</style>
</head>
<body>
<h1>{html_mod.escape(title)}</h1>
{"".join(msg_html)}
</body>
</html>"""


def export_thread(
    channel: str,
    thread_ts: str,
    client: object,
    output_path: str,
    fmt: str = "markdown",
    title: str = "Slack Thread",
    since: Optional[str] = None,
    no_resolve_usernames: bool = False,
) -> str:
    """Export a Slack thread to a file.

    Parameters
    ----------
    channel:
        Slack channel ID.
    thread_ts:
        Thread parent message timestamp.
    client:
        A :class:`~slackexport.client.SlackClient` or mock instance.
    output_path:
        Destination file path.
    fmt:
        Output format: ``"markdown"`` or ``"html"``.
    title:
        Document title.
    since:
    Optional date (YYYY-MM-DD). Only messages after this date are included.

    Returns
    -------
    str
        The output file path.
    """
    from datetime import datetime

    since_dt = None
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d")

    exporter = ThreadExporter(client, resolve_usernames=not no_resolve_usernames)

    messages  = exporter.fetch(channel, thread_ts)

    if since_dt:
        messages = [
            msg for msg in messages
            if datetime.fromtimestamp(float(msg.ts.split(".")[0])) >= since_dt
        ]

    if fmt == "html":
        content = exporter.to_html(messages, title=title)
    else:
        content = exporter.to_markdown(messages, title=title)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content, encoding="utf-8")
    return output_path
