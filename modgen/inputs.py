"""Читання вхідних файлів: скрипт-переможець (.md), болі (.csv), факти про продукт (.md)."""
import csv
import re
from pathlib import Path


def _sections(md: str) -> dict:
    """Розбиває markdown на {назва_розділу_lower: текст} за заголовками '## '."""
    out, current, buf = {}, "_intro", []
    for line in md.splitlines():
        if line.startswith("## "):
            out[current] = "\n".join(buf).strip()
            current, buf = line[3:].strip().lower(), []
        else:
            buf.append(line)
    out[current] = "\n".join(buf).strip()
    return out


def load_script(path: str) -> dict:
    md = Path(path).read_text(encoding="utf-8")
    title = next((l[2:].strip() for l in md.splitlines() if l.startswith("# ")), Path(path).stem)
    sec = _sections(md)

    def pick(*keys):
        for k, v in sec.items():
            if any(k.startswith(key) for key in keys):
                return v
        return ""

    return {
        "title": title,
        "slug": re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"),
        "hook": pick("hook"),
        "body": pick("body", "script", "scenes"),
        "cta": pick("cta", "call"),
        "onscreen": pick("on-screen", "onscreen", "text on screen"),
        "meta": pick("meta", "performance", "stats"),
        "raw": md,
    }


def load_pains(path: str | None) -> list[dict]:
    if not path:
        return []
    with open(path, newline="", encoding="utf-8") as f:
        rows = [dict(r) for r in csv.DictReader(f)]
    for r in rows:
        r.setdefault("pain", "")
        r.setdefault("quote", "")
        r.setdefault("segment", "")
        r.setdefault("source", "")
    return [r for r in rows if r["pain"].strip()]


def load_product(path: str | None) -> dict:
    """Повертає {'raw': весь текст, 'benefits': [...], 'proof': [...], 'offers': [...], 'stats': [...], 'dont_say': [...]}."""
    if not path:
        return {"raw": "", "benefits": [], "proof": [], "offers": [], "stats": [], "dont_say": []}
    md = Path(path).read_text(encoding="utf-8")
    sec = _sections(md)

    def bullets(key):
        for k, v in sec.items():
            if k.startswith(key):
                return [l.lstrip("-* ").strip() for l in v.splitlines() if l.strip().startswith(("-", "*"))]
        return []

    return {
        "raw": md,
        "benefits": bullets("benefit"),
        "proof": bullets("proof"),
        "offers": bullets("offer"),
        "stats": bullets("verified"),
        "dont_say": bullets("don"),
    }
