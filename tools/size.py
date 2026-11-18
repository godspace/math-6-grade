#!/usr/bin/env python3
"""Размеры math_board: строки и символы по секциям (метрика этапа оптимизации).

Показывает, сколько занимают разметка, inline-CSS и inline-JS, и сколько
строк лежит в вынесенных файлах assets/math_board.css / assets/math_board.js.

Запуск: python tools/size.py
Всегда возвращает 0: это измеритель, а не тест.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Консоль Windows (cp866/cp1251) не умеет часть символов — не падаем, а подменяем на '?'
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "trainers" / "fractions" / "math_board.html"
EXTERNAL = (
    ROOT / "assets" / "math_board.css",
    ROOT / "assets" / "math_board.js",
)


def find_line(lines: list, needle: str, start: int = 0) -> int:
    """Индекс строки, которая ровно совпадает с needle (-1, если нет)."""
    for index in range(start, len(lines)):
        if lines[index].strip() == needle:
            return index
    return -1


def measure(lines: list) -> list:
    """Возвращает [(название, строк, символов), ...] по секциям страницы."""
    style_start = find_line(lines, "<style>")
    style_end = find_line(lines, "</style>", style_start + 1)
    script_start = find_line(lines, "<script>", style_end + 1)
    script_end = find_line(lines, "</script>", script_start + 1)

    if -1 in (style_start, style_end, script_start, script_end):
        chars = sum(len(line) for line in lines) + max(len(lines) - 1, 0)
        return [("HTML без inline-секций", len(lines), chars)]

    def span(first: int, last: int) -> tuple:
        chunk = lines[first:last + 1]
        return len(chunk), sum(len(line) for line in chunk) + max(len(chunk) - 1, 0)

    css_lines, css_chars = span(style_start, style_end)
    js_lines, js_chars = span(script_start, script_end)

    total_chars = sum(len(line) for line in lines) + max(len(lines) - 1, 0)
    html_lines = len(lines) - css_lines - js_lines
    html_chars = total_chars - css_chars - js_chars

    return [
        ("разметка + head (HTML)", html_lines, html_chars),
        (f"CSS inline (<style>, {style_start + 1}-{style_end + 1})", css_lines, css_chars),
        (f"JS inline (<script>, {script_start + 1}-{script_end + 1})", js_lines, js_chars),
    ]


def fmt(number: int) -> str:
    return f"{number:,}".replace(",", " ")


def main() -> int:
    if not PAGE.is_file():
        print(f"[FAIL] нет файла: {PAGE}")
        return 1

    raw = PAGE.read_text(encoding="utf-8")
    lines = raw.splitlines()

    print(f"{PAGE.relative_to(ROOT)}  -  {len(lines)} строк, {fmt(len(raw))} символов")
    total_lines = 0
    total_chars = 0
    for name, count, chars in measure(lines):
        total_lines += count
        total_chars += chars
        tokens = round(chars / 4)
        print(f"  {name:<44} {count:>6} стр.  {fmt(chars):>9} симв.  ~{fmt(tokens):>7} ток.")

    print(f"  {'итого':<44} {total_lines:>6} стр.  {fmt(total_chars):>9} симв.  ~{fmt(round(total_chars / 4)):>7} ток.")

    for path in EXTERNAL:
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            print(f"{path.relative_to(ROOT)}  -  {len(text.splitlines())} строк, {fmt(len(text))} символов")
        else:
            print(f"{path.relative_to(ROOT)}  -  ещё не создан")

    return 0


if __name__ == "__main__":
    sys.exit(main())
