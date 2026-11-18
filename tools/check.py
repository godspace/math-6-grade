#!/usr/bin/env python3
"""Headless-проверка math_board.html (рецепт из MATH_BOARD_PLAN.md).

Запускает tests/math_board.smoke.html в headless Edge/Chrome с --dump-dom,
читает document.body[data-test] / [data-err] и печатает результат.

Примеры:
    python tools/check.py
    python tools/check.py --keep-profile
    python tools/check.py --browser "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"

Коды возврата: 0 - все проверки прошли, 1 - есть падения, 2 - нет файлов/браузера.
"""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Консоль Windows (cp866/cp1251) не умеет символы вроде ↶/↷ — не падаем, а подменяем на '?'.
for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass

ROOT = Path(__file__).resolve().parent.parent
SMOKE_PAGE = ROOT / "tests" / "math_board.smoke.html"
BOARD_PAGE = ROOT / "trainers" / "fractions" / "math_board.html"

BODY_RE = re.compile(r"<body\b([^>]*)>", re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(r'([\w-]+)\s*=\s*"([^"]*)"')
LOG_RE = re.compile(r'<pre id="log">(.*?)</pre>', re.IGNORECASE | re.DOTALL)
SUMMARY_RE = re.compile(r"pass=(\d+);fail=(\d+);total=(\d+)")

# Символы из имён проверок, которых нет в консольных кодировках Windows.
CONSOLE_MAP = str.maketrans({"↶": "<-", "↷": "->", "—": "-", "≈": "~", "→": "->"})


def console(text: str) -> str:
    """Заменяет «непечатаемые» в cp866/cp1251 символы на ASCII-аналоги."""
    return text.translate(CONSOLE_MAP)


def browser_candidates() -> list:
    """Типовые пути установки Edge/Chrome на Windows и Unix."""
    paths = []
    for env_key in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
        base = os.environ.get(env_key)
        if not base:
            continue
        paths.append(Path(base) / "Microsoft/Edge/Application/msedge.exe")
        paths.append(Path(base) / "Google/Chrome/Application/chrome.exe")
    paths += [
        Path("/usr/bin/microsoft-edge"),
        Path("/usr/bin/google-chrome"),
        Path("/usr/bin/chromium"),
        Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    ]
    return paths


def find_browser(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return path
        raise SystemExit(f"[FAIL] не найден браузер: {explicit}")

    env_path = os.environ.get("EDGE_PATH") or os.environ.get("BROWSER_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    for name in ("msedge", "chrome", "google-chrome", "chromium"):
        found = shutil.which(name)
        if found:
            return Path(found)

    for path in browser_candidates():
        if path.is_file():
            return path

    raise SystemExit("[FAIL] не найден Edge/Chrome. Укажите путь: --browser <путь к msedge.exe>")


def parse_dump(dom: str) -> tuple:
    """Достаёт атрибуты <body> и текст лога из --dump-dom."""
    body = BODY_RE.search(dom)
    attrs = {}
    if body:
        attrs = {key.lower(): html.unescape(value) for key, value in ATTR_RE.findall(body.group(1))}

    log_text = ""
    log_match = LOG_RE.search(dom)
    if log_match:
        log_text = html.unescape(re.sub(r"<[^>]+>", "", log_match.group(1)))
        log_text = log_text.replace("\r\n", "\n").replace("\r", "\n").strip()

    return attrs, log_text


def run_browser(browser: Path, url: str, budget: int, timeout: int, keep_profile: bool) -> tuple:
    """Запускает браузер в headless-режиме и возвращает (dom, stderr, ошибка)."""
    profile = Path(tempfile.mkdtemp(prefix="mathboard-smoke-"))
    argv = [
        str(browser),
        "--headless",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        f"--user-data-dir={profile}",
        f"--virtual-time-budget={budget}",
        "--dump-dom",
        url,
    ]

    proc = None
    error = None
    try:
        proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except subprocess.TimeoutExpired:
        error = f"браузер не ответил за {timeout} с"
    except OSError as exc:
        error = f"не удалось запустить браузер: {exc}"
    finally:
        if not keep_profile:
            shutil.rmtree(profile, ignore_errors=True)

    if error:
        return None, "", error

    dom = proc.stdout.decode("utf-8", "replace")
    stderr = proc.stderr.decode("utf-8", "replace").strip()
    if not dom.strip():
        return None, stderr, f"пустой вывод --dump-dom (код браузера {proc.returncode})"
    return dom, stderr, None


def print_tail(text: str, limit: int = 10) -> None:
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return
    print("--- stderr браузера (последние строки) ---")
    for line in lines[-limit:]:
        print("  " + line)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-проверка math_board.html в headless-браузере")
    parser.add_argument("--browser", help="путь к msedge.exe / chrome.exe (по умолчанию ищется автоматически)")
    parser.add_argument("--budget", type=int, default=20000, help="--virtual-time-budget, мс (по умолчанию 20000)")
    parser.add_argument("--timeout", type=int, default=120, help="жёсткий таймаут процесса, с (по умолчанию 120)")
    parser.add_argument("--keep-profile", action="store_true", help="не удалять временный профиль браузера")
    args = parser.parse_args(argv)

    for page in (SMOKE_PAGE, BOARD_PAGE):
        if not page.is_file():
            print(f"[FAIL] нет файла: {page}")
            return 2

    try:
        browser = find_browser(args.browser)
    except SystemExit as exc:
        print(exc)
        return 2

    print(f"Браузер: {browser}")
    print(f"Тест:    {SMOKE_PAGE}")
    print(f"Доска:   {BOARD_PAGE}")

    dom, stderr, error = run_browser(browser, SMOKE_PAGE.as_uri(), args.budget, args.timeout, args.keep_profile)
    if error:
        print(f"[FAIL] {error}")
        print_tail(stderr)
        return 1

    attrs, log_text = parse_dump(dom)
    summary = attrs.get("data-test", "")
    if not SUMMARY_RE.search(summary):
        print("[FAIL] тест не дошёл до итога (нет data-test в <body>)")
        if log_text:
            print("--- лог теста ---")
            print(console(log_text))
        print_tail(stderr)
        return 1

    passed, failed, total = (int(value) for value in SUMMARY_RE.search(summary).groups())
    if log_text:
        print("--- лог теста ---")
        print(console(log_text))
        print("----------------")

    if failed == 0 and total > 0:
        print(f"[OK] {passed}/{total} проверок пройдено")
        return 0

    print(f"[FAIL] пройдено {passed} из {total}")
    for part in attrs.get("data-err", "").split(" | "):
        if part.strip():
            print("  - " + console(part.strip()))
    print_tail(stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
