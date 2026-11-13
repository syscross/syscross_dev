# /// script
# dependencies = ["markdown", "pymdown-extensions"]
# ///

from dataclasses import dataclass, field
from pathlib import Path
import re
import shutil
import markdown
import pymdownx.superfences

DEV_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = DEV_DIR / ".target"
SOURCE_DIR = DEV_DIR / ".source"

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

# 틀과 틀 조각은 .source에 있고, 빌드 결과만 .target에 나옴
HTML_TEMPLATE = (SOURCE_DIR / "template.html").read_text(encoding="utf-8")
ARTICLE_BAR = (SOURCE_DIR / "article-bar.html").read_text(encoding="utf-8")
CATEGORY_BAR = (SOURCE_DIR / "category-bar.html").read_text(encoding="utf-8")


# ---------------------------------------------------------------- 프론트매터 / 마크다운

def read_front(raw: str) -> dict:
    """맨 앞 프론트매터의 `key: value` 줄을 dict로 읽음."""
    meta = {}
    match = re.match(r"\A---\r?\n(.*?)\r?\n---", raw, flags=re.DOTALL)
    if match:
        for line in match.group(1).splitlines():
            kv = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*$", line)
            if kv:
                meta[kv.group(1)] = kv.group(2)
    return meta


def strip_front(raw: str) -> str:
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n?", "", raw, flags=re.DOTALL)


def plain(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).strip()


def page_title(clean_md: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+?)\s*$", clean_md, flags=re.MULTILINE)
    return match.group(1) if match else fallback


# 제목 영역(hero): 프론트매터 hero가 있으면 맨 앞의 h1을 배경 이미지가 깔린 영역으로 감쌈
# 부제는 h1 바로 다음에 문단이 딱 하나 있고, 그 뒤에 구분선(---)이 올 때만 인정하며 구분선도 영역 안에 흡수함
HERO_TITLE = re.compile(r"\A(\s*<h1\b.*?</h1>)", re.DOTALL)
HERO_SUBTITLE = re.compile(r"\A(\s*<h1\b.*?</h1>\s*<p>(?:(?!</p>).)*</p>)\s*<hr\s*/?>", re.DOTALL)


def wrap_hero(body: str, image: str, position: str = "center") -> str:
    def repl(match: re.Match) -> str:
        return (
            f'<header class="hero" style="--hero-image: url({image}); --hero-position: {position}">'
            f'{match.group(1).strip()}</header>\n'
        )
    if HERO_SUBTITLE.match(body):
        return HERO_SUBTITLE.sub(repl, body, count=1)
    return HERO_TITLE.sub(repl, body, count=1)


# ---------------------------------------------------------------- 구조: 카테고리(폴더) > 글(md)

@dataclass
class Article:
    out_rel: Path
    href: str
    title: str
    en: str
    thumb: str
    body: str


@dataclass
class Category:
    folder: str
    href: str
    title: str
    en: str
    image: str
    image_alt: str
    articles: list[Article] = field(default_factory=list)


def load_article(md_path: Path, folder: str) -> Article:
    raw = md_path.read_text(encoding="utf-8")
    front = read_front(raw)
    clean = strip_front(raw)
    body = markdown.markdown(clean, extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS)

    # 목록에 쓸 영문 부제: h1 바로 다음 문단(구분선이 뒤따를 때만)
    en = ""
    sub = HERO_SUBTITLE.match(body)
    if sub:
        para = re.search(r"<p>(.*?)</p>", sub.group(1), re.DOTALL)
        en = plain(para.group(1)) if para else ""

    if "hero" in front:
        body = wrap_hero(body, front["hero"], front.get("hero_position", "center"))

    out_rel = Path(folder) / f"{md_path.stem}.html"
    return Article(
        out_rel=out_rel,
        href="/" + out_rel.with_suffix("").as_posix(),
        title=page_title(clean, md_path.stem),
        en=en,
        thumb=front.get("thumb", ""),
        body=body,
    )


def collect_categories() -> list[Category]:
    """최상위 폴더 중 README.md가 있는 곳이 카테고리. README 프론트매터가 카테고리 정보."""
    categories = []
    folders = sorted(
        (p for p in DEV_DIR.iterdir() if p.is_dir() and not p.name.startswith(".") and (p / "README.md").exists()),
        key=lambda p: p.name,
    )
    for folder in folders:
        meta = read_front((folder / "README.md").read_text(encoding="utf-8"))
        articles = [
            load_article(md, folder.name)
            for md in sorted(folder.glob("*.md"))
            if md.name.lower() != "readme.md"
        ]
        categories.append(Category(
            folder=folder.name,
            href=f"/{folder.name}/",
            title=meta.get("title", folder.name),
            en=meta.get("en", ""),
            image=meta.get("image", ""),
            image_alt=meta.get("image_alt", ""),
            articles=articles,
        ))
    return categories


# ---------------------------------------------------------------- 조각 렌더링

def render_cards(categories: list[Category]) -> str:
    cards = []
    for cat in categories:
        cards.append(
            f'<a class="card" href="{cat.href}">\n'
            f'    <span class="card-photo">\n'
            f'        <img src="{cat.image}" alt="{cat.image_alt}">\n'
            f'    </span>\n'
            f'    <span class="card-label">\n'
            f'        <span class="label-ko">{cat.title}</span>\n'
            f'        <span class="label-en">{cat.en}</span>\n'
            f'    </span>\n'
            f'</a>'
        )
    return "\n".join(cards)


def render_list(cat: Category) -> str:
    if not cat.articles:
        return '<p class="empty-list">아직 글이 없습니다.</p>'
    items = []
    for art in cat.articles:
        thumb = f'<img class="thin-thumb" src="{art.thumb}" alt="">' if art.thumb else ""
        items.append(
            f'<li><a class="thin-card" href="{art.href}">{thumb}'
            f'<div class="thin-text"><div class="thin-ko">{art.title}</div>'
            f'<div class="thin-en">{art.en}</div></div></a></li>'
        )
    return '<ul class="thin-list">\n' + "\n".join(items) + "\n</ul>"


def render_index(categories: list[Category]) -> str:
    """좌측 사이드바: 카테고리 > 글"""
    lines = []
    for cat in categories:
        lines.append(f'<li><a href="{cat.href}">{cat.title}</a></li>')
        lines += [f'<li class="sub"><a href="{art.href}">{art.title}</a></li>' for art in cat.articles]
    return "\n".join(lines)


# 우측 사이드바: 현재 글의 소제목(h2) 목록
TOC_HEADING = re.compile(r'<h2 id="([^"]+)">(.*?)</h2>', re.DOTALL)


def render_toc(body: str) -> str:
    return "\n".join(f'<li><a href="#{m.group(1)}">{m.group(2)}</a></li>' for m in TOC_HEADING.finditer(body))


RIGHT_FALLBACK = (
    '<div class="drawer-empty">'
    '<a class="drawer-contact" href="mailto:syscross@proton.me">'
    '<span class="contact-icon" aria-hidden="true">✉️</span>'
    '<span>syscross@proton.me</span>'
    '</a>'
    '</div>'
)


def render_right(toc: str) -> str:
    if toc:
        return f'    <ul class="drawer-list drawer-toc">\n{toc}\n    </ul>'
    return f'    {RIGHT_FALLBACK}'


# ---------------------------------------------------------------- 페이지 조립

def compose(intro: str, body: str, left: str, right: str, html_cls: str = "", body_cls: str = "") -> str:
    html = (
        HTML_TEMPLATE
        .replace("{left}", left)
        .replace("{right}", render_right(right))
        .replace("{intro}", intro)
        .replace("{body}", body)
    )
    if html_cls:
        html = html.replace('<html lang="en">', f'<html lang="en" class="{html_cls}">', 1)
    if body_cls:
        html = html.replace("<body>", f'<body class="{body_cls}">', 1)
    return html


def write(out_path: Path, html: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    print(f"{out_path.relative_to(OUTPUT_DIR)} -> .target/{out_path.relative_to(OUTPUT_DIR)}")


def build() -> None:
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 정적 자산은 .source/assets에서 .target/assets로 그대로 복사
    assets_dir = SOURCE_DIR / "assets"
    if assets_dir.exists():
        shutil.copytree(assets_dir, OUTPUT_DIR / "assets")

    categories = collect_categories()
    left = render_index(categories)

    # 메인: 카테고리 카드
    write(OUTPUT_DIR / "index.html", compose(
        intro=render_cards(categories), body="", left=left, right=""))

    for cat in categories:
        # 카테고리 화면: 상단 하위 바 + 글 목록
        intro = CATEGORY_BAR.replace("{title}", cat.title).replace("{list}", render_list(cat))
        write(OUTPUT_DIR / cat.folder / "index.html", compose(
            intro=intro, body="", left=left, right="", html_cls="section-view"))

        for art in cat.articles:
            # 글: 제목 영역 바로 아래에 뒤로 바(카테고리로 돌아감)를 놓고 본문을 이어 씀
            bar = (ARTICLE_BAR
                   .replace("{title}", art.title)
                   .replace("{category_href}", cat.href)
                   .replace("{category_title}", cat.title))
            if "</header>" in art.body:
                content = art.body.replace("</header>", "</header>\n" + bar, 1)
            else:
                content = bar + art.body
            write(OUTPUT_DIR / art.out_rel, compose(
                intro="", body=content, left=left, right=render_toc(art.body), body_cls="article-view"))


if __name__ == "__main__":
    build()
