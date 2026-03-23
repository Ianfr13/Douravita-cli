"""Output formatters for cli-anything-langfuse.

Handles human-readable and JSON output modes.
"""

import json
import sys
from datetime import datetime
from typing import Any


def output_json(data: Any) -> None:
    """Print data as formatted JSON to stdout."""
    print(json.dumps(data, indent=2, default=_json_serializer))


def output_table(headers: list[str], rows: list[list[str]], skin=None) -> None:
    """Print data as a formatted table.

    Args:
        headers: Column headers.
        rows: Rows of data.
        skin: Optional ReplSkin instance for styled output.
    """
    if skin:
        skin.table(headers, rows)
    else:
        _simple_table(headers, rows)


def _simple_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a simple ASCII table without ANSI colors."""
    if not headers:
        return

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    # Cap widths
    col_widths = [min(w, 50) for w in col_widths]

    def pad(text: str, width: int) -> str:
        t = str(text)[:width]
        return t + " " * (width - len(t))

    header_line = " | ".join(pad(h, col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * w for w in col_widths)

    print(header_line)
    print(sep_line)
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            if i < len(col_widths):
                cells.append(pad(str(cell), col_widths[i]))
        print(" | ".join(cells))


def format_timestamp(ts: str | None) -> str:
    """Format an ISO timestamp to a shorter display form."""
    if not ts:
        return "-"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return ts[:19] if len(ts) > 19 else ts


def format_cost(cost: float | None) -> str:
    """Format a USD cost value."""
    if cost is None:
        return "-"
    if cost < 0.01:
        return f"${cost:.4f}"
    return f"${cost:.2f}"


def format_latency(latency: float | None) -> str:
    """Format latency in seconds to human-readable."""
    if latency is None:
        return "-"
    if latency < 1:
        return f"{latency * 1000:.0f}ms"
    return f"{latency:.2f}s"


def truncate(text: str | None, max_len: int = 60) -> str:
    """Truncate text for table display."""
    if text is None:
        return "-"
    text = str(text).replace("\n", " ")
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def _json_serializer(obj):
    """JSON serializer for objects not serializable by default."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)
