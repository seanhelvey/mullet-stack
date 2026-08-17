# /// script
# requires-python = ">=3.12"
# dependencies = ["markdown>=3.6", "pymdown-extensions>=10.9", "pygments>=2.18"]
# ///
"""Render zine.md into a single self-contained zine.html.

Run it with `uv run zine/build.py` — uv reads the dependency block above and
fetches the packages into a throwaway environment, so there is nothing to
install and no virtualenv to manage.

Open the result in a browser to read it, or print it (Ctrl/Cmd+P) for a PDF.
"""

import base64
import html
import pathlib

import markdown
from pygments.formatters import HtmlFormatter

HERE = pathlib.Path(__file__).parent
LIGHT, DARK = "friendly", "github-dark"

EXTENSIONS = [
    "meta",              # the --- front matter block at the top of zine.md
    "smarty",            # straight quotes -> curly
    "toc",               # heading anchors + the contents list
    "tables",
    "attr_list",
    "pymdownx.superfences",       # fenced code, maintained successor to fenced_code
    "pymdownx.highlight",         # ditto for codehilite
    "pymdownx.inlinehilite",
    "pymdownx.blocks.admonition",  # the /// aside | ... sidebars
]

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
<header class="masthead">
<h1 class="title">{title}</h1>
<p class="subtitle">{subtitle}</p>
<p class="byline">{byline}</p>
</header>
<nav class="contents">
<h2>Contents</h2>
{toc}
</nav>
{body}
</body>
</html>
"""


def font_face():
    """Embed the display face so the zine looks the same on every machine.

    fonts/ holds a Latin subset of Lato Black (SIL OFL, license alongside it).
    Inlining it as a data URI keeps zine.html a single portable file and means
    the design never silently degrades to whatever sans the reader happens to
    have installed.
    """
    woff2 = (HERE / "fonts" / "lato-black-subset.woff2").read_bytes()
    encoded = base64.b64encode(woff2).decode("ascii")
    return (
        "@font-face {\n"
        "  font-family: 'Lato Zine';\n"
        "  font-style: normal;\n"
        "  font-weight: 900;\n"
        "  font-display: swap;\n"
        f"  src: url(data:font/woff2;base64,{encoded}) format('woff2');\n"
        "}"
    )


def stylesheet():
    """style.css, plus the display face and a Pygments theme for each medium."""
    # Dark rules apply only when the reader's OS asks for dark. The light
    # rules are emitted again for print so a dark-mode browser still prints
    # readable code rather than slabs of black ink.
    light = HtmlFormatter(style=LIGHT).get_style_defs(".highlight")
    dark = HtmlFormatter(style=DARK).get_style_defs(".highlight")
    return "\n".join(
        [
            font_face(),
            (HERE / "style.css").read_text(encoding="utf-8"),
            light,
            f"@media (prefers-color-scheme: dark) {{\n{dark}\n}}",
            f"@media print {{\n{light}\n}}",
        ]
    )


def main():
    md = markdown.Markdown(
        extensions=EXTENSIONS,
        extension_configs={
            "pymdownx.highlight": {"pygments_style": LIGHT, "guess_lang": False},
            # `aside` isn't a built-in admonition type; register it so
            # `/// aside | Title` blocks in zine.md render as sidebars.
            "pymdownx.blocks.admonition": {"types": ["aside"]},
        },
    )
    body = md.convert((HERE / "zine.md").read_text(encoding="utf-8"))
    meta = {key: value[0].strip('"') for key, value in md.Meta.items()}

    page = PAGE.format(
        title=html.escape(meta.get("title", "Zine")),
        subtitle=html.escape(meta.get("subtitle", "")),
        byline=html.escape(" · ".join(meta[k] for k in ("author", "date") if k in meta)),
        toc=md.toc,
        body=body,
        css=stylesheet(),
    )

    out = HERE / "zine.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out.relative_to(HERE.parent)} ({len(page):,} bytes)")


if __name__ == "__main__":
    main()
