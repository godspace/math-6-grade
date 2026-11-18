#!/usr/bin/env python3
"""SEO-аудит страниц math-6-grade (только stdlib, без сети).

По каждой HTML-странице проверяет:
  * title (длина, дубликаты) и meta description (длина, дубликаты);
  * canonical (есть ли, совпадает ли с фактическим URL), meta robots/noindex;
  * ровно один H1 и его текст;
  * JSON-LD (типы), Open Graph (набор og:*);
  * объём видимого текста (слов) — прокси «тонкого контента»;
  * исходящие внутренние/внешние ссылки и входящие ссылки от других страниц;
  * наличие страницы в sitemap.xml и наличие robots.txt.

Примеры:
    python -X utf8 tools/seo_audit.py                    # сводка в консоль
    python -X utf8 tools/seo_audit.py --md seo_report.md # + подробный отчёт
    python -X utf8 tools/seo_audit.py --page trainers/geometry/area.html
    (в режиме --page входящие ссылки считаются только внутри выбранной страницы → 0)

Коды возврата: 0 - критичных замечаний (ERR) нет, 1 - есть ERR, 2 - нет HTML-файлов.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

# Консоль Windows (cp866/cp1251) не умеет часть символов — не падаем, подменяем.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://godspace.github.io/math-6-grade/"

SKIP_DIRS = {"tests", "tools", "assets", "node_modules", ".git", ".vscode"}
# Не страницы: фрагмент head-разметки и файлы подтверждения прав владельца.
SKIP_FILES = {"head-snippet.html"}
SKIP_RE = re.compile(r"^(google[0-9a-f]+\.html|yandex_[0-9a-f]+\.html)$", re.IGNORECASE)
# Служебные страницы: обязателен только title, остальное — WARN, а не ERR.
SERVICE = {"privacy.html"}

# Пороги (символы/слова). Ниже — только эвристика «как у нормальных страниц».
TITLE_MIN, TITLE_MAX = 30, 70
DESC_MIN, DESC_MAX = 70, 200
WORDS_MIN = 120
H1_MIN_LEN = 15

WORD_RE = re.compile(r"[0-9A-Za-zА-Яа-яЁё]{2,}")


class PageParser(HTMLParser):
    """Собирает SEO-факты страницы: head-теги, H1, JSON-LD, текст, ссылки."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.title: str = ""
        self.metas: list[tuple[str, str]] = []
        self.canonical: str | None = None
        self.h1_texts: list[str] = []
        self.ld_types: list[str] = []
        self.imgs = 0
        self.imgs_no_alt = 0
        self.hrefs: list[str] = []
        self._in_title = False
        self._h1_depth = 0
        self._h1_buf: list[str] = []
        self._ld_buf: list[str] = []
        self._in_ld = False
        self._skip = 0
        self._in_body = False
        self._text: list[str] = []

    # --- разбор ---------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html":
            self.lang = a.get("lang")
        elif tag == "body":
            self._in_body = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").strip().lower()
            if key:
                self.metas.append((key, a.get("content", "")))
        elif tag == "link":
            if "canonical" in a.get("rel", "").lower():
                self.canonical = (a.get("href") or "").strip()
        elif tag == "h1":
            self._h1_depth += 1
            if self._h1_depth == 1:
                self._h1_buf = []
        elif tag == "script":
            if "ld+json" in a.get("type", "").lower():
                self._in_ld = True
                self._ld_buf = []
            else:
                self._skip += 1
        elif tag in ("style", "noscript", "template"):
            self._skip += 1
        elif tag == "img":
            self.imgs += 1
            if "alt" not in a:
                self.imgs_no_alt += 1
        elif tag == "a":
            href = (a.get("href") or "").strip()
            if href:
                self.hrefs.append(href)

        if self._in_body and self._skip == 0 and tag in (
            "p", "div", "br", "li", "tr", "td", "th", "h2", "h3", "h4", "span", "button", "label",
        ):
            self._text.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1" and self._h1_depth:
            self._h1_depth -= 1
            if self._h1_depth == 0:
                self.h1_texts.append(_norm(" ".join(self._h1_buf)))
        elif tag == "script":
            if self._in_ld:
                self._in_ld = False
                self.ld_types += _ld_types("".join(self._ld_buf))
            else:
                self._skip = max(0, self._skip - 1)
        elif tag in ("style", "noscript", "template"):
            self._skip = max(0, self._skip - 1)
        elif tag == "body":
            self._in_body = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._in_ld:
            self._ld_buf.append(data)
        elif self._h1_depth == 1:
            self._h1_buf.append(data)
            if self._in_body and self._skip == 0:
                self._text.append(data)
        elif self._in_body and self._skip == 0:
            self._text.append(data)

    # --- результат ------------------------------------------------------
    @property
    def words(self) -> int:
        return len(WORD_RE.findall(" ".join(self._text)))

    def meta(self, key: str) -> str | None:
        for k, v in self.metas:
            if k == key:
                return v
        return None


def _norm(text: str) -> str:
    """Схлопывает пробелы/переводы строк в один пробел."""
    return re.sub(r"\s+", " ", text).strip()


def _ld_types(raw: str) -> list[str]:
    """Достаёт значения @type из JSON-LD (в т.ч. вложенных и списками)."""
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return ["<битый JSON-LD>"]
    found: list[str] = []

    def walk(node) -> None:
        if isinstance(node, dict):
            t = node.get("@type")
            if isinstance(t, str):
                found.append(t)
            elif isinstance(t, list):
                found.extend(str(x) for x in t)
            for key, value in node.items():
                if key != "@type":
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return found


def url_of(rel_path: str) -> str:
    """Фактический URL страницы по пути в репозитории."""
    if rel_path == "index.html":
        return SITE
    return SITE + rel_path.replace("\\", "/")


def collect_pages() -> list[str]:
    """Все HTML-страницы проекта, кроме фикстур/инструментов/служебных файлов."""
    pages: list[str] = []
    for path in ROOT.rglob("*.html"):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        name = rel.name.lower()
        if name in SKIP_FILES or SKIP_RE.match(name):
            continue
        pages.append(rel.as_posix())
    return sorted(pages)


def resolve_link(page: str, href: str) -> str | None:
    """Внутренняя ссылка -> путь в репозитории; внешняя -> None."""
    href = href.strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None
    if href.startswith(SITE):
        href = href[len(SITE):] or "index.html"
    elif href.startswith("/math-6-grade/"):
        # Абсолютные ссылки вида /math-6-grade/trainers/... (GitHub Pages base path).
        href = href[len("/math-6-grade/"):] or "index.html"
    elif href == "/math-6-grade":
        href = "index.html"
    elif href.startswith("http://") or href.startswith("https://") or href.startswith("//"):
        return None
    href = urlsplit(href).path.lstrip("/")
    if not href:
        return None
    base = posixpath.dirname(page)
    target = posixpath.normpath(posixpath.join(base, href))
    if target.startswith(".."):
        return None
    if target.endswith("/"):
        target += "index.html"
    return target


def sitemap_entries() -> list[str]:
    """Пути страниц, перечисленных в sitemap.xml (абсолютные URL -> путь)."""
    path = ROOT / "sitemap.xml"
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8", errors="replace")
    out: list[str] = []
    for loc in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", raw):
        if loc.startswith(SITE):
            out.append(loc[len(SITE):] or "index.html")
        else:
            out.append(loc)  # чужой origin — попадёт в «лишние», это и нужно
    return out


def audit(page: str, inbound: int) -> dict:
    """Проверка одной страницы -> {field: value, issues: [(level, code, text)]}."""
    parser = PageParser()
    raw = (ROOT / page).read_text(encoding="utf-8", errors="replace")
    try:
        parser.feed(raw)
        parser.close()
    except Exception as exc:  # noqa: BLE001 - битая разметка не должна ронять аудит
        print(f"! {page}: разбор упал ({exc.__class__.__name__}: {exc})", file=sys.stderr)

    issues: list[tuple[str, str, str]] = []
    service = page in SERVICE

    def err(code: str, text: str) -> None:
        issues.append(("WARN" if service else "ERR", code, text))

    title = _norm(parser.title)
    desc = _norm(parser.meta("description") or "")
    robots = (parser.meta("robots") or "").lower()
    og_title = parser.meta("og:title") or ""
    og_desc = parser.meta("og:description") or ""
    og_image = parser.meta("og:image") or ""
    og_url = parser.meta("og:url") or ""
    h1 = parser.h1_texts[0] if parser.h1_texts else ""

    if not title:
        err("title", "нет <title>")
    elif not (TITLE_MIN <= len(title) <= TITLE_MAX):
        issues.append(("WARN", "title-len", f"title {len(title)} симв. (норма {TITLE_MIN}-{TITLE_MAX})"))
    if not desc:
        err("desc", "нет meta description")
    elif not (DESC_MIN <= len(desc) <= DESC_MAX):
        issues.append(("WARN", "desc-len", f"description {len(desc)} симв. (норма {DESC_MIN}-{DESC_MAX})"))

    expected = url_of(page)
    if not parser.canonical:
        err("canon", "нет rel=canonical")
    elif parser.canonical.rstrip("/") != expected.rstrip("/"):
        err("canon-mismatch", f"canonical {parser.canonical} != {expected}")
    if "noindex" in robots:
        err("noindex", "meta robots содержит noindex")

    if not parser.h1_texts:
        err("h1", "нет H1")
    else:
        if len(parser.h1_texts) > 1:
            issues.append(("WARN", "h1-multi", f"H1 x{len(parser.h1_texts)}"))
        if len(h1) < H1_MIN_LEN:
            issues.append(("WARN", "h1-short", f"H1 короткий: «{h1}»"))

    if not parser.ld_types:
        issues.append(("WARN", "ld", "нет JSON-LD"))
    if not og_title or not og_desc:
        issues.append(("WARN", "og", "Open Graph неполный (og:title/og:description)"))
    if not og_image:
        issues.append(("WARN", "og-image", "нет og:image (нет превью в мессенджерах)"))
    if og_url and parser.canonical and og_url.rstrip("/") != parser.canonical.rstrip("/"):
        issues.append(("WARN", "og-url", "og:url != canonical"))

    if parser.words < WORDS_MIN:
        issues.append(("WARN", "thin", f"мало текста: {parser.words} слов (<{WORDS_MIN})"))
    if inbound == 0:
        issues.append(("WARN", "orphan", "0 входящих ссылок с других страниц"))
    if parser.lang != "ru":
        issues.append(("WARN", "lang", f"<html lang={parser.lang!r}>"))
    if parser.imgs_no_alt:
        issues.append(("WARN", "img-alt", f"img без alt: {parser.imgs_no_alt}"))
    if parser.meta("keywords"):
        issues.append(("INFO", "keywords", "meta keywords (устарел, не вредит)"))

    og = [n for n, v in (("title", og_title), ("description", og_desc), ("image", og_image), ("url", og_url)) if v]
    return {
        "page": page,
        "title": title,
        "title_len": len(title),
        "desc": desc,
        "desc_len": len(desc),
        "h1": h1,
        "h1_count": len(parser.h1_texts),
        "canonical": parser.canonical,
        "ld": parser.ld_types,
        "og": og,
        "words": parser.words,
        "imgs": parser.imgs,
        "inbound": inbound,
        "out": len(parser.hrefs),
        "issues": issues,
    }


def build_inbound(pages: list[str]) -> dict[str, int]:
    """Считает входящие внутренние ссылки между страницами сайта."""
    known = set(pages)
    inbound = {p: 0 for p in pages}
    for page in pages:
        raw = (ROOT / page).read_text(encoding="utf-8", errors="replace")
        parser = PageParser()
        try:
            parser.feed(raw)
            parser.close()
        except Exception:  # noqa: BLE001 - битая разметка не должна ронять аудит
            continue
        seen: set[str] = set()
        for href in parser.hrefs:
            target = resolve_link(page, href)
            if target in known and target != page:
                seen.add(target)
        for target in seen:
            inbound[target] += 1
    return inbound


def duplicates(rows: list[dict], field: str) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for row in rows:
        value = row[field]
        if value:
            buckets.setdefault(value, []).append(row["page"])
    return {v: ps for v, ps in buckets.items() if len(ps) > 1}


def summary(rows: list[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in rows:
        for level, code, _ in row["issues"]:
            if level != "INFO":
                counts[code] = counts.get(code, 0) + 1
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def print_table(rows: list[dict]) -> None:
    head = f"{'страница':44} {'title':>5} {'desc':>5} {'canon':5} {'H1':>2} {'слов':>5} {'вх':>3}  флаги"
    print(head)
    print("-" * len(head))
    for row in rows:
        flags = ",".join(code for level, code, _ in row["issues"] if level == "ERR")
        warns = len([1 for level, _, _ in row["issues"] if level == "WARN"])
        canon = "ok" if row["canonical"] else "---"
        desc = str(row["desc_len"]) if row["desc_len"] else "---"
        page = row["page"] if len(row["page"]) <= 44 else "..." + row["page"][-41:]
        print(
            f"{page:44} {row['title_len']:>5} {desc:>5} {canon:5} {row['h1_count']:>2} "
            f"{row['words']:>5} {row['inbound']:>3}  ERR:{flags or '-'} WARN:{warns}"
        )


def write_md(rows: list[dict], sm_missing: list[str], sm_extra: list[str], path: Path) -> None:
    errs = sum(1 for r in rows for lvl, _, _ in r["issues"] if lvl == "ERR")
    warns = sum(1 for r in rows for lvl, _, _ in r["issues"] if lvl == "WARN")
    lines = [
        "# SEO-аудит math-6-grade",
        "",
        f"Дата: {date.today().isoformat()} · страниц: {len(rows)} · ERR: {errs} · WARN: {warns}",
        "",
        "Сгенерировано `python -X utf8 tools/seo_audit.py --md <файл>`; руками не править.",
        "",
        "## Сводка по замечаниям",
        "",
        "| код | страниц |",
        "|---|---|",
    ]
    lines += [f"| {code} | {count} |" for code, count in summary(rows)]
    lines += [
        "",
        "## Страницы",
        "",
        "| страница | title | desc | canonical | H1 | слов | вх. | замечания |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        notes = "; ".join(f"{lvl} {code}: {text}" for lvl, code, text in row["issues"] if lvl != "INFO")
        lines.append(
            f"| `{row['page']}` | {row['title_len']} | {row['desc_len']} | "
            f"{'ok' if row['canonical'] else '—'} | {row['h1_count']} | {row['words']} | "
            f"{row['inbound']} | {notes or '—'} |"
        )
    lines += ["", "## sitemap.xml", ""]
    lines.append(f"Нет в sitemap ({len(sm_missing)}): " + (", ".join(f"`{p}`" for p in sm_missing) or "—"))
    lines.append("")
    lines.append(f"Лишние записи ({len(sm_extra)}): " + (", ".join(f"`{p}`" for p in sm_extra) or "—"))
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="SEO-аудит страниц math-6-grade")
    ap.add_argument("--md", metavar="FILE", help="записать подробный отчёт в markdown")
    ap.add_argument("--page", metavar="PATH", help="аудит одной страницы (путь от корня)")
    ap.add_argument("--quiet", action="store_true", help="только сводка, без таблицы")
    args = ap.parse_args()

    all_pages = collect_pages()
    if not all_pages:
        print("Нет HTML-страниц — проверить ROOT", file=sys.stderr)
        return 2
    pages = all_pages
    if args.page:
        page = args.page.replace("\\", "/").lstrip("./")
        if page not in all_pages:
            print(f"Страница не найдена: {page}", file=sys.stderr)
            return 2
        pages = [page]

    inbound = build_inbound(pages)
    rows = [audit(p, inbound.get(p, 0)) for p in pages]

    # Дубликаты title/description ищем по всей выборке страниц.
    for field, code in (("title", "dup-title"), ("desc", "dup-desc")):
        for _, same in duplicates(rows, field).items():
            for row in rows:
                if row["page"] in same:
                    row["issues"].append(("WARN", code, f"тот же {field}: {', '.join(same)}"))

    sm = sitemap_entries()
    sm_rel = {p for p in sm if not p.startswith("http")}
    sm_missing = sorted(set(all_pages) - sm_rel - {"index.html"})
    sm_extra = sorted(p for p in sm if p.startswith("http") or p not in set(all_pages))

    errs = sum(1 for r in rows for lvl, _, _ in r["issues"] if lvl == "ERR")
    warns = sum(1 for r in rows for lvl, _, _ in r["issues"] if lvl == "WARN")
    print(f"SEO-аудит: страниц {len(rows)}, ERR {errs}, WARN {warns}")
    print(
        f"robots.txt: {'есть' if (ROOT / 'robots.txt').is_file() else 'НЕТ'}; "
        f"sitemap.xml: {len(sm)} записей, страниц без записи {len(sm_missing)}, лишних {len(sm_extra)}"
    )
    if not args.quiet:
        print_table(rows)
    print("\nЗамечания (страниц):")
    for code, count in summary(rows):
        print(f"  {code:14} {count}")
    if sm_missing:
        print("нет в sitemap: " + ", ".join(sm_missing))
    if sm_extra:
        print("лишнее в sitemap: " + ", ".join(sm_extra))

    if args.md:
        write_md(rows, sm_missing, sm_extra, Path(args.md))
        print(f"\nОтчёт: {args.md}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
