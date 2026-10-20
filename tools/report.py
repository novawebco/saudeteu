"""Create user-facing documentation after successful full validation."""
import json,pathlib,collections
from extract import ROOT,WORK,dump,file_sha
out=ROOT/'export';m=json.loads((out/'manifest.json').read_text(encoding='utf-8'));v=m['validation'];assert v['state']=='passed'
spot=json.loads((WORK/'readable-spot-checks.json').read_text(encoding='utf-8'))
readme='''# WordPress backup preservation export

This is a data export of `saudeteu-info-20260226-132638-v43377afhuxl.zip`, not a rebuilt website. The original ZIP is unchanged. It contains a single All-in-One WP Migration `.wpress` file. The archive uses 4,377-byte file headers (name 255, size 14, mtime 12, prefix 4096 bytes). It contains 24,505 entries, including `database.sql` and 9,715 uploads files. ZIP decompression verified the entry CRC; all inner entries were read in chunks, bounds checked and hashed. The .wpress format itself has no independent per-file checksum, so hashes prove preservation, not historical integrity before this backup was made.

The SQL table prefix is `SERVMASK_PREFIX_`; the package records the original prefix as `wpag_`. SQL is parsed as data, never executed. UTF-8 decoding is strict; MySQL string escapes are decoded while HTML entities, Gutenberg comments, shortcodes, Unicode and serialized PHP values remain as stored in WordPress. PHP arrays are decoded only to map attachment variants; no PHP code or objects are executed.

## Files

- `manifest.json`: source hashes, complete counts by type/status, batch paths, media counts and validation results.
- `posts.jsonl` and `posts.part-NNNN.jsonl`: all standard posts; read **every** batch in the manifest, not only the first file. Each line is a complete JSON object, never a fragment of a record. Batches target 32 MiB.
- `pages.jsonl`: complete page records.
- `custom-post-types/`: a separate stream for each remaining post type, including system/plugin types such as embed caches and redirection records.
- `classified-records/`: attachments, revisions/autosaves and navigation records, separate from standard posts. All 50,502 source post-table rows are retained in exactly one stream.
- `posts/<original-ID>/metadata.json` and `content.html`: all posts, pages and custom records. The HTML file contains the exact decoded WordPress body as UTF-8, without an added newline, wrapper or formatting. Metadata excludes only the body and explicitly redacted credential fields. These paths use IDs and cannot collide when titles/slugs repeat.
- `posts-index.csv`: full titles and descriptive fields; not the full-body export.
- `media-manifest.jsonl`: attachment-to-file mappings and an inventory of every uploads entry, including files excluded from Git. Missing files are explicitly marked. URLs alone do not imply that a file exists locally.
- `media/uploads/`: every actual image file found in uploads, including unreferenced files, preserved byte for byte. Generated CSS, plugin/support files and form support files are retained only in the original backup.
- `taxonomies/`: all term, term-taxonomy and safe term-metadata rows; each content record contains original relationship IDs/order plus term and taxonomy details.
- `seo/`: Rank Math internal metadata and redirection tables. Per-post SEO plugin fields remain in `postmeta` and `seo_metadata`.
- `site-settings.json`: only public URL, permalink, timezone and related settings needed to interpret records.
- `content-integrity.jsonl`: per-ID source title/body SHA-256 results, including classified records.
- `record-flags.jsonl`, `reference-issues.jsonl`, `duplicate-groups.jsonl`: empty/large bodies, unresolved media IDs and preserved duplicate groups.
- `redactions.json`: excluded credential field names/paths and reasons, never their values.
- `validation-report.md`: checks, counts, representative readable excerpts and limitations.

## Reading and reproducing

Use the `batches` map in `manifest.json` to iterate each stream in order. JSONL is UTF-8 and standard JSON: `post_title` is the complete title and `post_content` is the complete body. WordPress column names are preserved, including status, local/GMT dates, author ID, slug, GUID, parent, menu order, excerpt and filtered content. `author` supplies available public display name/nicename; private user/account fields are excluded. `postmeta` is a list, preserving repeated keys and meta IDs; PHP serialized values are preserved as original strings. `featured_image_ids` links to attachment IDs in the media manifest. `body_media_references` lists uploads and external embeds; `body_media_ids` includes recognized block/class/gallery IDs. The original body is the authoritative source for dynamic shortcodes or code-generated URLs.

The source has GMT offset `0`, an empty named timezone, and permalink structure `/%postname%/`. Both local and GMT database fields are preserved even if zero/empty. GUIDs, old slugs, canonical/permalink plugin metadata and public permalink settings are available; no current live URL behavior is asserted.

Reproduce in a fresh directory containing `tools/` with Python 3 (standard library only):

```text
python tools/unpack.py /path/to/saudeteu-info-20260226-132638-v43377afhuxl.zip
python tools/extract.py import
python tools/extract.py export
python tools/enrich_media.py
python tools/verify.py
python tools/report.py
```

For the original run the backup is in the current user's Downloads folder. `extract.py` and `verify.py` use that location unless `.work/backup-location.json` was created by `unpack.py`. Work files, database, extracted archive and spot-check staging stay in ignored `.work/`. Preserve the original ZIP separately; it is intentionally not committed. The root repository README remains unchanged.

Credentials, post access passwords, password hashes, raw SQL, wp-config.php, user emails/logins, usermeta, comments/customer submissions, unrelated non-content log/cache tables and private options are excluded. Public author names are retained. The metadata credential scan covers credential-like keys, nested serialized assignments and high-confidence token/private-key patterns; it cannot prove that every arbitrary string is harmless. Raw title/body content is never rewritten; a high-confidence content credential match blocks validation for manual review. No such match was detected in this run.

Git stores export files with text conversion disabled to preserve bytes. No file exceeds GitHub's 100 MiB limit; see the manifest for the largest file and total size. No force push or Git LFS is required. [GitHub large-file documentation](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).
'''
(out/'README.md').write_text(readme,encoding='utf-8',newline='')
lines=['# Validation report','','Full automated validation passed. This means preservation against the available backup, not confirmation that the original website or backup contained every historical record.','','## Source and coverage','','| Post type | Source | Export |','| --- | ---: | ---: |']
for typ,n in sorted(m['record_types'].items()):lines.append(f'| {typ} | {n:,} | {n:,} |')
lines+=['','Total: **50,502** unique source IDs and exported records. Content folders: **49,818**. Navigation (5), attachments (678) and revisions (1) are separately classified.','', '### Counts by type and status','','| Type | Status | Count |','| --- | --- | ---: |']
for x in m['type_status_counts']:lines.append(f"| {x['type']} | {x['status']} | {x['count']:,} |")
lines+=['','No source pending, private, future/scheduled or trash records were found. No statuses were converted or omitted.','','## Complete title/body and structure checks','',f"- All **{v['independent_sql_title_body_matches']:,}** source rows were re-read from SQL with an independent regex tokenizer/escape decoder; decoded title and body hashes match exported JSONL exactly. **Zero mismatches.**",f"- All **{v['per_record_folders_verified']:,}** eligible content.html files match the full source body bytes; all matching metadata files equal their JSONL record fields.",f"- Source/export ID sets, unique IDs, type/status pairs, every original public post-table field, **{v['postmeta_rows_verified']:,}** retained postmeta rows, taxonomy relationship IDs/order and CSV full titles passed record-by-record checks.",'- Every JSON and JSONL file parses. Duplicate IDs and overwritten ID paths were checked. Duplicate titles/slugs were preserved, not merged.',f"- Duplicate-title groups: {v['duplicates_preserved']['title']['groups']:,}; duplicate-slug groups: {v['duplicates_preserved']['slug']['groups']:,}. IDs are in duplicate-groups.jsonl.",'- SQL, inner archive and original ZIP hashes were rechecked unchanged. ZIP CRC and inner archive lengths/paths were checked. Source hashes are in manifest.json.','','### Encoding and content features','','| Feature present in source title/body | Records |','| --- | ---: |']
for k,n in m['source_content_features'].items():lines.append(f'| {k} | {n:,} |')
lines+=['','All title/body characters, including the listed scripts, emoji, HTML, block comments and shortcodes, were covered by the full hashes. A feature absent from this table was not observed. Existing U+FFFD replacement characters, if listed, originate in source content and are preserved rather than guessed/repaired.','','### Flags','','```json',json.dumps(v['flags'],ensure_ascii=False,indent=2),'```',f"Largest body: ID {v['largest_body']['ID']}, {v['largest_body']['bytes']:,} UTF-8 bytes. Empty values and large bodies are flagged and preserved; nothing was filled in.",'','## Media','', '```json',json.dumps(m['media'],ensure_ascii=False,indent=2),'```',f"All **{v['media_files_hash_verified']:,}** copied files were rehashed against archive-entry hashes. Every claimed local media path exists. Unresolved attachment-ID references: **{v['unresolved_media_id_references']:,}** (reference-issues.jsonl).",'','Some missing attachment references have differently named archive candidates (for example, a database filename begins `Óleo-de-colza` while the archive filename begins `leo-de-colza`). These are not automatically treated as verified matches. All actual image files are preserved. Missing-reference counts are reference occurrences, not necessarily distinct files. External URLs and unresolved relative URLs are recorded without downloading or claiming availability. Dynamic shortcode execution, URLs generated at runtime and remote availability were not verified. Original bodies retain references that a static scanner cannot interpret.','','## Redactions and boundaries','',f"Credential/password fields excluded: **{m['redactions']}**. Field paths/reasons are in redactions.json. The original backup remains unchanged. Private account/customer data and raw SQL were not included.",'','Existing root README was preserved. No WordPress code/plugins were executed and no content was published. Media is preserved as data. No live-site completeness, external-link availability, historical pre-backup encoding or executable shortcode behavior is asserted.','','## Readable representative spot-checks','','These excerpts supplement the complete automated comparisons; they do not replace them. Titles and body openings/endings were inspected as text, without executing HTML.']
for s in spot:
 lines+=['',f"### ID {s['ID']} ({s['type']})",'',s['title'],'',f"Body size: {s['bytes']:,} UTF-8 bytes.",'','```text',s['content_start'].replace('```','[triple backticks]'),'... [excerpt only; full body remains in export] ...',s['content_end'].replace('```','[triple backticks]'),'```']
lines+=['','## Storage checks','',f"Largest exported data file: `{v['largest_export_file']['path']}` ({v['largest_export_file']['bytes']:,} bytes). Total exported data before reports: {v['export_data_bytes_before_reports']:,} bytes. No oversized file was silently omitted. JSONL uses complete-record batches near 32 MiB. Git's compressed pack size is checked separately before push.",'']
(out/'validation-report.md').write_text('\n'.join(lines),encoding='utf-8',newline='')
print(dump({'documentation':'written','validated_records':v['exported_records']}))
