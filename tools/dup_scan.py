#!/usr/bin/env python3
"""Измеритель дублирования HTML-страниц (шаги 6.2-6.3 PROJECT_OPTIMIZATION_PLAN.md).

Считает: экономию от выноса повторяющихся нормализованных строк (>=20 симв.),
самые крупные общие блоки <head>/CSS/JS/body, экономию внутри кластеров страниц,
повторяемые объявления функций, on*-атрибуты и внешние <script src>.

Экономия = сумма (длина строки x (копий - 1)) по строкам, встреченным в >=2 файлах,
то есть оценка снизу: отступы, комментарии и короткие строки не учитываются.

Запуск: python -X utf8 tools/dup_scan.py [--json]
Перед запуском в PowerShell 5.1: [Console]::OutputEncoding=[Text.Encoding]::UTF8
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", "node_modules", "__pycache__", "tools", "tests"}

# Заполняется в main(); используется для режима --json.
PAYLOAD: dict = {}

STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
SCRIPT_SRC_RE = re.compile(r"<script[^>]*\bsrc\s*=\s*[\"']([^\"']+)", re.I)
SCRIPT_INLINE_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S | re.I)
HEAD_RE = re.compile(r"<head[^>]*>(.*?)</head>", re.S | re.I)
HANDLER_RE = re.compile(r"\son(click|input|change|load|keydown|pointerdown|mousedown|touchstart)\s*=", re.I)
FN_RE = re.compile(r"function\s+([A-Za-z_$][\w$]*)\s*\(|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:function|\()")


def norm_lines(text: str, minlen: int = 20) -> list[str]:
    """Нормализованные непустые строки (пробелы схлопнуты), без коротких."""
    out = []
    for raw in text.splitlines():
        s = re.sub(r"\s+", " ", raw.strip())
        if len(s) >= minlen:
            out.append(s)
    return out


def load() -> list[dict]:
    rows = []
    for path in sorted(ROOT.rglob("*.html")):
        if any(part in SKIP for part in path.relative_to(ROOT).parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        head = HEAD_RE.search(text)
        head_text = head.group(1) if head else ""
        head_clean = SCRIPT_INLINE_RE.sub("", STYLE_RE.sub("", head_text))
        body = text.split("</head>", 1)[1] if "</head>" in text else ""
        body = SCRIPT_INLINE_RE.sub("", STYLE_RE.sub("", body))
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "chars": len(text),
                "css_blocks": STYLE_RE.findall(text),
                "js_blocks": SCRIPT_INLINE_RE.findall(text),
                "head": head_text,
                "head_clean": head_clean,
                "body": body,
                "text": text,
                "handlers": [m.group(1).lower() for m in HANDLER_RE.finditer(text)],
                "externals": [u.split("?")[0] for u in SCRIPT_SRC_RE.findall(text)],
            }
        )
    return rows


def block_text(row: dict, key: str) -> str:
    return row[key] if key in ("head", "head_clean", "body") else "".join(row[key])



def duplication(rows: list[dict], key: str) -> dict:
    """Строки, встречающиеся в >=2 разных файлах; экономия = копии сверх одной."""
    files_with_line: dict[str, set[str]] = defaultdict(set)
    per_file_total: dict[str, int] = {}
    per_file_shared: dict[str, int] = defaultdict(int)
    for row in rows:
        text = block_text(row, key)
        lines = norm_lines(text)
        per_file_total[row["path"]] = sum(len(s) for s in lines)
        for s in set(lines):
            files_with_line[s].add(row["path"])
    shared = {s: f for s, f in files_with_line.items() if len(f) >= 2}
    saved = 0
    occ_chars = 0
    for s, files in shared.items():
        occ_chars += len(s) * len(files)
        saved += len(s) * (len(files) - 1)
        for p in files:
            per_file_shared[p] += len(s)
    return {
        "shared_lines": len(shared),
        "shared_chars_occurrences": occ_chars,
        "saved_if_one_copy": saved,
        "per_file_total": per_file_total,
        "per_file_shared": dict(per_file_shared),
    }


def pair_blocks(rows: list[dict], key: str, min_lines: int = 6, min_chars: int = 250) -> list[dict]:
    """Максимальные общие блоки строк между парами файлов (difflib)."""
    import difflib

    data = {}
    for row in rows:
        data[row["path"]] = norm_lines(block_text(row, key))
    out = []
    paths = list(data)
    for i, a in enumerate(paths):
        for b in paths[i + 1:]:
            sm = difflib.SequenceMatcher(None, data[a], data[b], autojunk=False)
            for blk in sm.get_matching_blocks():
                if blk.size >= min_lines:
                    chunk = data[a][blk.a:blk.a + blk.size]
                    size = sum(len(x) for x in chunk)
                    if size >= min_chars:
                        out.append({"files": (a, b), "lines": blk.size, "chars": size,
                                    "sample": chunk[0][:90]})
    out.sort(key=lambda d: -d["chars"])
    return out


def thresholds(rows: list[dict], key: str) -> list[tuple[int, int]]:
    """(порог k, экономия симв.), если строку, встречающуюся в >=k файлах, держать в 1 экземпляре."""
    files_with_line: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for s in set(norm_lines(block_text(row, key))):
            files_with_line[s].add(row["path"])
    out = []
    for k in (2, 5, 10, 20):
        saved = sum(len(s) * (len(f) - 1) for s, f in files_with_line.items() if len(f) >= k)
        out.append((k, saved))
    return out


def fn_body(text: str, name: str) -> str | None:
    """Тело функции по балансу скобок (приближение: без учёта строк/комментариев)."""
    pats = [
        r"function\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{",
        r"(?:const|let|var)\s+" + re.escape(name) + r"\s*=\s*(?:async\s*)?(?:function\s*\([^)]*\)|\([^)]*\)\s*=>)\s*\{",
    ]
    for pat in pats:
        m = re.search(pat, text)
        if not m:
            continue
        start = text.index("{", m.start())
        depth = 0
        for i in range(start, len(text)):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[m.start():i + 1]
    return None


def fn_report(rows: list[dict], name: str) -> dict:
    bodies = {}
    for row in rows:
        js = "\n".join(row["js_blocks"])
        b = fn_body(js, name)
        if b:
            bodies[row["path"]] = b
    sizes = {p: len(re.sub(r"\s+", " ", b)) for p, b in bodies.items()}
    total = sum(sizes.values())
    canon = max(sizes.values()) if sizes else 0
    distinct = len({re.sub(r"\s+", " ", b) for b in bodies.values()})
    return {"files": len(bodies), "total": total, "canon": canon, "saved": total - canon,
            "distinct": distinct, "sizes": sizes}


FN_NAMES = ["gcd", "lcm", "getRandomInt", "pickRandom", "declOfNum", "startConfetti",
            "fireConfetti", "animate", "autoSaveToFirebase", "generateTask", "checkAnswer",
            "checkSolution", "nextTask", "initProblem", "handleTextDrop", "setupDragAndDrop",
            "shuffleArray", "isPrime", "primeFactors", "showVictory", "setFeedback",
            "updateLiveCancellation", "vibrate", "initGame"]


CLUSTERS = {
    "percents (4)": ["trainers/percents/number-by.html", "trainers/percents/percent-of.html",
                     "trainers/percents/ratio.html", "trainers/percents/tiles.html"],
    "fractions (8)": ["trainers/fractions/addition.html", "trainers/fractions/comparison.html",
                      "trainers/fractions/conversion.html", "trainers/fractions/division.html",
                      "trainers/fractions/mixed.html", "trainers/fractions/mixed_complex.html",
                      "trainers/fractions/multiplication.html", "trainers/fractions/math_board.html"],
    "construct (9)": [f"trainers/equations/construct/task{i}.html" for i in range(1, 10)],
    "divisibility (4)": ["trainers/divisibility/gcd.html", "trainers/divisibility/lcm.html",
                         "trainers/divisibility/primes.html", "trainers/divisibility/signs.html"],
    "geometry (4)": ["trainers/geometry/area.html", "trainers/geometry/area-metaphor.html",
                     "trainers/geometry/pi.html", "trainers/geometry/perimeter-area.html"],
    "equations (6)": ["trainers/equations/equations.html", "trainers/equations/equations-test.html",
                      "trainers/equations/opening.html", "trainers/equations/opening-test.html",
                      "trainers/equations/equations_construct.html",
                      "trainers/equations/equations_construct-2.html"],
    "rational (2)": ["trainers/rational/coordinates-pro.html",
                     "trainers/rational/phone-balance.html"],
}


def cluster_savings(rows: list[dict], paths: list[str], key: str) -> int:
    files_with_line: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["path"] in paths:
            for s in set(norm_lines(block_text(row, key))):
                files_with_line[s].add(row["path"])
    return sum(len(s) * (len(f) - 1) for s, f in files_with_line.items() if len(f) >= 2)


SIGNATURES = [
    ("favicon-набор (ico+3 png+apple)", ["favicon.ico", "favicon-16x16.png", "favicon-32x32.png",
                                        "favicon-48x48.png", "apple-touch-icon"]),
    ("site.webmanifest", ["site.webmanifest"]),
    ("analytics.js", ["assets/analytics.js"]),
    ("Open Graph", ["og:title"]),
    ("JSON-LD", ["application/ld+json"]),
    ("canonical", ["rel=\"canonical\""]),
    ("CSS var --primary", ["--primary:"]),
    ("back-link (навигация)", ["back-link"]),
    ("startConfetti", ["startConfetti"]),
    ("Firebase", ["firebase-app.js"]),
    ("MathJax CDN", ["mathjax"]),
    ("polyfill.io CDN", ["polyfill.io"]),
    ("Google Fonts", ["fonts.googleapis.com"]),
    ("Tailwind CDN", ["cdn.tailwindcss.com"]),
]


def main() -> int:
    rows = load()
    print(f"файлов HTML (без tools/tests): {len(rows)}\n")

    dup = {}
    for key, title in (("head_clean", "HEAD (SEO/мета/иконки, без style/script)"),
                       ("css_blocks", "inline-CSS"),
                       ("js_blocks", "inline-JS"),
                       ("body", "BODY-разметка (без style/script)")):
        d = duplication(rows, key)
        dup[key] = d
        total = sum(d["per_file_total"].values())
        print(f"== {title} ==")
        print(f"  строк(>=20 симв.) всего: суммарно {total} симв.")
        print(f"  совпадающих строк: {d['shared_lines']}; вхождений {d['shared_chars_occurrences']} симв.;"
              f" экономия при 1 копии: {d['saved_if_one_copy']} симв.")
        print("  пороги: " + ", ".join(f">={k} файлов: {v} симв." for k, v in thresholds(rows, key)))
        for p, c in sorted(d["per_file_shared"].items(), key=lambda kv: -kv[1])[:6]:
            tot = d["per_file_total"].get(p, 0) or 1
            print(f"    {p:<52}{c:>8} ({100 * c / tot:4.0f}% от своих)")
        print()

    print("== сигнатуры по файлам ==")
    for name, needles in SIGNATURES:
        hits = [r["path"] for r in rows if all(n in r["text"] for n in needles)]
        print(f"  {name:<34} файлов: {len(hits)}")
    print()

    print("== тела общих функций (баланс скобок, пробелы схлопнуты) ==")
    print(f"  {'функция':<24}{'файлов':>7}{'всего':>8}{'канон':>7}{'экономия':>9}{'вариантов':>10}")
    fn_data = {}
    for name in FN_NAMES:
        r = fn_report(rows, name)
        if r["files"] >= 2:
            fn_data[name] = r
            print(f"  {name:<24}{r['files']:>7}{r['total']:>8}{r['canon']:>7}{r['saved']:>9}{r['distinct']:>10}")
    print()

    print("== повторяющиеся on*-обработчики ==")
    onvals: Counter = Counter()
    onfiles: defaultdict[str, set[str]] = defaultdict(set)
    ON_VAL_RE = re.compile(r"\son(?:click|input|change)\s*=\s*[\"']([^\"']+)[\"']", re.I)
    for row in rows:
        for m in ON_VAL_RE.finditer(row["text"]):
            v = re.sub(r"\s+", " ", m.group(1).strip())
            onvals[v] += 1
            onfiles[v].add(row["path"])
    for v, c in onvals.most_common(12):
        print(f"  {c:>3} × в {len(onfiles[v])} файлах: {v[:70]}")
    print()

    print("== пофайловая карта inline-блоков: всего/совпадает с другими ==")
    print(f"  {'файл':<50}{'CSS':>7}{'копия%':>7}{'JS':>8}{'копия%':>7}")
    for row in rows:
        p = row["path"]
        css_t = dup["css_blocks"]["per_file_total"].get(p, 0)
        css_s = dup["css_blocks"]["per_file_shared"].get(p, 0)
        js_t = dup["js_blocks"]["per_file_total"].get(p, 0)
        js_s = dup["js_blocks"]["per_file_shared"].get(p, 0)
        if not css_t and not js_t:
            continue
        cp = f"{100 * css_s / css_t:.0f}" if css_t else "-"
        jp = f"{100 * js_s / js_t:.0f}" if js_t else "-"
        print(f"  {p:<50}{css_t:>7}{cp:>7}{js_t:>8}{jp:>7}")
    print()

    print("== крупнейшие общие блоки inline-JS (>=6 строк, >=250 симв.) ==")
    for blk in pair_blocks(rows, "js_blocks")[:14]:
        print(f"  {blk['lines']:>3} стр {blk['chars']:>6} симв  {blk['files'][0]}  <->  {blk['files'][1]}")
        print(f"      {blk['sample']}")
    print()

    print("== крупнейшие общие блоки inline-CSS ==")
    for blk in pair_blocks(rows, "css_blocks")[:12]:
        print(f"  {blk['lines']:>3} стр {blk['chars']:>6} симв  {blk['files'][0]}  <->  {blk['files'][1]}")
        print(f"      {blk['sample']}")
    print()

    print("== общие блоки head (SEO/мета/иконки) ==")
    for blk in pair_blocks(rows, "head_clean", min_lines=4, min_chars=150)[:12]:
        print(f"  {blk['lines']:>3} стр {blk['chars']:>6} симв  {blk['files'][0]}  <->  {blk['files'][1]}")
        print(f"      {blk['sample']}")
    print()

    print("== общие блоки BODY-разметки ==")
    for blk in pair_blocks(rows, "body", min_lines=5, min_chars=200)[:12]:
        print(f"  {blk['lines']:>3} стр {blk['chars']:>6} симв  {blk['files'][0]}  <->  {blk['files'][1]}")
        print(f"      {blk['sample']}")
    print()

    print("== экономия внутри кластеров страниц (общие строки, 1 копия) ==")
    print(f"  {'кластер':<20}{'JS':>8}{'CSS':>8}{'HEAD':>8}{'BODY':>8}")
    for name, paths in CLUSTERS.items():
        js = cluster_savings(rows, paths, "js_blocks")
        css = cluster_savings(rows, paths, "css_blocks")
        head = cluster_savings(rows, paths, "head_clean")
        body = cluster_savings(rows, paths, "body")
        print(f"  {name:<20}{js:>8}{css:>8}{head:>8}{body:>8}")
    print()

    names: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        js = "\n".join(row["js_blocks"])
        for m in FN_RE.finditer(js):
            names[m.group(1) or m.group(2)].add(row["path"])
    print("== имена функций/утилит в inline-JS (объявлены в >=2 файлах) ==")
    for name, files in sorted(names.items(), key=lambda kv: -len(kv[1])):
        if len(files) >= 2:
            print(f"  {name:<18} файлов: {len(files)}")
    print()

    handler_kinds: Counter = Counter()
    handler_files: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        for h in row["handlers"]:
            handler_kinds[h] += 1
            handler_files[h].add(row["path"])
    print("== on*-атрибуты по типам ==")
    for h, c in handler_kinds.most_common():
        print(f"  on{h:<12} {c:>4} в {len(handler_files[h])} файлах")
    print()

    print("== внешние <script src> ==")
    ext: Counter = Counter()
    for row in rows:
        for u in row["externals"]:
            ext[u] += 1
    for u, c in ext.most_common():
        print(f"  {c:>3} × {u}")
    print()

    payload = {
        "rows": [
            {
                "path": r["path"],
                "chars": r["chars"],
                "css_chars": sum(len(m) for m in r["css_blocks"]),
                "js_chars": sum(len(m) for m in r["js_blocks"]),
                "handlers": len(r["handlers"]),
                "externals": r["externals"],
            }
            for r in rows
        ],
        "js": dup["js_blocks"],
        "css": dup["css_blocks"],
        "head": dup["head_clean"],
        "body": dup["body"],
        "fn": {k: {kk: vv for kk, vv in v.items() if kk != "sizes"} for k, v in fn_data.items()},
    }
    global PAYLOAD
    PAYLOAD = payload
    return 0


if __name__ == "__main__":
    import contextlib
    import io

    if "--json" in sys.argv:
        with contextlib.redirect_stdout(io.StringIO()):
            code = main()
        print(json.dumps(PAYLOAD, ensure_ascii=False, indent=1))
        sys.exit(code)
    sys.exit(main())
