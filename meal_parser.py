"""Parser simples de texto livre -> lista de alimentos + quantidades -> nutrientes.
Não é IA real, é um parser por regex + tabela local. Serve de base para depois
ligar a um modelo de linguagem (ex: API da OpenAI/Anthropic) se desejado."""
import re
from food_data import lookup, UNIT_G_DEFAULTS, portion_grams

# separadores comuns de itens numa frase
SPLIT_RE = re.compile(r"\s*(?:,| e | com |\+)\s*", flags=re.IGNORECASE)

# unidades que significam "1 porção normal para uma pessoa"
DOSE_UNITS = ("dose", "doses", "porcao", "porção", "porcoes", "porções")

# "200g de frango", "200 g frango", "1 banana", "2 ovos", "uma fatia de pao", "1 dose de arroz"
QTY_RE = re.compile(
    r"^\s*(?P<qty>\d+[\.,]?\d*)\s*(?P<unit>g|gr|gramas|kg|ml|un|unidades|unidade|doses|dose|por[cç][oõ]es|por[cç][aã]o)?\s*(?:de\s+)?(?P<food>.+?)\s*$",
    flags=re.IGNORECASE,
)

WORD_QTY = {"uma": 1, "um": 1, "duas": 2, "dois": 2, "tres": 3, "três": 3, "quatro": 4}


def parse_meal_text(text: str):
    """Retorna (total_dict, itens_detalhe) onde total_dict tem kcal/proteina_g/hidratos_g/gordura_g
    e itens_detalhe é lista de {texto, alimento_encontrado, gramas, kcal, proteina_g, hidratos_g, gordura_g}."""
    parts = [p for p in SPLIT_RE.split(text) if p.strip()]
    if not parts:
        parts = [text]

    total = {"kcal": 0.0, "proteina_g": 0.0, "hidratos_g": 0.0, "gordura_g": 0.0}
    itens = []

    for part in parts:
        item = _parse_item(part)
        itens.append(item)
        if item["encontrado"]:
            total["kcal"] += item["kcal"]
            total["proteina_g"] += item["proteina_g"]
            total["hidratos_g"] += item["hidratos_g"]
            total["gordura_g"] += item["gordura_g"]

    return total, itens


def _parse_item(part: str):
    part_clean = part.strip()
    lower = part_clean.lower()

    qty_g = None
    food_name = part_clean

    # tenta "uma banana" / "duas fatias..."
    for word, num in WORD_QTY.items():
        if lower.startswith(word + " "):
            food_name = part_clean[len(word):].strip()
            qty_g = None
            grams_per_unit = UNIT_G_DEFAULTS.get(food_name.lower(), 100)
            qty_g = num * grams_per_unit
            break

    m = QTY_RE.match(part_clean)
    if qty_g is None and m:
        qty = m.group("qty")
        unit = (m.group("unit") or "").lower()
        food_name = m.group("food").strip()
        try:
            qty_val = float(qty.replace(",", "."))
        except ValueError:
            qty_val = None

        if qty_val is not None:
            if unit == "" and food_name.lower() in UNIT_G_DEFAULTS:
                # sem unidade explícita mas alimento é contável (ex: "2 ovos")
                qty_g = qty_val * UNIT_G_DEFAULTS[food_name.lower()]
            elif unit in ("g", "gr", "gramas", ""):
                qty_g = qty_val
            elif unit == "kg":
                qty_g = qty_val * 1000
            elif unit == "ml":
                qty_g = qty_val  # aproximação 1ml=1g
            elif unit in ("un", "unidade", "unidades"):
                grams_per_unit = UNIT_G_DEFAULTS.get(food_name.lower(), 100)
                qty_g = qty_val * grams_per_unit
            elif unit.startswith("dose") or unit.startswith("por"):
                # "1 dose de arroz" / "2 porções de frango" -> usa o tamanho
                # normal de uma porção deste alimento (definido em food_data.py)
                qty_g = qty_val * portion_grams(food_name)

    if qty_g is None:
        qty_g = 100  # assume 100g por omissão se não conseguir perceber quantidade
        food_name = part_clean

    vals = lookup(food_name)
    if vals is None:
        return {
            "texto": part_clean, "alimento_encontrado": None, "gramas": qty_g,
            "kcal": 0, "proteina_g": 0, "hidratos_g": 0, "gordura_g": 0, "encontrado": False,
        }

    kcal100, prot100, carb100, fat100 = vals
    factor = qty_g / 100.0
    return {
        "texto": part_clean,
        "alimento_encontrado": food_name,
        "gramas": round(qty_g, 1),
        "kcal": round(kcal100 * factor, 1),
        "proteina_g": round(prot100 * factor, 1),
        "hidratos_g": round(carb100 * factor, 1),
        "gordura_g": round(fat100 * factor, 1),
        "encontrado": True,
    }
