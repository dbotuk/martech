"""Вивід: markdown-бриф для дизайнера, CSV для Airtable, JSON для інтеграцій."""
import csv
import json
import re
from pathlib import Path
from .schema import MOD_TYPES, BASELINE_MINUTES

NO_PAIN = ("", "none", "-", "—")
NO_PAIN_LABEL = "— (без прив’язки до болю)"


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9$]+", " ", (s or "").lower()).strip()


def enrich(mods: list[dict], script: dict) -> list[dict]:
    """Додає id, що саме змінюється, оцінку часу моушн-роботи і скільки хвилин зекономлено проти 3 год.

    База береться з таксономії типу; якщо рушій додатково змінив тіло ролика або CTA,
    ці елементи й хвилини додаються зверху, щоб оцінка відповідала фактичному брифу."""
    slug = script["slug"]
    original_cta = _norm(script.get("cta", ""))
    out = []
    for i, m in enumerate(mods, 1):
        desc, changed, minutes = MOD_TYPES.get(m["type"], ("", [], 90))
        changed = list(changed)
        body = [b for b in m.get("body_changes", []) if b.strip()]
        if body and not any("body" in c or "all scenes" in c for c in changed):
            changed.append(f"body scenes ({len(body)})")
            minutes += 15 * min(len(body), 3)
        if original_cta and _norm(m.get("cta")) != original_cta and not any("end card" in c for c in changed):
            changed.append("CTA / end card")
            minutes += 15
        pain = m.get("pain_ref", "").strip()
        out.append({
            "mod_id": f"{slug}-m{i:02d}",
            **m,
            "body_changes": body,
            "pain_ref": "" if pain.lower() in NO_PAIN else pain,
            "type_desc": desc,
            "changed_elements": changed,
            "est_motion_minutes": minutes,
            "saved_minutes_vs_baseline": BASELINE_MINUTES - minutes,
        })
    return out


def to_markdown(script: dict, mods: list[dict], engine: str) -> str:
    total_saved_h = sum(m["saved_minutes_vs_baseline"] for m in mods) / 60
    lines = [
        f"# Бриф на модифікації: {script['title']}",
        "",
        f"Рушій: `{engine}` · модифікацій: {len(mods)} · орієнтовна економія проти 3 год/модифікацію: **{total_saved_h:.1f} год** на цей бриф.",
        "",
        "## Оригінальний хук (для порівняння)",
        "",
        script["hook"] or "_(не задано)_",
        "",
        "## Модифікації",
        "",
    ]
    for m in mods:
        lines += [
            f"### {m['mod_id']} · {m['type']} — {m['type_desc']}",
            "",
            f"**Гіпотеза.** {m['hypothesis']}",
            "",
            f"**Хук, VO (0–3 с):** {m['hook_vo']}",
            "",
            f"**Текст на екрані (0–3 с):** {m['hook_onscreen']}",
            "",
            *(["**Зміни в тілі ролика:**", ""] + [f"- {b}" for b in m["body_changes"]]
              if m["body_changes"] else ["**Зміни в тілі ролика:** без змін"]),
            "",
            f"**CTA:** {m['cta']}",
            "",
            f"**Біль із дослідження:** {m['pain_ref'] or NO_PAIN_LABEL}",
            "",
            f"**Дизайнеру:** {m['designer_notes']} Змінюється: {', '.join(m['changed_elements'])}. Оцінка моушн-роботи: ~{m['est_motion_minutes']} хв.",
            "",
        ]
    return "\n".join(lines)


CSV_COLUMNS = ["mod_id", "type", "hypothesis", "hook_vo", "hook_onscreen", "body_changes", "cta",
               "pain_ref", "designer_notes", "changed_elements", "est_motion_minutes", "saved_minutes_vs_baseline"]


def write_all(out_dir: Path, script: dict, mods: list[dict], engine: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / "brief.md"
    csv_path = out_dir / "mods.csv"
    json_path = out_dir / "mods.json"

    md_path.write_text(to_markdown(script, mods, engine), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        for m in mods:
            row = {k: m[k] for k in CSV_COLUMNS}
            row["body_changes"] = " | ".join(m["body_changes"])
            row["changed_elements"] = " | ".join(m["changed_elements"])
            w.writerow(row)
    json_path.write_text(json.dumps({"script": script["title"], "engine": engine, "modifications": mods},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    return {"brief": md_path, "csv": csv_path, "json": json_path}
