#!/usr/bin/env python3
"""Размеры math_board: строки, символы и ≈токены по файлам (метрика оптимизации).

После шага 4.1/4.2 inline-секций в HTML нет: страница меряется целиком, рядом
показываются вынесенные assets/math_board.css и assets/math_board.js, внизу итог.

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
FILES = (PAGE, *EXTERNAL)


def measure(path: Path) -> tuple:
    """Возвращает (строк, символов) для файла: символы — как в read_text (UTF-8)."""
    raw = path.read_text(encoding="utf-8")
    return len(raw.splitlines()), len(raw)


def fmt(number: int) -> str:
    return f"{number:,}".replace(",", " ")


def main() -> int:
    if not PAGE.is_file():
        print(f"[FAIL] нет файла: {PAGE}")
        return 1

    rows = []
    missing = []
    for path in FILES:
        if path.is_file():
            rows.append((str(path.relative_to(ROOT)), *measure(path)))
        else:
            missing.append(path)

    width = max([len(name) for name, _, _ in rows] + [len("итого")])
    total_lines = 0
    total_chars = 0
    for name, count, chars in rows:
        total_lines += count
        total_chars += chars
        tokens = round(chars / 4)
        print(f"  {name:<{width}} {count:>6} стр.  {fmt(chars):>9} симв.  ~{fmt(tokens):>7} ток.")

    if len(rows) > 1:
        print(f"  {'итого':<{width}} {total_lines:>6} стр.  {fmt(total_chars):>9} симв.  ~{fmt(round(total_chars / 4)):>7} ток.")

    for path in missing:
        print(f"{path.relative_to(ROOT)}  -  ещё не создан")

    return 0


if __name__ == "__main__":
    sys.exit(main())
