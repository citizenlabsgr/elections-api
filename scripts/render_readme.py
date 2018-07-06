"""Render the static homepage from the README."""

import sys
from pathlib import Path

import grip


def run(input_markdown_path, output_html_path):
    markdown = ""

    with Path(input_markdown_path).open('r') as f:
        for line in f:
            if '-- skip --' in line:
                continue
            line = line.replace('https://michiganelections.io', '')
            markdown += line

    html = grip.render_page(
        text=markdown, title="Michigan Elections API", render_inline=True
    )

    with Path(output_html_path).open('w') as f:
        f.write(html)


def main():
    run(sys.argv[1], sys.argv[2])
