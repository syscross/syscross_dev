# /// script
# dependencies = ["markdown", "pymdown-extensions"]
# ///

from pathlib import Path
import re
import shutil
import markdown
import pymdownx.superfences

DEV_DIR = Path(__file__).resolve().parent
TARGET_DIR = DEV_DIR / ".target"

EXTENSIONS = [
    "extra",
    "admonition",
    "sane_lists",
    "toc",
    "wikilinks",
    "pymdownx.superfences",
    "pymdownx.highlight",
    "pymdownx.inlinehilite",
    "pymdownx.arithmatex",
    "pymdownx.tasklist",
    "pymdownx.tilde",
    "pymdownx.caret",
    "pymdownx.mark",
    "pymdownx.magiclink",
    "pymdownx.details",
    "pymdownx.keys",
    "pymdownx.saneheaders",
]

EXTENSION_CONFIGS = {
    "wikilinks": {"base_url": "/", "end_url": ""},
    "pymdownx.arithmatex": {"generic": True},
    "pymdownx.highlight": {"use_pygments": False},
    "pymdownx.superfences": {
        "custom_fences": [
            {
                "name": "mermaid",
                "class": "mermaid",
                "format": pymdownx.superfences.fence_div_format,
            }
        ]
    },
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SysCross</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.8.1/github-markdown.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css" media="(prefers-color-scheme: light)">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github-dark.min.css" media="(prefers-color-scheme: dark)">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            background-color: #ffffff;
        }
        @media (prefers-color-scheme: dark) {
            body { background-color: #0d1117; }
        }
        .markdown-body, .markdown-body pre, .markdown-body code, .markdown-body tt {
            font-family: "Noto Sans Mono CJK JP", "Noto Sans Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        }
        .markdown-body {
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
        }
        @media (max-width: 767px) {
            .markdown-body { padding: 15px; }
        }
    </style>
    <script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.21/dist/contrib/auto-render.min.js"></script>
    <script type="module">
        import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
        const isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        mermaid.initialize({ startOnLoad: true, theme: isDark ? "dark" : "default" });
        window.addEventListener("DOMContentLoaded", () => {
            if (window.hljs) hljs.highlightAll();
            if (window.renderMathInElement) renderMathInElement(document.body);
        });
    </script>
</head>
<body class="markdown-body">
{body}
</body>
</html>
"""


def build() -> None:
    if TARGET_DIR.exists():
        shutil.rmtree(TARGET_DIR)
    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    for md_path in DEV_DIR.rglob("*.md"):
        rel = md_path.relative_to(DEV_DIR)
        if any(part.startswith(".") for part in rel.parts):
            continue

        out_rel = rel.with_name("index.html") if rel.name.lower() == "readme.md" else rel.with_suffix(".html")
        out_path = TARGET_DIR / out_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)

        raw_md = md_path.read_text(encoding="utf-8")
        clean_md = re.sub(r"\A---\r?\n.*?\r?\n---\r?\n?", "", raw_md, flags=re.DOTALL)
        body = markdown.markdown(
            clean_md,
            extensions=EXTENSIONS,
            extension_configs=EXTENSION_CONFIGS,
        )
        out_path.write_text(HTML_TEMPLATE.replace("{body}", body), encoding="utf-8")
        print(f"{rel} -> .target/{out_rel}")


if __name__ == "__main__":
    build()
