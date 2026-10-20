# Saúde Teu

Static site and verified WordPress content export for the `saudeteu` backup.

**Live site:** <https://lamberdar8singh.github.io/saudeteu/>

The site renders all **49,709 published posts** and **16 published pages** found in the backup. It includes article pages, paginated archives, category pages, a search index, sitemap, and the **8,532 media files** available in the backup. Draft and other non-published records remain in the preservation export but are not displayed on the public site.

GitHub Pages publishes the generated files from `docs/`. The complete preservation export is under `export/`; it retains the structured records, metadata, source hashes, and validation report. The static pages preserve each source body, mapping available WordPress upload URLs to the copied local media. Missing media and WordPress-only dynamic features remain documented in the export report.

## Rebuild and verify

Python 3 standard library is sufficient. From the repository root:

```text
python tools/build_site.py
python tools/verify_site.py
```

The builder refuses to publish unless `export/manifest.json` records a passed source validation. The verifier streams the source records and checks every published page title and body, search entry, sitemap count, copied media file count, and the GitHub Pages 1 GB published-site size limit. See `docs/site-validation.md` for the latest result and `export/validation-report.md` for the original extraction validation.

This is a static rendering of the backup. WordPress plugins, PHP shortcodes, comments, forms, and dynamic embeds do not run on GitHub Pages.
