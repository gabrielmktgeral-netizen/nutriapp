"""Tabela local de composição nutricional (por 100g) de alimentos comuns em Portugal.
Valores aproximados (fonte: tabelas de composição de alimentos genéricas)."""

# nome_chave: (kcal, proteina_g, hidratos_g, gordura_g) por 100g
FOODS = {
    "frango": (165, 31, 0, 3.6),
    "peito de frango": (165, 31, 0, 3.6),
    "frango grelhado": (165, 31, 0, 3.6),
    "carne de vaca": (250, 26, 0, 17),
    "bife": (271, 25, 0, 19),
    "porco": (242, 27, 0, 14),
    "lombo de porco": (143, 21, 0, 6),
    "peixe": (150, 22, 0, 6),
    "salmao": (208, 20, 0, 13),
    "salmão": (208, 20, 0, 13),
    "atum": (132, 28, 0, 1.3),
    "bacalhau": (105, 23, 0, 0.7),
    "pescada": (90, 17, 0, 1.7),
    "ovo": (155, 13, 1.1, 11),
    "ovos": (155, 13, 1.1, 11),
    "arroz": (130, 2.7, 28, 0.3),
    "arroz integral": (123, 2.6, 26, 1),
    "massa": (131, 5, 25, 1.1),
    "esparguete": (131, 5, 25, 1.1),
    "batata": (77, 2, 17, 0.1),
    "batata doce": (86, 1.6, 20, 0.1),
    "batata frita": (312, 3.4, 41, 15),
    "pao": (265, 9, 49, 3.2),
    "pão": (265, 9, 49, 3.2),
    "pao integral": (247, 13, 41, 4.2),
    "aveia": (389, 17, 66, 7),
    "feijao": (127, 9, 23, 0.5),
    "feijão": (127, 9, 23, 0.5),
    "grao": (164, 9, 27, 2.6),
    "grão": (164, 9, 27, 2.6),
    "lentilhas": (116, 9, 20, 0.4),
    "banana": (89, 1.1, 23, 0.3),
    "maca": (52, 0.3, 14, 0.2),
    "maçã": (52, 0.3, 14, 0.2),
    "iogurte": (61, 3.5, 4.7, 3.3),
    "iogurte grego": (97, 9, 4, 5),
    "iogurte natural": (61, 3.5, 4.7, 3.3),
    "leite": (42, 3.4, 5, 1),
    "queijo": (350, 25, 1.3, 27),
    "queijo fresco": (98, 11, 3.4, 4.3),
    "azeite": (884, 0, 0, 100),
    "manteiga": (717, 0.9, 0.1, 81),
    "brocolos": (34, 2.8, 7, 0.4),
    "brócolos": (34, 2.8, 7, 0.4),
    "espinafres": (23, 2.9, 3.6, 0.4),
    "cenoura": (41, 0.9, 10, 0.2),
    "tomate": (18, 0.9, 3.9, 0.2),
    "alface": (15, 1.4, 2.9, 0.2),
    "cebola": (40, 1.1, 9, 0.1),
    "legumes": (35, 2, 6, 0.3),
    "amendoas": (579, 21, 22, 50),
    "amêndoas": (579, 21, 22, 50),
    "nozes": (654, 15, 14, 65),
    "amendoim": (567, 26, 16, 49),
    "manteiga de amendoim": (588, 25, 20, 50),
    "whey protein": (400, 80, 8, 5),
    "proteina em po": (400, 80, 8, 5),
}

UNIT_G_DEFAULTS = {
    "ovo": 55,
    "ovos": 55,
    "banana": 120,
    "maca": 130,
    "maçã": 130,
    "fatia de pao": 30,
    "fatia de pão": 30,
    "iogurte": 125,
}


def lookup(food_name: str):
    key = food_name.strip().lower()
    if key in FOODS:
        return FOODS[key]
    # tenta correspondência parcial
    for name, vals in FOODS.items():
        if name in key or key in name:
            return vals
    return None
