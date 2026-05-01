<div align="center">

# slack-thread-exporter

**Preserve Slack knowledge. Export any thread to clean Markdown or HTML.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Zero Runtime Deps](https://img.shields.io/badge/Runtime%20Deps-Zero-22c55e?style=flat)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat)](CONTRIBUTING.md)
[![CI](https://github.com/jishanahmed-shaikh/slack-thread-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/jishanahmed-shaikh/slack-thread-exporter/actions)

</div>

---

## Why this exists

Your team just had a 40-message Slack thread that solved a critical production incident. In 90 days, Slack's free tier will delete it. Or you need to share the decision with someone outside your workspace. Or you want to add it to your team wiki.

`slack-thread-exporter` fetches the full thread via the Slack API and exports it to a clean, readable Markdown or HTML file — with usernames resolved, mrkdwn formatting converted, and reactions preserved.

---

## Install

```bash
pip install slack-thread-exporter
```

---

## Quick start

```bash
# Test with built-in mock data (no token needed)
slackexport --mock

# Export a real thread to Markdown
slackexport C01234567 1714500000.000100 --token xoxb-your-token

# Or set the token as an env var
export SLACK_BOT_TOKEN=xoxb-your-token
slackexport C01234567 1714500000.000100

# Export to HTML
slackexport C01234567 1714500000.000100 --format html

# Custom output file and title
slackexport C01234567 1714500000.000100 \
  --output incident-2026-04.md \
  --title "Incident Post-Mortem: Auth Service Memory Leak"
```

---

## Example output (Markdown)

```markdown
# Incident Post-Mortem: Auth Service Memory Leak

**Alice** — 2026-04-30 12:00 UTC

Has anyone looked into the memory leak in the auth service?

---

**Bob** — 2026-04-30 12:01 UTC

Yes, I traced it to the JWT cache not being cleared on logout.
The `token_cache` dict grows unbounded.

---

**Carol** — 2026-04-30 12:02 UTC

We should add a TTL or use `functools.lru_cache` with `maxsize`.
I can open a PR today.
```

---

## Setting up a Slack Bot Token

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
2. Under **OAuth & Permissions**, add these Bot Token Scopes:
   - `channels:history` — read public channel messages
   - `groups:history` — read private channel messages
   - `users:read` — resolve user IDs to names
3. Install the app to your workspace
4. Copy the **Bot User OAuth Token** (`xoxb-...`)
5. Invite the bot to the channel: `/invite @your-app-name`

---

## All flags

| Flag | Description |
|------|-------------|
| `channel` | Slack channel ID (e.g. `C01234567`) |
| `thread_ts` | Thread timestamp (e.g. `1714500000.000100`) |
| `--output FILE` | Output file path |
| `--format` | `markdown` or `html` (default: `markdown`) |
| `--title TEXT` | Document title |
| `--token KEY` | Slack Bot Token (or set `SLACK_BOT_TOKEN`) |
| `--mock` | Use built-in mock data (no token needed) |

---

## Library usage

```python
from slackexport import SlackClient, ThreadExporter

client   = SlackClient(token="xoxb-your-token")
exporter = ThreadExporter(client)

messages = exporter.fetch(channel="C01234567", thread_ts="1714500000.000100")
markdown = exporter.to_markdown(messages, title="My Thread")
html     = exporter.to_html(messages, title="My Thread")

with open("thread.md", "w") as f:
    f.write(markdown)
```

---

## Project structure

```
slack-thread-exporter/
├── slackexport/
│   ├── __init__.py      # Public API
│   ├── client.py        # Slack API wrapper + MockSlackClient
│   ├── formatter.py     # Slack mrkdwn to Markdown converter
│   ├── exporter.py      # ThreadExporter (Markdown + HTML output)
│   └── cli.py           # CLI entry point
├── tests/
│   └── test_exporter.py
└── pyproject.toml
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues labelled [`good first issue`](https://github.com/jishanahmed-shaikh/slack-thread-exporter/issues?q=label%3A%22good+first+issue%22) are a great place to start.

---

## License

[MIT](LICENSE) © 2026 [Jishanahmed AR Shaikh](https://github.com/jishanahmed-shaikh)
