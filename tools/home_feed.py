"""Create a compact homepage feed from the generated category archives."""

from __future__ import annotations

import json
import re
import subprocess
import unicodedata
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote


class CategoryParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.categories = []
        self.in_list = False
        self.in_link = False
        self.href = ""
        self.name = ""

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "ul" and "category-list" in attrs.get("class", ""):
            self.in_list = True
        elif self.in_list and tag == "a":
            self.in_link = True
            self.href = attrs.get("href", "")
            self.name = ""

    def handle_data(self, data):
        if self.in_link:
            self.name += data

    def handle_endtag(self, tag):
        if tag == "a" and self.in_link:
            self.categories.append((self.name.strip(), self.href))
            self.in_link = False
        elif tag == "ul" and self.in_list:
            self.in_list = False


CARD = re.compile(
    r'<article class="card"><p class="eyebrow">([^<]*)</p>'
    r'<h3><a href="([^"]+)">([^<]*)</a></h3>', re.DOTALL
)
COUNT = re.compile(r"<p>([\d,]+) artigos</p>")
SIZE = re.compile(r"-(?:\d+x\d+)(?:@2x)?$")


def image_index(docs: Path):
    media = docs / "media" / "uploads"
    if media.exists():
        paths = [path.relative_to(docs).as_posix() for path in media.rglob("*") if path.is_file()]
    else:
        # Sparse checkouts still contain the published media paths in Git's tree.
        result = subprocess.run(
            ["git", "-c", "core.quotepath=false", "ls-tree", "-r", "--name-only", "HEAD", "docs/media/uploads"],
            cwd=docs.parent, capture_output=True, text=True, encoding="utf-8", check=True,
        )
        paths = [path.removeprefix("docs/") for path in result.stdout.splitlines()]
    found = {}
    for path in paths:
        file = Path(path)
        if file.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            continue
        stem = SIZE.sub("", file.stem)
        key = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode().lower()
        key = re.sub(r"[^a-z0-9]+", "-", key).strip("-")
        score = 2 if re.search(r"-(?:438x246|300x168|255x193)$", file.stem) else 1
        if key not in found or score > found[key][0]:
            found[key] = (score, "/saudeteu/" + quote(path, safe="/"))
    return {key: value[1] for key, value in found.items()}


def generate(docs: Path):
    images = image_index(docs)
    listing = CategoryParser()
    listing.feed((docs / "categories" / "index.html").read_text(encoding="utf-8"))
    categories = []
    for name, url in listing.categories:
        relative = url.removeprefix("/saudeteu/")
        archive = docs / relative / "index.html"
        if not archive.is_file():
            continue
        source = archive.read_text(encoding="utf-8")
        count = COUNT.search(source)
        posts = []
        for date, post_url, title in CARD.findall(source)[:21]:
            post_url = unescape(post_url)
            post = {"date": unescape(date), "url": post_url, "title": unescape(title)}
            slug = post_url.rstrip("/").rsplit("/", 1)[-1].rsplit("--", 1)[0]
            if slug in images:
                post["image"] = images[slug]
            posts.append(post)
        if posts:
            categories.append({"name": name, "url": url, "count": int(count.group(1).replace(",", "")) if count else len(posts), "posts": posts})
    if not categories:
        raise ValueError("No populated category archives found")
    categories.sort(key=lambda category: (-category["count"], category["name"].casefold()))
    target = docs / "assets" / "home-feed.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(categories, ensure_ascii=False, separators=(",", ":")) + "\n")
    return len(categories)


if __name__ == "__main__":
    print(f"Generated {generate(Path(__file__).resolve().parents[1] / 'docs')} category previews")
