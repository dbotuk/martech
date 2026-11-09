"""Рушій на Claude API: один запит, структурований JSON-вивід за MOD_JSON_SCHEMA."""
import json
import anthropic
from .schema import MOD_JSON_SCHEMA, MOD_TYPES

MODEL = "claude-opus-5-5"

SYSTEM = """You are a senior direct-response creative strategist for SockLock, a DTC subscription brand
(magnetic socks that never get lost in the wash; 5 pairs for $29, then a quarterly refill).
You write MODIFICATIONS of a winning Meta video ad: keep 70–90% of the footage, change only the hook
(first 3 seconds), on-screen text, CTA, or the pain angle. Each modification must be a clean A/B test
with ONE clear hypothesis. Write ad copy in natural, spoken {lang_name}; keep hooks under 2 sentences,
on-screen text under 6 words. Never invent statistics or claims: use only facts and verified stats from
the product sheet, and never use anything from the "Don't say" list. Pain points must come from the
pains list when a modification references one (copy the `pain` field verbatim into pain_ref).
Write `hypothesis` and `designer_notes` in Ukrainian. Hypothesis format: "Якщо ..., то ..., тому що ...".
Cover different modification types; at most two of the same type."""

LANGS = {"en": "US English", "de": "German (Germany), adapted culturally, not translated literally",
         "fr": "French (France), adapted culturally, not translated literally",
         "uk": "Ukrainian"}


def _user_prompt(script, pains, product, n):
    pains_txt = "\n".join(f"- pain: {p['pain']} | quote: {p['quote']} | segment: {p['segment']}" for p in pains) or "- (no pains provided)"
    types_txt = "\n".join(f"- {k}: {v[0]}" for k, v in MOD_TYPES.items())
    return f"""# Winning script (keep its structure)
{script['raw']}

# Pain points from research (CSV)
{pains_txt}

# Product sheet
{product['raw'] or '(none)'}

# Modification types available
{types_txt}

Generate exactly {n} modifications as JSON matching the schema."""


def generate(script, pains, product, n=10, lang="en", model=MODEL) -> list[dict]:
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        system=SYSTEM.format(lang_name=LANGS.get(lang, lang)),
        messages=[{"role": "user", "content": _user_prompt(script, pains, product, n)}],
        output_config={"format": {"type": "json_schema", "schema": MOD_JSON_SCHEMA}},
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("Модель відмовилась відповідати (stop_reason=refusal).")
    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    usage = response.usage
    print(f"[claude] {model}: {usage.input_tokens} in / {usage.output_tokens} out tokens")
    return data["modifications"][:n]
