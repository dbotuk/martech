"""Таксономія модифікацій і JSON-схема одного результату.

Кожна модифікація — це НЕ новий креатив, а зміна одного-двох елементів
скрипта-переможця (хук, текст на екрані, CTA, кут болю). Так дизайнер
перевикористовує 70–90% уже змонтованого матеріалу.
"""

# тип -> (опис для людини, що саме змінюється, орієнтовний час моушн-роботи, хв)
MOD_TYPES = {
    "hook_question":     ("Хук-питання, яке глядач впізнає про себе",        ["VO 0–3s", "on-screen 0–3s"], 60),
    "hook_pain":         ("Хук із дослівної цитати болю (UGC-стиль)",          ["VO 0–3s", "on-screen 0–3s"], 60),
    "hook_claim":        ("Хук — смілива обіцянка результату",                 ["VO 0–3s", "on-screen 0–3s"], 60),
    "hook_social_proof": ("Хук із соціальним доказом",                         ["VO 0–3s", "on-screen 0–3s"], 60),
    "hook_curiosity":    ("Хук-інтрига: 'подивись ближче'",                    ["VO 0–3s", "on-screen 0–3s", "crop/zoom 0–3s"], 75),
    "hook_negative":     ("Негативний/контрінтуїтивний хук",                   ["VO 0–3s", "on-screen 0–3s"], 60),
    "hook_stat":         ("Хук із перевіреною цифрою",                         ["VO 0–3s", "on-screen 0–3s"], 60),
    "hook_pov":          ("POV-хук: сцена з життя глядача",                    ["VO 0–3s", "on-screen 0–3s"], 75),
    "onscreen_only":     ("Той самий VO, новий набір текстів на екрані",        ["on-screen all scenes"], 45),
    "cta_swap":          ("Інший CTA/оффер в останніх 3 секундах",             ["VO last 3s", "end card"], 30),
    "angle_swap":        ("Той самий ролик під інший біль/сегмент",            ["VO 0–3s", "on-screen 0–3s", "VO body line"], 90),
}

BASELINE_MINUTES = 180  # 3 години на модифікацію сьогодні (дата-рум)

MOD_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "modifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": list(MOD_TYPES.keys())},
                    "hypothesis": {"type": "string",
                                   "description": "Якщо ... то ... тому що ... (що тестуємо і чому це має підняти CTR/CR)"},
                    "hook_vo": {"type": "string", "description": "Перші 3 секунди голосом, 1–2 речення, розмовною англійською"},
                    "hook_onscreen": {"type": "string", "description": "Текст на екрані в перші 3 секунди, до 6 слів"},
                    "body_changes": {"type": "array", "items": {"type": "string"},
                                     "description": "Що змінити в тілі ролика; порожній список = без змін"},
                    "cta": {"type": "string", "description": "Фінальний заклик до дії (VO або текст)"},
                    "pain_ref": {"type": "string", "description": "Який біль із CSV використано (дослівно поле pain) або 'none'"},
                    "designer_notes": {"type": "string", "description": "1 речення: що саме перемонтувати"},
                },
                "required": ["type", "hypothesis", "hook_vo", "hook_onscreen", "body_changes", "cta", "pain_ref", "designer_notes"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["modifications"],
    "additionalProperties": False,
}
