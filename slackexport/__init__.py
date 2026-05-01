"""
slack-thread-exporter
=====================
Export a Slack thread to a clean Markdown or HTML file.

Replace the mock Slack client with a real one using your Bot Token:

    import urllib.request, json
    # Use SlackClient(token="xoxb-your-real-token")

Public API
----------
- :class:`SlackClient`   — Slack API wrapper (mockable)
- :class:`ThreadExporter` — export a thread to Markdown/HTML
- :func:`export_thread`  — convenience function
"""

__version__ = "1.0.0"
__author__  = "Jishanahmed AR Shaikh"
__license__ = "MIT"

from slackexport.client import SlackClient, SlackMessage  # noqa: F401
from slackexport.exporter import ThreadExporter, export_thread  # noqa: F401
