"""Офлайновий рушій: детерміновані шаблони + слоти з CSV болів і фактів про продукт.

Працює без API-ключа і без інтернету. Якість нижча за Claude, але результат
структурно той самий, тож дизайнер отримує бриф у перший день.
"""
import random
import re
from .schema import MOD_TYPES


def _first_sentence(text: str) -> str:
    for line in text.splitlines():
        line = line.strip().lstrip("-* ")
        if line:
            return line
    return ""


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s


def _clean(s: str) -> str:
    """Прибирає дужки з джерелом: 'X (internal survey ...)' -> 'X'."""
    return re.sub(r"\s*\([^)]*\)", "", s).strip()


def _short(s: str, max_words: int = 6) -> str:
    """Текст на екрані. Якщо у фразі є 'коротка | довга' форма — беремо коротку;
    інакше перший фрагмент до коми/двокрапки, обрізаний до max_words слів."""
    if "|" in s:
        return s.split("|")[0].strip()
    first = re.split(r"[,:;]", _clean(s))[0].rstrip(".")
    words = first.split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")


def _long(s: str) -> str:
    """Для VO беремо довгу форму з 'коротка | довга' або всю фразу без дужок."""
    return _clean(s.split("|")[-1].strip()) if "|" in s else _clean(s)


def generate(script: dict, pains: list[dict], product: dict, n: int = 10, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    benefits = product["benefits"] or ["Your socks stay in pairs. Every wash."]
    proof = product["proof"] or ["Thousands of pairs shipped"]
    offers = product["offers"] or ["5 pairs for $29"]
    stats = product["stats"] or []
    pains = pains or [{"pain": "one sock always goes missing", "quote": "I swear the dryer eats my socks", "segment": "general"}]
    original_cta = _first_sentence(script["cta"]) or offers[0]

    def pain():
        return rng.choice(pains)

    def hook_variants():
        """Повертає список (type, builder). Кожен builder -> dict полів модифікації."""
        return [
            ("hook_question", lambda p: dict(
                hook_vo=f"Be honest: {_lower_first(p['pain'])}?",
                hook_onscreen=_short(p["pain"]).capitalize() + "?",
                hypothesis=f"Якщо відкрити питанням про '{p['pain']}', глядач із сегмента '{p['segment'] or 'general'}' впізнає себе в перші 2 с і hold rate зросте.",
                pain_ref=p["pain"])),
            ("hook_pain", lambda p: dict(
                hook_vo=p["quote"] or f"{p['pain'].capitalize()}. Again.",
                hook_onscreen=f"POV: {_lower_first(p['pain'])}",
                hypothesis="Дослівна цитата болю звучить як UGC, а не реклама, тому менше скролять у першу секунду.",
                pain_ref=p["pain"])),
            ("hook_claim", lambda p: dict(
                hook_vo=f"This is the last time you lose a sock. {_long(rng.choice(benefits))}.",
                hook_onscreen=_short(rng.choice(benefits)),
                hypothesis="Пряма обіцянка результату працює на теплу аудиторію, яка вже бачила ролик про проблему.",
                pain_ref="none")),
            ("hook_social_proof", lambda p: dict(
                hook_vo=f"{_long(rng.choice(proof))}. Here's why.",
                hook_onscreen=_short(rng.choice(proof), 5),
                hypothesis="Соціальний доказ у перші 3 с знижує недовіру до 'гаджета для шкарпеток' і підіймає CR на квіз.",
                pain_ref="none")),
            ("hook_curiosity", lambda p: dict(
                hook_vo="There's a tiny magnet hidden in this sock. Watch what happens in the wash.",
                hook_onscreen="Look closer",
                hypothesis="Інтрига з макро-кадром магніту тримає увагу до демонстрації продукту (3–6 с).",
                pain_ref="none")),
            ("hook_negative", lambda p: dict(
                hook_vo="Stop buying socks. Seriously, stop.",
                hook_onscreen="STOP buying socks",
                hypothesis="Контрінтуїтивна заборона ламає патерн стрічки; тестуємо CTR проти позитивного хука.",
                pain_ref="none")),
            ("hook_stat", lambda p: dict(
                hook_vo=(_long(rng.choice(stats)) + ". I used to be one of them." if stats else f"{p['pain'].capitalize()} — for almost everyone."),
                hook_onscreen=(_short(stats[0]) if stats else _short(p["pain"])),
                hypothesis="Конкретна перевірена цифра додає ваги проблемі; беремо лише факти зі списку verified stats.",
                pain_ref=p["pain"] if not stats else "none")),
            ("hook_pov", lambda p: dict(
                hook_vo="POV: you open the dryer and every single sock has its partner.",
                hook_onscreen="every. single. pair.",
                hypothesis="Сцена бажаного результату замість проблеми; перевіряємо, чи 'після' продає краще, ніж 'до'.",
                pain_ref="none")),
        ]

    mods = []
    variants = hook_variants()
    rng.shuffle(variants)

    # 1) хуки — основна маса модифікацій
    for mtype, build in variants:
        if len(mods) >= max(n - 3, 1):
            break
        p = pain()
        fields = build(p)
        mods.append(dict(type=mtype, body_changes=[], cta=original_cta,
                         designer_notes="Перезаписати VO і текст на екрані для 0–3 с, решту ролика лишити.", **fields))

    # 2) один onscreen_only, один cta_swap, один angle_swap
    if len(mods) < n:
        mods.append(dict(type="onscreen_only",
                         hypothesis="Той самий VO, але тексти на екрані переписані під біль із CSV: тест для перегляду без звуку (~70% стрічки).",
                         hook_vo=_first_sentence(script["hook"]) or "(VO без змін)",
                         hook_onscreen=pains[0]["pain"].capitalize(),
                         body_changes=[f"Сцена 2: '{_short(rng.choice(benefits))}'", f"Сцена 3: '{_short(rng.choice(proof))}'", f"Фінал: '{_short(rng.choice(offers))}'"],
                         cta=original_cta, pain_ref=pains[0]["pain"],
                         designer_notes="Замінити лише текстові плашки, VO і монтаж без змін."))
    if len(mods) < n:
        new_offer = next((o for o in offers if o != original_cta), offers[0]).rstrip(".") + ". Link's below."
        mods.append(dict(type="cta_swap",
                         hypothesis="Інший оффер у фіналі: перевіряємо, чи ціна за пару продає краще за 'підписку'.",
                         hook_vo=_first_sentence(script["hook"]) or "(VO без змін)",
                         hook_onscreen="(без змін)", body_changes=[],
                         cta=new_offer, pain_ref="none",
                         designer_notes="Перемонтувати тільки останні 3 с і end card."))
    if len(mods) < n:
        p = pain()
        mods.append(dict(type="angle_swap",
                         hypothesis=f"Той самий ролик під сегмент '{p['segment'] or 'general'}': хук і одна репліка в тілі про '{p['pain']}'.",
                         hook_vo=f"If {_lower_first(p['pain'])}, this is for you.",
                         hook_onscreen=_clean(p["pain"]).capitalize() + "? Keep watching.",
                         body_changes=[f"Репліка в тілі: згадати '{p['pain']}' як причину купівлі"],
                         cta=original_cta, pain_ref=p["pain"],
                         designer_notes="Перезаписати 0–3 с та одну репліку в тілі; решта без змін."))

    # дозаповнюємо, якщо n більше за кількість шаблонів
    while len(mods) < n:
        mtype, build = rng.choice(variants)
        fields = build(pain())
        mods.append(dict(type=mtype, body_changes=[], cta=original_cta,
                         designer_notes="Перезаписати VO і текст на екрані для 0–3 с.", **fields))

    return mods[:n]
