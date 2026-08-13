"""Run lightweight launch checks against the generated Eleventy site."""

from __future__ import annotations

import re
import sys
import json
import html
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.assets: list[tuple[str, str]] = []
        self.errors: list[str] = []
        self.h1_count = 0
        self.has_title = False
        self.has_description = False
        self.has_canonical = False

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, str | None]]) -> None:
        attrs = dict(attrs_list)
        if tag == "h1":
            self.h1_count += 1
        elif tag == "title":
            self.has_title = True
        elif tag == "meta" and attrs.get("name") == "description" and attrs.get("content"):
            self.has_description = True
        elif tag == "link" and attrs.get("rel") == "canonical" and attrs.get("href", "").startswith("https://"):
            self.has_canonical = True

        if "href" in attrs:
            href = attrs.get("href") or ""
            if not href:
                self.errors.append(f"empty href on <{tag}>")
            self.assets.append(("href", href))
        if "src" in attrs:
            self.assets.append(("src", attrs.get("src") or ""))
        if "srcset" in attrs:
            for candidate in (attrs.get("srcset") or "").split(","):
                url = candidate.strip().split(" ", 1)[0]
                if url:
                    self.assets.append(("srcset", url))

        if tag == "img":
            if "alt" not in attrs:
                self.errors.append(f"image missing alt: {attrs.get('src', '')}")
            if "width" not in attrs or "height" not in attrs:
                self.errors.append(f"image missing dimensions: {attrs.get('src', '')}")
            if attrs.get("aria-hidden") == "true" and attrs.get("alt"):
                self.errors.append(f"hidden image has non-empty alt: {attrs.get('src', '')}")


def local_target(url: str) -> Path | None:
    if not url or url.startswith(("#", "data:", "mailto:", "tel:", "javascript:")):
        return None
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    if not path.startswith("/"):
        return None
    target = PUBLIC / path.lstrip("/")
    if path.endswith("/"):
        return target / "index.html"
    if target.suffix:
        return target
    if target.is_dir() or (target / "index.html").exists():
        return target / "index.html"
    return target


def main() -> int:
    if not PUBLIC.exists():
        print("public/ does not exist; run npm run build first")
        return 1

    failures: list[str] = []
    checked_urls: set[str] = set()
    html_files = sorted(PUBLIC.rglob("*.html"))
    for page in html_files:
        page_text = page.read_text(encoding="utf-8")
        parser = PageParser()
        parser.feed(page_text)
        label = page.relative_to(PUBLIC).as_posix()
        is_admin = label == "admin/index.html"
        if not is_admin:
            if parser.h1_count != 1:
                failures.append(f"{label}: expected one h1, found {parser.h1_count}")
            if not parser.has_title:
                failures.append(f"{label}: missing title")
            if not parser.has_description:
                failures.append(f"{label}: missing meta description")
            if not parser.has_canonical:
                failures.append(f"{label}: missing absolute canonical")
        failures.extend(f"{label}: {error}" for error in parser.errors)
        for position, schema in enumerate(
            re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page_text, re.DOTALL),
            start=1,
        ):
            try:
                json.loads(html.unescape(schema))
            except json.JSONDecodeError as error:
                failures.append(f"{label}: invalid JSON-LD block {position}: {error.msg}")
        for _, url in parser.assets:
            target = local_target(url)
            if target and url not in checked_urls:
                checked_urls.add(url)
                if not target.exists():
                    failures.append(f"{label}: missing local target {url}")

    css_url_pattern = re.compile(r"url\([\"']?([^\"')]+)")
    for css in PUBLIC.rglob("*.css"):
        for url in css_url_pattern.findall(css.read_text(encoding="utf-8")):
            target = local_target(url)
            if target and not target.exists():
                failures.append(f"{css.relative_to(PUBLIC).as_posix()}: missing local target {url}")

    for metadata in [PUBLIC / "assets/favicons/site.webmanifest", PUBLIC / "assets/favicons/browserconfig.xml"]:
        if metadata.exists():
            for url in re.findall(r'(?:"src"\s*:\s*"|src=")(/[^"]+)', metadata.read_text(encoding="utf-8")):
                target = local_target(url)
                if target and not target.exists():
                    failures.append(f"{metadata.relative_to(PUBLIC).as_posix()}: missing local target {url}")

    if failures:
        print("Site audit failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print(f"Site audit passed: {len(html_files)} HTML files and {len(checked_urls)} unique internal references checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
