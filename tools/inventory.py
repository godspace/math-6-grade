#!/usr/bin/env python3
"""Инвентаризация всего проекта: строки, символы, inline-CSS/JS, on*-атрибуты.

База для этапа 6 (`PROJECT_OPTIMIZATION_PLAN.md`): цифры до/после каждого шага
оптимизации должны быть воспроизводимыми.

Запуск:
    python tools/inventory.py              # сводка + топ-10 HTML
    python tools/inventory.py --top 20     # длиннее списки
    python tools/inventory.py --json       # машинный вывод (сохранить для «до/после»)

Единицы: текстовые файлы — символы (`len(text)`, как в `tools/size.py`),
картинки — байты. Всегда возвращает 0: это измеритель, а не тест.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
TEXT_EXT = {".html", ".css", ".js"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".svg"}

STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S)
SCRIPT_RE = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.S)
HANDLER_RE = re.compile(
    r"\son(?:click|input|change|load|keydown|pointerdown|mousedown|touchstart)\s*="
)


def walk() -> tuple[list[dict], list[dict]]:
    """(текстовые файлы с метриками, картинки с байтами)."""
    texts: list[dict] = []
    images: list[dict] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(ROOT).as_posix()
        ext = path.suffix.lower()
        if ext in IMAGE_EXT:
            images.append({"path": rel, "bytes": path.stat().st_size})
        elif ext in TEXT_EXT:
            text = path.read_text(encoding="utf-8", errors="replace")
            texts.append(
                {
                    "path": rel,
                    "ext": ext,
                    "lines": len(text.splitlines()),
                    "chars": len(text),
                    "inline_css": sum(len(m) for m in STYLE_RE.findall(text)),
                    "inline_js": sum(len(m) for m in SCRIPT_RE.findall(text)),
                    "handlers": len(HANDLER_RE.findall(text)),
                }
            )
    texts.sort(key=lambda r: r["path"])
    images.sort(key=lambda r: r["path"])
    return texts, images


def fmt(number: int) -> str:
    return f"{number:,}".replace(",", " ")


def totals(rows: list[dict]) -> dict:
    return {
        "files": len(rows),
        "lines": sum(r.get("lines", 0) for r in rows),
        "chars": sum(r.get("chars", 0) for r in rows),
        "inline_css": sum(r.get("inline_css", 0) for r in rows),
        "inline_js": sum(r.get("inline_js", 0) for r in rows),
        "handlers": sum(r.get("handlers", 0) for r in rows),
    }


def print_table(title: str, rows: list[dict], top: int) -> None:
    print(title)
    head = f"  {'файл':<50}{'стр':>6}{'симв':>9}"
    if any(r["ext"] == ".html" for r in rows):
        head += f"{'css-in':>8}{'js-in':>8}{'on*':>5}"
    print(head)
    for row in sorted(rows, key=lambda r: -r["chars"])[:top]:
        line = f"  {row['path']:<50}{row['lines']:>6}{row['chars']:>9}"
        if row["ext"] == ".html":
            line += f"{row['inline_css']:>8}{row['inline_js']:>8}{row['handlers']:>5}"
        print(line)
    print()


def report(texts: list[dict], images: list[dict], top: int) -> None:
    html = [r for r in texts if r["ext"] == ".html"]
    js = [r for r in texts if r["ext"] == ".js"]
    css = [r for r in texts if r["ext"] == ".css"]

    print(f"корень: {ROOT}\n")
    for name, rows in (("HTML", html), ("JS", js), ("CSS", css)):
        t = totals(rows)
        line = (f"{name}: {t['files']} файлов, {fmt(t['chars'])} симв., "
                f"{fmt(t['lines'])} стр.")
        if rows and rows[0]["ext"] == ".html":
            with_css = sum(1 for r in rows if r["inline_css"])
            with_js = sum(1 for r in rows if r["inline_js"])
            with_on = sum(1 for r in rows if r["handlers"])
            line += (f"\n  inline-CSS {fmt(t['inline_css'])} ({with_css} файлов), "
                     f"inline-JS {fmt(t['inline_js'])} ({with_js}), "
                     f"on*-атрибутов {t['handlers']} ({with_on})")
        print(line)
    if images:
        print(f"Картинки: {len(images)} файлов, {fmt(sum(i['bytes'] for i in images))} байт")
    print()

    print_table("=== HTML (топ по символам) ===", html, top)
    print_table("=== JS ===", js, top)
    print_table("=== CSS ===", css, top)

    if images:
        print("=== Картинки (байты) ===")
        for image in sorted(images, key=lambda i: -i["bytes"])[:top]:
            print(f"  {image['path']:<50}{image['bytes']:>9}")
        size = {}
        for image in images:
            size.setdefault(image["bytes"], []).append(image["path"])
        dupes = {b: names for b, names in size.items() if len(names) > 1}
        if dupes:
            print("\n  дубли по размеру (проверить побайтно):")
            for byte_size, names in sorted(dupes.items(), reverse=True):
                print(f"    {fmt(byte_size):>9} байт ×{len(names)}: {', '.join(names)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Инвентаризация файлов проекта.")
    parser.add_argument("--top", type=int, default=10, help="длина списков (по умолчанию 10)")
    parser.add_argument("--json", action="store_true", help="машинный вывод для сравнения до/после")
    args = parser.parse_args()

    texts, images = walk()
    if args.json:
        payload = {
            "root": ROOT.as_posix(),
            "totals": {ext: totals([r for r in texts if r["ext"] == ext])
                       for ext in (".html", ".js", ".css")},
            "images_total_bytes": sum(i["bytes"] for i in images),
            "files": texts,
            "images": images,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    report(texts, images, max(1, args.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())

