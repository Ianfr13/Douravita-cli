"""Obsidian Charts plugin integration — generate Chart.js chart blocks.

Obsidian Charts renders chart codeblocks (```chart ... ```) using Chart.js.
This module generates the YAML chart block that can be inserted into notes.

Supported chart types: bar, line, pie, doughnut, radar, polarArea.
"""

import json


VALID_TYPES = ("bar", "line", "pie", "doughnut", "radar", "polarArea")

# Default color palette (accessible, distinct colors)
DEFAULT_COLORS = [
    "rgba(255, 99, 132, 0.7)",   # red
    "rgba(54, 162, 235, 0.7)",   # blue
    "rgba(255, 206, 86, 0.7)",   # yellow
    "rgba(75, 192, 192, 0.7)",   # teal
    "rgba(153, 102, 255, 0.7)",  # purple
    "rgba(255, 159, 64, 0.7)",   # orange
    "rgba(46, 204, 113, 0.7)",   # green
    "rgba(231, 76, 60, 0.7)",    # dark red
]


def generate_block(chart_type: str, labels: list[str], datasets: list[dict],
                   title: str | None = None,
                   width: str = "80%",
                   legend: bool = True,
                   stacked: bool = False,
                   begin_at_zero: bool = True) -> str:
    """Generate an Obsidian Charts YAML codeblock.

    Args:
        chart_type: Chart type (bar, line, pie, doughnut, radar, polarArea).
        labels: X-axis labels (e.g., ["Jan", "Feb", "Mar"]).
        datasets: List of dataset dicts, each with:
            - label (str): Dataset name
            - data (list[number]): Values
            - color (str, optional): Override color
        title: Optional chart title.
        width: Chart width (default: "80%").
        legend: Show legend (default: True).
        stacked: Stack bars/lines (default: False).
        begin_at_zero: Y-axis starts at 0 (default: True).

    Returns:
        Complete ```chart ... ``` codeblock string ready to insert.

    Raises:
        ValueError: If chart_type is invalid or labels/datasets are empty.
    """
    if chart_type not in VALID_TYPES:
        raise ValueError(
            f"Invalid chart type '{chart_type}'. Must be one of: {', '.join(VALID_TYPES)}"
        )
    if not labels:
        raise ValueError("Labels list cannot be empty.")
    if not datasets:
        raise ValueError("Datasets list cannot be empty.")

    lines = ["```chart", f"type: {chart_type}"]

    if title:
        lines.append(f"title: \"{title}\"")

    lines.append(f"width: {width}")
    lines.append(f"legend: {str(legend).lower()}")
    lines.append(f"beginAtZero: {str(begin_at_zero).lower()}")

    if stacked:
        lines.append("stacked: true")

    # Labels
    lines.append("labels:")
    for lbl in labels:
        lines.append(f"  - \"{lbl}\"")

    # Datasets
    lines.append("datasets:")
    for i, ds in enumerate(datasets):
        ds_label = ds.get("label", f"Dataset {i + 1}")
        ds_data = ds.get("data", [])
        ds_color = ds.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])

        lines.append(f"  - label: \"{ds_label}\"")
        lines.append(f"    backgroundColor: \"{ds_color}\"")
        lines.append(f"    borderColor: \"{ds_color.replace('0.7', '1')}\"")
        lines.append(f"    data:")
        for val in ds_data:
            lines.append(f"      - {val}")

    lines.append("```")
    return "\n".join(lines)


def bar(labels: list[str], datasets: list[dict], **kwargs) -> str:
    """Generate a bar chart block."""
    return generate_block("bar", labels, datasets, **kwargs)


def line(labels: list[str], datasets: list[dict], **kwargs) -> str:
    """Generate a line chart block."""
    return generate_block("line", labels, datasets, **kwargs)


def pie(labels: list[str], datasets: list[dict], **kwargs) -> str:
    """Generate a pie chart block."""
    return generate_block("pie", labels, datasets, **kwargs)


def doughnut(labels: list[str], datasets: list[dict], **kwargs) -> str:
    """Generate a doughnut chart block."""
    return generate_block("doughnut", labels, datasets, **kwargs)


def radar(labels: list[str], datasets: list[dict], **kwargs) -> str:
    """Generate a radar chart block."""
    return generate_block("radar", labels, datasets, **kwargs)


def insert_chart(base_url: str, api_key: str | None,
                 file: str, chart_block: str,
                 heading: str | None = None) -> dict:
    """Insert a chart block into a vault file.

    Args:
        base_url: Obsidian server base URL.
        api_key: Bearer token.
        file: File path relative to vault root.
        chart_block: The ```chart...``` block string.
        heading: Optional heading to append under. If None, appends to end.

    Returns:
        Status dict.
    """
    from cli_anything.obsidian.core import vault as vault_mod
    from cli_anything.obsidian.utils.obsidian_backend import api_patch

    content = "\n\n" + chart_block + "\n"

    if heading:
        from cli_anything.obsidian.utils.obsidian_backend import encode_path
        encoded = encode_path(file)
        return api_patch(
            base_url, f"/vault/{encoded}", api_key=api_key, body=content,
            operation="append", target_type="heading", target=heading,
        )
    else:
        return vault_mod.append(base_url, api_key, file, content)
