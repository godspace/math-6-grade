#!/usr/bin/env python3
"""Headless-проверка произвольных страниц: ошибки консоли + маркер загрузки.

Открывает указанные HTML в headless Edge/Chrome с `--dump-dom`, читает
`CONSOLE`-строки из stderr (нужен `--enable-logging=stderr`) и печатает
по странице: число ошибок JS, число предупреждений, найден ли текст `--expect`.

Зачем: шаги плана (§15) требуют «пройти изменённые страницы, в консоли нет
`is not defined`». Руками это долго; инструмент даёт воспроизводимый PASS/FAIL
по каждой странице без изменения самих страниц.

Примеры:
    python -X utf8 tools/page_console.py trainers/divisibility/gcd.html
    python -X utf8 tools/page_console.py "trainers/divisibility/*.html" --budget 5000
    python -X utf8 tools/page_console.py index.html --expect "Математика" --offline
    python -X utf8 tools/page_console.py index.html --expect "Математика"
    python -X utf8 tools/page_console.py trainers/divisibility/lcm.html --dump-dir %TEMP%\\dom

Коды возврата: 0 - все страницы чистые, 1 - есть ошибки JS/не найден маркер,
2 - нет файлов/браузера.
"""

from __future__ import annotations

import argparse
import glob
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

# Оба формата строки Chromium: "INFO:CONSOLE(12)] ..." и "INFO:CONSOLE:12] ...".
CONSOLE_RE = re.compile(
    r'CONSOLE(?:\((?P<line1>\d+)\):|:(?P<line2>\d+)\])\s*"(?P<msg>.*?)",\s*source:\s*(?P<src>\S+)',
    re.DOTALL,
)
# Сообщения, которые считаем падением: необработанные исключения и падения промисов.
ERROR_RE = re.compile(r"Uncaught|Unhandled|is not defined|is not a function", re.IGNORECASE)
# Шум, который к нашему коду отношения не имеет (нет сети в headless, счётчики, DevTools-протокол).
NOISE_RE = re.compile(
    r"favicon\.ico|net::ERR_|Failed to load resource|Tracking Prevention|ProtocolLaunch|DevTools",
    re.IGNORECASE,
)

CONSOLE_MAP = str.maketrans({"↶": "<-", "↷": "->", "—": "-", "≈": "~", "→": "->", "«": '"', "»": '"'})


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


def expand_pages(patterns: list) -> list:
    """Разворачивает аргументы (файлы и mask-шаблоны) в список существующих HTML."""
    pages = []
    for pattern in patterns:
        matched = sorted(glob.glob(pattern)) if any(ch in pattern for ch in "*?[") else [pattern]
        for item in matched:
            path = Path(item)
            if not path.is_absolute():
                path = Path.cwd() / path
            if path.is_file():
                pages.append(path.resolve())
            else:
                print(f"[SKIP] нет файла: {item}")
    return pages


def run_page(browser: Path, page: Path, budget: int, timeout: int, keep_profile: bool, offline: bool = False) -> dict:
    """Грузит страницу в headless-браузере, возвращает DOM и разобранные сообщения консоли."""
    profile = Path(tempfile.mkdtemp(prefix="page-console-"))
    argv = [
        str(browser),
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        "--disable-extensions",
        "--mute-audio",
        f"--user-data-dir={profile}",
        "--enable-logging=stderr",
        "--v=1",
        f"--virtual-time-budget={budget}",
        "--dump-dom",
    ]
    if offline:
        # Внешние запросы (CDN, шрифты, счётчики) падают сразу, а не держат браузер.
        argv.append("--host-resolver-rules=MAP * ~NOTFOUND")
    argv.append(page.as_uri())

    dom = ""
    stderr = ""
    problem = ""
    try:
        proc = subprocess.run(argv, capture_output=True, timeout=timeout)
        dom = proc.stdout.decode("utf-8", "replace")
        stderr = proc.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        problem = f"таймаут {timeout} с"
    finally:
        if not keep_profile:
            shutil.rmtree(profile, ignore_errors=True)

    messages = []
    for match in CONSOLE_RE.finditer(stderr):
        text = html.unescape(match.group("msg")).strip()
        if text:
            messages.append({"text": text, "source": match.group("src")})

    return {"dom": dom, "messages": messages, "problem": problem}


def verdict(messages: list) -> tuple:
    """Делит сообщения на ошибки и предупреждения (шум headless-режима отбрасываем)."""
    errors, warnings = [], []
    for item in messages:
        if NOISE_RE.search(item["text"]):
            continue
        if ERROR_RE.search(item["text"]):
            errors.append(item["text"])
        else:
            warnings.append(item["text"])
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Headless-проверка страниц: ошибки JS в консоли и маркер загрузки.")
    parser.add_argument("pages", nargs="+", help="пути или маски HTML-страниц")
    parser.add_argument("--budget", type=int, default=4000, help="virtual-time-budget, мс (по умолчанию 4000)")
    parser.add_argument("--timeout", type=int, default=120, help="жёсткий таймаут процесса, с (по умолчанию 120)")
    parser.add_argument("--expect", default=None, help="текст, который обязан присутствовать в итоговом DOM")
    parser.add_argument("--dump-dir", default=None, help="куда сохранить снятый DOM (по странице)")
    parser.add_argument("--browser", default=None, help="путь к msedge.exe/chrome.exe")
    parser.add_argument("--keep-profile", action="store_true", help="не удалять временный профиль браузера")
    parser.add_argument("--quiet", action="store_true", help="печатать только итог по страницам")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="заблокировать внешние запросы (CDN, шрифты, счётчики) — быстрее и детерминированнее",
    )
    args = parser.parse_args()

    pages = expand_pages(args.pages)
    if not pages:
        print("[FAIL] не найдено ни одной страницы")
        return 2

    browser = find_browser(args.browser)
    dump_dir = Path(args.dump_dir) if args.dump_dir else None
    if dump_dir:
        dump_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    for page in pages:
        try:
            name = page.relative_to(ROOT).as_posix()
        except ValueError:
            name = page.as_posix()
        result = run_page(browser, page, args.budget, args.timeout, args.keep_profile, args.offline)
        if dump_dir:
            (dump_dir / f"{page.stem}.dom.html").write_text(result["dom"], encoding="utf-8")

        errors, warnings = verdict(result["messages"])
        missing = bool(args.expect) and args.expect not in result["dom"]
        ok = not result["problem"] and not errors and not missing and bool(result["dom"])

        print(f"[{'PASS' if ok else 'FAIL'}] {console(name)}")
        print(f"       ошибок JS: {len(errors)}, предупреждений: {len(warnings)}, DOM: {len(result['dom'])} симв.")
        if result["problem"]:
            print(f"       проблема: {console(result['problem'])}")
        if missing:
            print(f"       не найден текст: {console(args.expect)}")
        if not args.quiet:
            for text in errors[:10]:
                print(f"       error: {console(text)[:200]}")
            for text in warnings[:5]:
                print(f"       warn : {console(text)[:160]}")

        if not ok:
            failed.append(name)

    total = len(pages)
    print(f"\nитог: {total - len(failed)}/{total} страниц чистые")
    if failed:
        print("падения: " + ", ".join(console(item) for item in failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
