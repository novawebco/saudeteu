#!/usr/bin/env python3
"""Build a static, read-only GitHub Pages site from the verified WordPress export."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

from home_feed import generate as generate_home_feed

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "export"
DOCS = ROOT / "docs"
SITE_ORIGIN = "https://lamberdar8singh.github.io"
SITE_URL = SITE_ORIGIN + "/saudeteu"
BASE_PATH = "/saudeteu"
PER_PAGE = 100


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value: str) -> str:
    parser = TextOnly()
    try:
        parser.feed(value or "")
        return " ".join(" ".join(parser.parts).split())
    except Exception:
        return " ".join(re.sub(r"<[^>]*>", " ", value or "").split())


def safe_slug(value: str, fallback: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", value or "").strip("-_")
    return (slug[:100] or fallback)


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def media_maps():
    by_id, by_url = {}, {}
    for item in read_jsonl(EXPORT / "media-manifest.jsonl"):
        paths = [f for f in item.get("files", []) if f.get("available")]
        if not paths:
            continue
        chosen = next((f for f in paths if f.get("archive_path") == item.get("guid", "").split("/wp-content/")[-1]), paths[0])
        rel = chosen["local_path"].replace("\\", "/")
        url = f"{BASE_PATH}/{rel}"
        if item.get("ID") is not None:
            by_id[str(item["ID"])] = url
        guid = item.get("guid")
        if guid:
            by_url[guid] = url
        for f in paths:
            archive = f.get("archive_path", "")
            if archive.startswith("uploads/"):
                by_url["/wp-content/" + archive] = f"{BASE_PATH}/media/{archive}"
    return by_id, by_url


def rewrite_media(body: str, by_url: dict) -> str:
    # Only point source-site upload URLs at files that the backup actually contains.
    def replace(match):
        original = match.group(0)
        tail = match.group(1)
        for key in ("/wp-content/uploads/" + tail, "https://saudeteu.info/wp-content/uploads/" + tail,
                    "http://saudeteu.info/wp-content/uploads/" + tail):
            if key in by_url:
                return by_url[key]
        return original

    return re.sub(r"(?:https?://saudeteu\.info)?/wp-content/uploads/([^\"'<>\s)]+)", replace, body or "")


def shell(title: str, description: str, content: str, canonical: str, page_title: str | None = None):
    title_full = page_title or f"{title} | Saúde Teu"
    return f'''<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' https: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-src https:; object-src 'none'; base-uri 'self'">
<title>{esc(title_full)}</title><meta name="description" content="{esc(description[:300])}">
<link rel="canonical" href="{esc(canonical)}"><link rel="stylesheet" href="{BASE_PATH}/assets/site.css">
<link rel="icon" href="{BASE_PATH}/favicon.svg" type="image/svg+xml">
</head><body><header class="site-header"><div class="header-inner"><a class="brand" href="{BASE_PATH}/">Saúde Teu</a><nav class="site-nav" aria-label="Navegação principal"><a href="{BASE_PATH}/">Início</a><a href="{BASE_PATH}/categories/">Categorias</a><a href="{BASE_PATH}/pages/">Páginas</a></nav></div></header>
<main id="main-content">{content}</main><footer><div class="footer-inner"><div><h2>Saúde Teu</h2><p>Informação sobre saúde, alimentação e bem-estar. O conteúdo é informativo e não substitui orientação, diagnóstico ou tratamento por um profissional de saúde.</p></div><div><h3>Saúde Teu</h3><ul class="footer-links"><li><a href="{BASE_PATH}/pages/sobre-nos--15604/">Sobre nós</a></li><li><a href="{BASE_PATH}/pages/contact--101/">Contato</a></li><li><a href="{BASE_PATH}/pages/politica-de-privacidade--15608/">Política de privacidade</a></li><li><a href="{BASE_PATH}/pages/aviso-legal--15985/">Aviso legal</a></li></ul></div><div><h3>Acompanhe</h3><ul class="social-links"><li><a href="https://twitter.com/saudeteu/">X / Twitter</a></li><li><a href="https://www.instagram.com/saudeteu/">Instagram</a></li><li><a href="https://pinterest.com/saudeteu/">Pinterest</a></li><li><a href="https://www.facebook.com/Saudeteuofficial/">Facebook</a></li><li><a href="https://www.linkedin.com/saude-teu/">LinkedIn</a></li></ul></div></div></footer>
<script src="{BASE_PATH}/assets/site.js" defer></script></body></html>'''


def article_url(item):
    ident = int(item["ID"])
    slug = safe_slug(item.get("post_name", ""), "post")
    return f"{BASE_PATH}/posts/{ident % 100:02d}/{slug}--{ident}/"


def date_key(item):
    return item.get("post_date_gmt") or item.get("post_date") or "0000-00-00 00:00:00"


def category_info(item):
    result = []
    for rel in item.get("categories", []):
        term = rel.get("term") or {}
        if not term.get("term_id"):
            continue
        result.append({"id": term["term_id"], "name": term.get("name", "Category"), "slug": term.get("slug", "category")})
    return result


def build():
    if not (EXPORT / "manifest.json").exists():
        raise SystemExit("Verified export manifest missing; refusing to build site.")
    manifest = json.loads((EXPORT / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("validation", {}).get("state") != "passed":
        raise SystemExit("Export validation has not passed; refusing to publish.")

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "assets").mkdir()
    write_text(DOCS / "assets/site.css", (ROOT / "tools/site.css").read_text(encoding="utf-8"))
    write_text(DOCS / "assets/site.js", (ROOT / "tools/site.js").read_text(encoding="utf-8"))
    write_text(DOCS / "favicon.svg", '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#0f766e"/><path d="M28 12h8v16h16v8H36v16h-8V36H12v-8h16z" fill="white"/></svg>')

    # Copy only actual upload media into the publish tree, preserving bytes.
    src_media = EXPORT / "media" / "uploads"
    if src_media.exists():
        shutil.copytree(src_media, DOCS / "media" / "uploads")
    media_by_id, media_by_url = media_maps()

    records = []
    categories = defaultdict(list)
    pages = []
    index_parts = sorted(EXPORT.glob("posts*.jsonl"), key=lambda p: p.name)
    if (EXPORT / "pages.jsonl").exists():
        index_parts.append(EXPORT / "pages.jsonl")
    for part in index_parts:
        for item in read_jsonl(part):
            if item.get("post_status") != "publish":
                continue
            kind = item.get("post_type")
            if kind not in ("post", "page"):
                continue
            body = item.get("post_content") or ""
            title = item.get("post_title") or ""
            slug = safe_slug(item.get("post_name", ""), "page" if kind == "page" else "post")
            url = article_url(item) if kind == "post" else f"{BASE_PATH}/pages/{slug}--{item['ID']}/"
            cats = category_info(item) if kind == "post" else []
            rec = {"ID": int(item["ID"]), "title": title, "slug": item.get("post_name", ""), "date": item.get("post_date", ""),
                   "modified": item.get("post_modified", ""), "excerpt": plain_text(item.get("post_excerpt", ""))[:400],
                   "url": url, "type": kind, "categories": cats}
            records.append(rec)
            if kind == "page":
                pages.append(rec)
            for cat in cats:
                categories[(int(cat["id"]), cat["slug"], cat["name"])].append(rec)

            # Render this source row immediately so the full postmeta-heavy JSON
            # object is released before the next line is parsed.
            target = DOCS / Path(url.removeprefix(BASE_PATH + "/")) / "index.html"
            categories_html = " ".join(f'<a class="chip" href="{BASE_PATH}/categories/{safe_slug(c["slug"],"category")}--{c["id"]}/">{esc(c["name"])}</a>' for c in cats)
            image = ""
            for media_id in item.get("featured_image_ids", []):
                if str(media_id) in media_by_id:
                    image = f'<img class="featured" src="{media_by_id[str(media_id)]}" alt="">'
                    break
            byline = '<p class="article-byline">Por <strong>Dr. Amber Pelloe, MD</strong></p>' if kind == "post" else ""
            content = f'<article><p class="eyebrow">{esc(rec["date"][:10])} · {"Artigo" if kind=="post" else "Página"}</p><h1>{esc(title)}</h1>{byline}<div class="chips">{categories_html}</div>{image}<div class="article-body">{rewrite_media(body, media_by_url)}</div></article>'
            write_text(target, shell(title, rec["excerpt"], content, SITE_ORIGIN + url))

    if not records:
        raise SystemExit("No published posts/pages found; refusing to deploy an empty site.")
    records.sort(key=lambda rec: (rec.get("date", ""), rec["ID"]), reverse=True)
    post_rows = [r for r in records if r["type"] == "post"]

    # Search index is fetched only when a reader searches; it contains no body text.
    search_index = [{k: r[k] for k in ("ID", "title", "excerpt", "url", "date", "type")} for r in records]
    write_text(DOCS / "search-index.json", json.dumps(search_index, ensure_ascii=False, separators=(",", ":")))

    # Paginated home listing.
    total_pages = (len(post_rows) + PER_PAGE - 1) // PER_PAGE
    for page_no in range(total_pages):
        group = post_rows[page_no * PER_PAGE:(page_no + 1) * PER_PAGE]
        cards = "".join(card(rec) for rec in group)
        nav = pagination(page_no + 1, total_pages, "")
        content = f'<section class="hero"><p class="eyebrow">Arquivo de artigos</p><h1>Saúde, bem-estar e informação</h1><p>{len(post_rows):,} artigos preservados do backup.</p><form id="search-form"><label for="search-q">Buscar artigos</label><div class="search-row"><input id="search-q" type="search" placeholder="Título ou palavras do resumo"><button>Buscar</button></div><p id="search-status" aria-live="polite"></p><div id="search-results"></div></form></section><section><h2>Artigos recentes</h2>{cards}{nav}</section>'
        path = DOCS / "index.html" if page_no == 0 else DOCS / "page" / str(page_no + 1) / "index.html"
        write_text(path, shell("Início", "Artigos de saúde preservados do backup do site Saúde Teu.", content, SITE_URL + ("/" if page_no == 0 else f"/page/{page_no+1}/"), "Saúde Teu — artigos" if page_no == 0 else f"Artigos — página {page_no+1} | Saúde Teu"))

    # Category archive and page directory.
    cat_list = []
    for (cat_id, cat_slug, cat_name), rows in sorted(categories.items(), key=lambda entry: entry[0][2].casefold()):
        route = f"{BASE_PATH}/categories/{safe_slug(cat_slug,'category')}--{cat_id}/"
        cat_list.append((cat_name, route, len(rows)))
        rows.sort(key=lambda r: (r.get("date", ""), r["ID"]), reverse=True)
        count = (len(rows) + PER_PAGE - 1) // PER_PAGE
        for n in range(count):
            content = f'<p class="eyebrow">Categoria</p><h1>{esc(cat_name)}</h1><p>{len(rows)} artigos</p>' + "".join(card(r) for r in rows[n*PER_PAGE:(n+1)*PER_PAGE]) + pagination(n+1, count, route)
            suffix = "" if n == 0 else f"page/{n+1}/"
            write_text(DOCS / Path(route.removeprefix(BASE_PATH + "/")) / suffix / "index.html", shell(cat_name, f"Artigos da categoria {cat_name}", content, SITE_URL + route + (suffix or "")))
    cat_html = "".join(f'<li><a href="{route}">{esc(name)}</a> <span>({count})</span></li>' for name, route, count in cat_list)
    write_text(DOCS / "categories" / "index.html", shell("Categorias", "Categorias dos artigos Saúde Teu.", f'<h1>Categorias</h1><ul class="category-list">{cat_html}</ul>', SITE_URL + "/categories/"))
    page_links = "".join(f'<li><a href="{r["url"]}">{esc(r["title"] or "(sem título)")}</a></li>' for r in pages)
    write_text(DOCS / "pages" / "index.html", shell("Páginas", "Páginas publicadas recuperadas do backup.", f'<h1>Páginas</h1><ul class="category-list">{page_links}</ul>', SITE_URL + "/pages/"))
    generate_home_feed(DOCS)

    # Split the sitemap below the 50,000-URL protocol limit.
    urls = [SITE_ORIGIN + rec["url"] for rec in records]
    urls += [SITE_URL + "/", SITE_URL + "/categories/", SITE_URL + "/pages/"]
    chunk_size = 20000
    sitemap_names = []
    for idx in range(0, len(urls), chunk_size):
        name = f"sitemap-{idx // chunk_size + 1}.xml"
        sitemap_names.append(name)
        lines = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        lines.extend(f"<url><loc>{html.escape(url)}</loc></url>" for url in urls[idx:idx+chunk_size])
        lines.append("</urlset>")
        write_text(DOCS / name, "\n".join(lines))
    index = ['<?xml version="1.0" encoding="UTF-8"?>', '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    index.extend(f"<sitemap><loc>{SITE_URL}/{name}</loc></sitemap>" for name in sitemap_names)
    index.append("</sitemapindex>")
    write_text(DOCS / "sitemap.xml", "\n".join(index))
    write_text(DOCS / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    summary = {"source_commit": os.environ.get("GITHUB_SHA", "local export commit e94d72f9dc239416115b5c8d01cece7a6fbc1d6d"),
               "published_posts": len(post_rows), "published_pages": len(pages), "post_pages": len(records),
               "categories": len(categories), "search_records": len(search_index), "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "source_validation": manifest["validation"]["state"], "media_files_copied": sum(1 for _ in (DOCS / "media" / "uploads").rglob("*") if _.is_file())}
    write_text(DOCS / "site-manifest.json", json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False))


def card(rec):
    cats = " ".join(f'<a class="chip" href="{BASE_PATH}/categories/{safe_slug(c["slug"],"category")}--{c["id"]}/">{esc(c["name"])}</a>' for c in rec["categories"])
    excerpt = esc(rec["excerpt"] or "")
    return f'<article class="card"><p class="eyebrow">{esc(rec["date"][:10])}</p><h3><a href="{rec["url"]}">{esc(rec["title"] or "(sem título)")}</a></h3><p class="byline">Por Dr. Amber Pelloe, MD</p><p>{excerpt}</p><div class="chips">{cats}</div></article>'


def pagination(current, total, route):
    prefix = route if route else BASE_PATH
    if route:
        here = "" if current == 1 else f"page/{current}/"
    else:
        here = "" if current == 1 else f"page/{current}/"
    prev_link = ""
    next_link = ""
    if current > 1:
        prev = "" if current == 2 else f"page/{current-1}/"
        prev_link = f'<a rel="prev" href="{prefix}/{prev}">← Anterior</a>'
    if current < total:
        next_link = f'<a rel="next" href="{prefix}/page/{current+1}/">Próxima →</a>'
    return f'<nav class="pagination">{prev_link}<span>Página {current} de {total}</span>{next_link}</nav>'



if __name__ == "__main__":
    build()
