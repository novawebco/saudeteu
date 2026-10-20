"""Create a compact homepage feed from the generated category archives."""

from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


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


def generate(docs: Path):
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
        posts = [
            {"date": unescape(date), "url": unescape(link), "title": unescape(title)}
            for date, link, title in CARD.findall(source)[:6]
        ]
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
