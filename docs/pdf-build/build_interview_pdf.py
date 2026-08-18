#!/usr/bin/env python3
"""Convert CalTrack_Interview_Preparation.md to professional HTML for Chrome PDF."""

from __future__ import annotations

import html
import pathlib
import re
import sys

import markdown
from pymdownx.superfences import fence_div_format

ROOT = pathlib.Path(__file__).resolve().parents[2]
MD_PATH = ROOT / "docs" / "CalTrack_Interview_Preparation.md"
OUT_HTML = ROOT / "docs" / "pdf-build" / "CalTrack_Interview_Preparation.html"
CSS_PATH = pathlib.Path(__file__).with_name("print.css")


def mermaid_formatter(source, language, css_class, options, md, classes=None, id_value="", attrs=None, **kwargs):
    body = html.escape(source.strip())
    return f'<div class="diagram"><pre class="mermaid">{body}</pre></div>'


def convert(md_text: str) -> str:
    ext = [
        "tables",
        "fenced_code",
        "codehilite",
        "toc",
        "sane_lists",
        "attr_list",
        "pymdownx.superfences",
    ]
    configs = {
        "codehilite": {"linenums": False, "guess_lang": False, "noclasses": True},
        "toc": {"permalink": False, "toc_depth": "2-3"},
        "pymdownx.superfences": {
            "custom_fences": [
                {
                    "name": "mermaid",
                    "class": "mermaid",
                    "format": mermaid_formatter,
                }
            ]
        },
    }
    return markdown.markdown(md_text, extensions=ext, extension_configs=configs)


COVER = """
<section class="cover">
  <p class="cover-kicker">Technical handbook</p>
  <h1 class="cover-title">CalTrack</h1>
  <p class="cover-subtitle">Complete Technical &amp; Interview Preparation Guide</p>
  <dl class="cover-meta">
    <div><dt>Project</dt><dd>CalTrack — personal calorie and nutrition tracker</dd></div>
    <div><dt>Audience</dt><dd>Technical interviews (architecture, auth, API, deploy)</dd></div>
    <div><dt>Source</dt><dd>Codebase inspection of Prudhvi-60/CalTrack</dd></div>
    <div><dt>Companion analysis</dt><dd>docs/CALTRACK_INTERVIEW_PREP.md (unchanged)</dd></div>
  </dl>
  <p class="cover-note">Facts are from imports and call chains. Unused dependencies are labeled unused. Secrets are not included.</p>
</section>
"""


def wrap(body: str, css: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>CalTrack — Technical &amp; Interview Preparation Guide</title>
  <style>{css}</style>
  <script src="./mermaid.min.js"></script>
  <script>
    mermaid.initialize({{
      startOnLoad: false,
      theme: 'base',
      securityLevel: 'strict',
      fontFamily: 'Georgia, serif',
      themeVariables: {{
        primaryColor: '#e8f0ec',
        primaryTextColor: '#1c2b24',
        primaryBorderColor: '#245c4a',
        lineColor: '#3d5c4f',
        secondaryColor: '#f4f1ea',
        tertiaryColor: '#ffffff',
        background: '#ffffff'
      }}
    }});
  </script>
</head>
<body>
{COVER}
<article class="doc">
{body}
</article>
</body>
</html>
"""


def main() -> int:
    md_text = MD_PATH.read_text(encoding="utf-8")
    # Cover is generated in HTML; skip duplicate H1 block in the markdown body.
    md_text = re.sub(
        r"^# CALTRACK\n\n## Complete Technical & Interview Preparation Guide\n\n.*?\n---\n",
        "",
        md_text,
        count=1,
        flags=re.S,
    )
    body = convert(md_text)
    css = CSS_PATH.read_text(encoding="utf-8")
    OUT_HTML.write_text(wrap(body, css), encoding="utf-8")
    print(f"Wrote {OUT_HTML}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
