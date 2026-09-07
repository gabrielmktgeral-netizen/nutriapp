"""Receitas completas (ingredientes + preparo) para o assistente de sugestões.
Cada receita tem uma lista de ingredientes-chave (para cruzar com a despensa)
e os macros aproximados por dose."""

RECIPES = [
    {
        "nome": "Frango grelhado com arroz e brócolos",
        "tags": ["almoco", "jantar", "proteico"],
        "ingredientes": ["150g de peito de frango", "80g de arroz (cru)", "150g de brócolos", "1 colher de azeite", "sal, alho e limão a gosto"],
        "preparo": [
            "Tempera o frango com sal, alho e limão.",
            "Grelha o frango 5-6 min de cada lado até ficar bem cozinhado.",
            "Coze o arroz em água com sal, cerca de 15 min.",
            "Coze os brócolos no vapor 5-6 min.",
            "Serve tudo junto com um fio de azeite.",
        ],
        "kcal": 520, "proteina_g": 48, "hidratos_g": 55, "gordura_g": 12,
        "chave_despensa": ["frango", "arroz", "brocolos"],
    },
    {
        "nome": "Omelete de ovos com espinafres e queijo fresco",
        "tags": ["pequeno_almoco", "lanche", "rapido"],
        "ingredientes": ["3 ovos", "50g de espinafres", "30g de queijo fresco", "sal e pimenta"],
        "preparo": [
            "Bate os ovos com sal e pimenta.",
            "Salteia os espinafres numa frigideira 1-2 min.",
            "Junta os ovos batidos e o queijo fresco.",
            "Cozinha em lume brando até solidificar.",
        ],
        "kcal": 350, "proteina_g": 28, "hidratos_g": 4, "gordura_g": 24,
        "chave_despensa": ["ovos", "espinafres", "queijo fresco"],
    },
    {
        "nome": "Atum com batata doce e legumes",
        "tags": ["almoco", "jantar", "proteico"],
        "ingredientes": ["1 lata de atum (ao natural)", "200g de batata doce", "legumes a gosto", "1 colher de azeite"],
        "preparo": [
            "Coze a batata doce em cubos 15-20 min.",
            "Salteia os legumes com azeite.",
            "Escorre o atum e junta a tudo.",
            "Tempera a gosto.",
        ],
        "kcal": 420, "proteina_g": 35, "hidratos_g": 45, "gordura_g": 10,
        "chave_despensa": ["atum", "batata doce", "legumes"],
    },
    {
        "nome": "Iogurte grego com aveia, banana e amendoim",
        "tags": ["pequeno_almoco", "lanche", "rapido"],
        "ingredientes": ["150g de iogurte grego", "40g de aveia", "1 banana", "1 colher de manteiga de amendoim"],
        "preparo": [
            "Corta a banana às rodelas.",
            "Junta tudo numa taça: iogurte, aveia, banana.",
            "Termina com a colher de manteiga de amendoim por cima.",
        ],
        "kcal": 480, "proteina_g": 24, "hidratos_g": 60, "gordura_g": 16,
        "chave_despensa": ["iogurte grego", "aveia", "banana", "manteiga de amendoim"],
    },
    {
        "nome": "Massa integral com atum e tomate",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["80g de massa integral (crua)", "1 lata de atum", "molho de tomate", "azeite e orégãos"],
        "preparo": [
            "Coze a massa conforme indicado na embalagem.",
            "Aquece o molho de tomate com um fio de azeite.",
            "Junta o atum escorrido e os orégãos.",
            "Mistura com a massa escorrida.",
        ],
        "kcal": 500, "proteina_g": 32, "hidratos_g": 65, "gordura_g": 10,
        "chave_despensa": ["massa", "atum", "tomate"],
    },
    {
        "nome": "Feijoada de legumes com ovo",
        "tags": ["almoco", "jantar"],
        "ingredientes": ["150g de feijão cozido", "legumes a gosto (cenoura, cebola)", "1-2 ovos", "azeite, alho e louro"],
        "preparo": [
            "Refoga a cebola e o alho em azeite.",
            "Junta os legumes cortados e deixa amolecer.",
            "Adiciona o feijão cozido e um pouco de água, deixa apurar.",
            "Escalfa ou frita o ovo à parte e serve por cima.",
        ],
        "kcal": 400, "proteina_g": 22, "hidratos_g": 45, "gordura_g": 12,
        "chave_despensa": ["feijao", "cenoura", "cebola", "ovos"],
    },
    {
        "nome": "Batido proteico com banana e aveia",
        "tags": ["lanche", "pos_treino", "rapido"],
        "ingredientes": ["1 dose de whey protein", "1 banana", "30g de aveia", "200ml de leite"],
        "preparo": [
            "Junta tudo no liquidificador.",
            "Bate até ficar homogéneo.",
            "Serve fresco.",
        ],
        "kcal": 380, "proteina_g": 35, "hidratos_g": 45, "gordura_g": 6,
        "chave_despensa": ["whey protein", "banana", "aveia", "leite"],
    },
    {
        "nome": "Salada de frango com queijo e nozes",
        "tags": ["almoco", "jantar", "leve"],
        "ingredientes": ["150g de peito de frango", "alface e tomate a gosto", "30g de queijo", "20g de nozes", "azeite e limão"],
        "preparo": [
            "Grelha o frango e corta em tiras.",
            "Monta a base de alface e tomate.",
            "Junta o frango, o queijo e as nozes.",
            "Tempera com azeite e limão.",
        ],
        "kcal": 450, "proteina_g": 42, "hidratos_g": 12, "gordura_g": 26,
        "chave_despensa": ["frango", "alface", "tomate", "queijo", "nozes"],
    },
]


def sugerir_receitas(pantry_nomes, restante_kcal, restante_prot, top_n=3):
    """Pontua receitas por: quantos ingredientes já tens em casa + se cabem no que falta hoje."""
    pantry_lower = [p.lower() for p in pantry_nomes]

    scored = []
    for r in RECIPES:
        match_count = sum(1 for chave in r["chave_despensa"] if any(chave in p or p in chave for p in pantry_lower))
        cabe_kcal = r["kcal"] <= max(restante_kcal, 1) * 1.3  # alguma tolerância
        ajuda_proteina = r["proteina_g"] >= (restante_prot * 0.25 if restante_prot > 0 else 0)
        score = match_count * 2 + (1 if cabe_kcal else 0) + (1 if ajuda_proteina else 0)
        scored.append((score, match_count, r))

    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [{"receita": r, "match_count": mc} for score, mc, r in scored[:top_n]]
