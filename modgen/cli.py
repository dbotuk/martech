"""CLI: modgen.py <winner_script.md> [--pains pains.csv] [--product product.md] [--n 10] [--engine auto|claude|rules]"""
import argparse
import os
import sys
from pathlib import Path

from . import inputs, render
from .schema import BASELINE_MINUTES


def pick_engine(name: str) -> str:
    if name in ("claude", "rules"):
        return name
    # auto: Claude, якщо є ключ або профіль; інакше офлайн-шаблони
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "claude"
    print("[info] ANTHROPIC_API_KEY не знайдено — використовую офлайновий рушій `rules`. "
          "Для якісніших варіантів: export ANTHROPIC_API_KEY=... і --engine claude", file=sys.stderr)
    return "rules"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="modgen", description="Генератор модифікацій креативів зі скрипта-переможця (SockLock).")
    ap.add_argument("script", help="markdown зі скриптом-переможцем (розділи: ## Hook, ## Body, ## CTA, ## On-screen)")
    ap.add_argument("--pains", help="CSV з болями: pain,quote,segment,source")
    ap.add_argument("--product", help="markdown з фактами про продукт: ## Benefits, ## Proof, ## Offers, ## Verified stats, ## Don't say")
    ap.add_argument("--n", type=int, default=10, help="скільки модифікацій (за замовчуванням 10)")
    ap.add_argument("--engine", default="auto", choices=["auto", "claude", "rules"])
    ap.add_argument("--lang", default="en", help="мова копі для рушія claude: en, de, fr (адаптація, не переклад)")
    ap.add_argument("--model", default=None, help="перевизначити модель Claude")
    ap.add_argument("--seed", type=int, default=7, help="seed для рушія rules")
    ap.add_argument("--out", default="out", help="тека для результатів")
    args = ap.parse_args(argv)

    script = inputs.load_script(args.script)
    pains = inputs.load_pains(args.pains)
    product = inputs.load_product(args.product)
    engine = pick_engine(args.engine)

    if engine == "claude":
        try:
            from . import engine_claude
        except ImportError:
            print("[error] пакет anthropic не встановлено. Виконайте: pip install -r requirements.txt "
                  "(або запустіть з --engine rules).", file=sys.stderr)
            return 2
        kwargs = {"model": args.model} if args.model else {}
        try:
            mods = engine_claude.generate(script, pains, product, n=args.n, lang=args.lang, **kwargs)
        except TypeError as e:  # SDK: не знайдено ключ/профіль
            print(f"[error] Claude API недоступний: {e}\n  Задайте ANTHROPIC_API_KEY або запустіть з --engine rules.", file=sys.stderr)
            return 2
    else:
        from . import engine_rules
        if args.lang != "en":
            print("[warn] рушій rules пише лише англійською; --lang проігноровано", file=sys.stderr)
        mods = engine_rules.generate(script, pains, product, n=args.n, seed=args.seed)

    mods = render.enrich(mods, script)
    paths = render.write_all(Path(args.out) / script["slug"], script, mods, engine)

    saved_h = sum(m["saved_minutes_vs_baseline"] for m in mods) / 60
    print(f"\n✔ {len(mods)} модифікацій для «{script['title']}» (рушій: {engine})")
    print(f"  бриф:  {paths['brief']}")
    print(f"  CSV:   {paths['csv']}  (імпорт в Airtable)")
    print(f"  JSON:  {paths['json']}")
    print(f"  орієнтовна економія часу дизайнера: {saved_h:.1f} год проти {len(mods) * BASELINE_MINUTES / 60:.0f} год за сьогоднішніх 3 год/модифікацію")
    return 0


if __name__ == "__main__":
    sys.exit(main())
