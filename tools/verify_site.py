#!/usr/bin/env python3
"""Verify that each published WordPress post/page is rendered without body loss."""

import html
import json
from pathlib import Path

import build_site as builder


def main():
    manifest = json.loads((builder.EXPORT / "manifest.json").read_text(encoding="utf-8"))
    expected_count = sum(row["count"] for row in manifest.get("type_status_counts", [])
                         if row.get("type") in ("post", "page") and row.get("status") == "publish")

    def published_rows():
        for source in sorted(builder.EXPORT.glob("posts*.jsonl"), key=lambda p: p.name):
            for item in builder.read_jsonl(source):
                if item.get("post_status") == "publish" and item.get("post_type") == "post":
                    yield item
        page_source = builder.EXPORT / "pages.jsonl"
        if page_source.exists():
            for item in builder.read_jsonl(page_source):
                if item.get("post_status") == "publish" and item.get("post_type") == "page":
                    yield item

    by_id, by_url = builder.media_maps()
    mismatches = []
    seen_ids = set()
    empty_titles = 0
    empty_bodies = 0
    for item in published_rows():
        ident = int(item["ID"])
        if ident in seen_ids:
            mismatches.append({"ID": ident, "issue": "duplicate published ID"})
            continue
        seen_ids.add(ident)
        if not item.get("post_title"):
            empty_titles += 1
        if not item.get("post_content"):
            empty_bodies += 1
        route = builder.article_url(item) if item.get("post_type") == "post" else f"{builder.BASE_PATH}/pages/{builder.safe_slug(item.get('post_name',''),'page')}--{ident}/"
        path = builder.DOCS / Path(route.removeprefix(builder.BASE_PATH + "/")) / "index.html"
        try:
            doc = path.read_text(encoding="utf-8")
        except OSError:
            mismatches.append({"ID": ident, "issue": "missing rendered page"})
            continue
        title = html.escape(item.get("post_title") or "", quote=True)
        if f"<h1>{title}</h1>" not in doc:
            mismatches.append({"ID": ident, "issue": "title mismatch"})
            continue
        start = "<div class=\"article-body\">"
        end = "</div></article>"
        if start not in doc or end not in doc:
            mismatches.append({"ID": ident, "issue": "article body wrapper missing"})
            continue
        rendered_body = doc.split(start, 1)[1].rsplit(end, 1)[0]
        expected_body = builder.rewrite_media(item.get("post_content") or "", by_url)
        # Text-mode HTML reads normalize CRLF to LF; newline style has no browser
        # rendering semantics, so compare after the same normalization.
        expected_body = expected_body.replace("\r\n", "\n").replace("\r", "\n")
        if rendered_body != expected_body:
            mismatches.append({"ID": ident, "issue": "body content mismatch"})

    search = json.loads((builder.DOCS / "search-index.json").read_text(encoding="utf-8"))
    sitemap_urls = sum(p.read_text(encoding="utf-8").count("<url>") for p in builder.DOCS.glob("sitemap-*.xml"))
    media_count = sum(1 for p in (builder.DOCS / "media" / "uploads").rglob("*") if p.is_file())
    total_bytes = sum(p.stat().st_size for p in builder.DOCS.rglob("*") if p.is_file())
    result = {
        "state": "passed" if not mismatches and len(seen_ids) == expected_count and len(search) == expected_count else "failed",
        "expected_published_posts_and_pages": expected_count,
        "unique_rendered_ids": len(seen_ids),
        "search_records": len(search),
        "sitemap_urls": sitemap_urls,
        "copied_media_files": media_count,
        "published_site_bytes": total_bytes,
        "within_github_pages_1gb_limit": total_bytes <= 1_000_000_000,
        "empty_titles_preserved": empty_titles,
        "empty_bodies_preserved": empty_bodies,
        "mismatches": mismatches[:100],
        "mismatch_count": len(mismatches),
    }
    (builder.DOCS / "site-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Static site validation", "", f"- State: **{result['state']}**",
             f"- Published posts/pages verified: {len(seen_ids)} / {expected_count}",
             f"- Search records: {len(search)}; sitemap URLs: {sitemap_urls}",
             f"- Copied media files: {media_count}",
             f"- Published output size: {total_bytes:,} bytes; under 1 GB: {result['within_github_pages_1gb_limit']}",
             f"- Empty titles/bodies preserved and flagged by source export: {empty_titles} / {empty_bodies}",
             f"- Record mismatches: {len(mismatches)}"]
    if mismatches:
        lines.extend(["", "## First mismatches", ""] + [f"- ID {x['ID']}: {x['issue']}" for x in mismatches[:100]])
    (builder.DOCS / "site-validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    if result["state"] != "passed" or not result["within_github_pages_1gb_limit"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
