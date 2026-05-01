"""CLI for slack-thread-exporter."""

from __future__ import annotations

import argparse
import os
import sys

from slackexport import __version__
from slackexport.client import MockSlackClient, SlackClient
from slackexport.exporter import ThreadExporter, export_thread


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="slackexport",
        description="Export a Slack thread to Markdown or HTML.",
    )
    parser.add_argument("channel",   nargs="?", help="Slack channel ID (e.g. C01234567)")
    parser.add_argument("thread_ts", nargs="?", help="Thread timestamp (e.g. 1714500000.000100)")
    parser.add_argument("--output",  "-o", metavar="FILE",
                        help="Output file path (default: thread_<ts>.md)")
    parser.add_argument("--format",  "-f", choices=["markdown", "html"], default="markdown",
                        help="Output format (default: markdown)")
    parser.add_argument("--title",   default="Slack Thread",
                        help="Document title (default: 'Slack Thread')")
    parser.add_argument("--token",   default=os.environ.get("SLACK_BOT_TOKEN", ""),
                        help="Slack Bot Token (or set SLACK_BOT_TOKEN env var)")
    parser.add_argument("--mock",   action="store_true",
                        help="Use mock data (no Slack token required, for testing)")
    parser.add_argument("--no-resolve-usernames",   action="store_true",
                        help="Skip resolving usernames and use raw user IDs")
    parser.add_argument("--version", "-V", action="version",
                        version=f"%(prog)s {__version__}")

    args = parser.parse_args(argv)

    if args.mock:
        mock = MockSlackClient()
        channel   = mock.MOCK_CHANNEL
        thread_ts = mock.MOCK_THREAD_TS
        client    = mock
    else:
        if not args.channel or not args.thread_ts:
            parser.error("channel and thread_ts are required (or use --mock)")
        if not args.token:
            print(
                "Error: Slack Bot Token required.\n"
                "Set SLACK_BOT_TOKEN env var or use --token.\n"
                "Use --mock to test without a token.",
                file=sys.stderr,
            )
            sys.exit(1)
        channel   = args.channel
        thread_ts = args.thread_ts
        client    = SlackClient(token=args.token)

    ext = "html" if args.format == "html" else "md"
    output = args.output or f"thread_{thread_ts.replace('.', '_')}.{ext}"

    try:
        path = export_thread(
            channel=channel,
            thread_ts=thread_ts,
            client=client,
            output_path=output,
            fmt=args.format,
            title=args.title,
            no_resolve_usernames=args.no_resolve_usernames
        )
        print(f"  Exported to {path}")
    except (ConnectionError, PermissionError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
