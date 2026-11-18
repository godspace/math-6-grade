#!/usr/bin/env python3
"""Карта утилит по страницам: где объявлена функция, сколько вариантов тела, совпадает ли с модулем.

Зачем: шаги 2a/2b/2c плана (`PROJECT_OPTIMIZATION_PLAN.md`, §14.2 п.1) требуют
решить по каждой утилите, можно ли перенести её в `assets/trainers-utils.js`.
`tools/dup_scan.py` даёт число файлов и символы, но не даёт номеров строк и не
показывает, сколько у функции разных реализаций. Этот инструмент закрывает
именно этот пробел: разбирает `function name(...) {...}` и `const name = ... =>`
во всех HTML, группирует по нормализованному телу и сверяет с модулем.

Примеры:
    python -X utf8 tools/utils_scan.py
    python -X utf8 tools/utils_scan.py --pages "trainers/fractions/*.html"
    python -X utf8 tools/utils_scan.py --names gcd lcm primeFactors
    python -X utf8 tools/utils_scan.py --names gcd --json

Коды возврата: 0 - разбор выполнен, 2 - не найдено ни одной страницы.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

# Консоль Windows (cp866/cp1251) не умеет ↶/↷/→ — не падаем, а подменяем на ASCII.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "assets" / "trainers-utils.js"

FUNC_RE = re.compile(r"(?m)^[ \t]*function\s+(\w+)\s*\(([^)]*)\)\s*\{")
CONST_RE = re.compile(r"(?m)^[ \t]*(?:const|let|var)\s+(\w+)\s*=\s*")


def match_braces(text: str, brace_at: int) -> int:
    """Позиция закрывающей скобки блока, с учётом строк, шаблонов и комментариев."""
    i = brace_at
    depth = 0
    quote = None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
        elif ch in "'\"`":
            quote = ch
        elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            nxt = text.find("\n", i)
            if nxt < 0:
                break
            i = nxt
            continue
        elif ch == "/" and i + 1 < len(text) and text[i + 1] == "*":
            i = text.find("*/", i) + 2
            continue
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return len(text) - 1


def declarations(text: str) -> list[dict]:
    """Все объявления функций в тексте: имя, строка, длина, нормализованное тело."""
    found: list[dict] = []
    ranges: list[tuple[int, int]] = []
    for match in FUNC_RE.finditer(text):
        close = match_braces(text, match.end() - 1)
        chunk = text[match.start():close + 1]
        found.append({
            "name": match.group(1),
            "line": text.count("\n", 0, match.start()) + 1,
            "lines": chunk.count("\n") + 1,
            "chars": len(chunk),
            "body": re.sub(r"\s+", " ", chunk).strip(),
            "kind": "function",
        })
        ranges.append((match.start(), close))
    for match in CONST_RE.finditer(text):
        if any(start <= match.start() <= end for start, end in ranges):
            continue
        end = text.find("\n", match.start())
        line = text[match.start():end if end > 0 else len(text)]
        if "=>" not in line or re.search(r"\bnew\b", line):
            continue
        found.append({
            "name": match.group(1),
            "line": text.count("\n", 0, match.start()) + 1,
            "lines": 1,
            "chars": len(line.rstrip()),
            "body": re.sub(r"\s+", " ", line).strip(),
            "kind": "const",
        })
    return sorted(found, key=lambda item: item["line"])


def collect(patterns: list[str]) -> list[Path]:
    """Разворачивает маски в список HTML-страниц (без дублей)."""
    pages: list[Path] = []
    for pattern in patterns:
        hits = [Path(p) for p in glob.glob(str(ROOT / pattern), recursive=True)]
        pages += [p for p in hits if p.suffix.lower() == ".html" and p.is_file()]
    return sorted({p.resolve() for p in pages})


def scan(pages: list[Path], names: list[str] | None) -> list[dict]:
    """Группирует объявления по имени функции и по варианту тела."""
    decls: list[dict] = []
    for page in pages:
        rel = page.relative_to(ROOT).as_posix()
        text = page.read_text(encoding="utf-8", errors="replace")
        for item in declarations(text):
            if names and item["name"] not in names:
                continue
            decls.append({**item, "file": rel})

    canon: dict[str, str] = {}
    if MODULE.is_file():
        for item in declarations(MODULE.read_text(encoding="utf-8")):
            canon[item["name"]] = item["body"]

    groups: list[dict] = []
    for name in sorted({item["name"] for item in decls}):
        items = [item for item in decls if item["name"] == name]
        variants: dict[str, list[dict]] = {}
        for item in items:
            variants.setdefault(item["body"], []).append(item)
        groups.append({
            "name": name,
            "files": len({item["file"] for item in items}),
            "declarations": len(items),
            "in_module": name in canon,
            "module_equal": canon.get(name) is not None
            and len(variants) == 1
            and next(iter(variants)) == canon[name],
            "variants": [
                {
                    "count": len(places),
                    "chars": places[0]["chars"],
                    "module_equal": canon.get(name) == body,
                    "places": [f'{p["file"]}:{p["line"]}' for p in places],
                    "body": places[0]["body"][:200],
                }
                for body, places in sorted(variants.items(), key=lambda kv: -len(kv[1]))
            ],
        })
    return groups


def main() -> int:
    parser = argparse.ArgumentParser(description="Карта объявлений утилит по страницам и сверка с модулем.")
    parser.add_argument("--pages", nargs="+", default=["trainers/**/*.html"],
                        help="маски HTML (по умолчанию trainers/**/*.html)")
    parser.add_argument("--names", nargs="+", default=None, help="только эти имена функций")
    parser.add_argument("--json", action="store_true", help="вывод в JSON")
    args = parser.parse_args()

    pages = collect(args.pages)
    if not pages:
        print("[FAIL] не найдено ни одной страницы")
        return 2

    groups = scan(pages, args.names)
    if args.json:
        print(json.dumps({"pages": len(pages), "utilities": groups}, ensure_ascii=False, indent=2))
        return 0

    print(f"страниц: {len(pages)}, модуль: {'есть' if MODULE.is_file() else 'нет'}")
    for group in groups:
        mark = ""
        if group["in_module"]:
            mark = " == модуль" if group["module_equal"] else " (в модуле, тела другие)"
        print(f"\n{group['name']}: объявлений {group['declarations']} в {group['files']} файлах, "
              f"вариантов {len(group['variants'])}{mark}")
        for index, variant in enumerate(group["variants"], 1):
            same = " == модуль" if variant["module_equal"] else ""
            places = ", ".join(variant["places"])
            print(f"  в{index} x{variant['count']}{same} [{variant['chars']} симв.] {places}")
            print(f"      {variant['body'][:120]}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
