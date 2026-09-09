"""Registo de refeições por lista de alimentos (em vez de texto livre).

A pessoa escolhe o alimento numa lista, indica a quantidade e a unidade
(gramas / dose / unidade / lata) — sem ter de escrever frases que um parser
de texto tenha de adivinhar. Isto guarda-se num formato próprio (texto
"canónico") no campo que antes tinha o texto livre, para que ao editar a
refeição seja possível voltar a mostrar exatamente os alimentos e
quantidades escolhidos.
"""
import food_data as fd

UNIT_LABELS = {
    "dose": "dose / porção normal",
    "g": "gramas (g)",
    "unidade": "unidade (ex: 1 ovo)",
    "lata": "lata",
}
# ordem em que aparecem no menu de unidades
UNIT_ORDER = ["dose", "g", "unidade", "lata"]

# (chave usada em food_data.FOODS, nome para mostrar na lista)
FOOD_CHOICES = [
    ("frango grelhado", "Frango grelhado"),
    ("peito de frango", "Peito de frango (cru)"),
    ("carne de vaca", "Carne de vaca"),
    ("bife", "Bife"),
    ("porco", "Carne de porco"),
    ("lombo de porco", "Lombo de porco"),
    ("peixe", "Peixe (genérico)"),
    ("salmão", "Salmão"),
    ("atum", "Atum"),
    ("bacalhau", "Bacalhau"),
    ("pescada", "Pescada"),
    ("ovo", "Ovo"),
    ("arroz", "Arroz branco"),
    ("arroz integral", "Arroz integral"),
    ("massa", "Massa / esparguete"),
    ("batata", "Batata"),
    ("batata doce", "Batata doce"),
    ("batata frita", "Batata frita"),
    ("pão", "Pão"),
    ("pao integral", "Pão integral"),
    ("aveia", "Aveia"),
    ("feijão", "Feijão"),
    ("grão", "Grão-de-bico"),
    ("lentilhas", "Lentilhas"),
    ("banana", "Banana"),
    ("maçã", "Maçã"),
    ("iogurte", "Iogurte natural"),
    ("iogurte grego", "Iogurte grego"),
    ("leite", "Leite"),
    ("queijo", "Queijo"),
    ("queijo fresco", "Queijo fresco"),
    ("azeite", "Azeite"),
    ("manteiga", "Manteiga"),
    ("brócolos", "Brócolos"),
    ("espinafres", "Espinafres"),
    ("cenoura", "Cenoura"),
    ("tomate", "Tomate"),
    ("alface", "Alface"),
    ("cebola", "Cebola"),
    ("legumes", "Legumes (genérico)"),
    ("amêndoas", "Amêndoas"),
    ("nozes", "Nozes"),
    ("amendoim", "Amendoim"),
    ("manteiga de amendoim", "Manteiga de amendoim"),
    ("whey protein", "Whey protein (pó)"),
]
FOOD_LABELS = dict(FOOD_CHOICES)


def grams_for(chave, quantidade, unidade):
    if unidade == "g":
        return quantidade
    if unidade == "dose":
        return quantidade * fd.portion_grams(chave)
    if unidade == "unidade":
        return quantidade * fd.UNIT_G_DEFAULTS.get(chave, 100)
    if unidade == "lata":
        return quantidade * fd.lata_grams(chave)
    return quantidade


def calcular_item(chave, quantidade, unidade):
    vals = fd.lookup(chave)
    if vals is None or quantidade <= 0:
        return None
    gramas = grams_for(chave, quantidade, unidade)
    kcal100, prot100, carb100, fat100 = vals
    factor = gramas / 100.0
    return {
        "chave": chave,
        "nome": FOOD_LABELS.get(chave, chave.capitalize()),
        "quantidade": quantidade,
        "unidade": unidade,
        "unidade_label": UNIT_LABELS.get(unidade, unidade),
        "gramas": round(gramas, 1),
        "kcal": round(kcal100 * factor, 1),
        "proteina_g": round(prot100 * factor, 1),
        "hidratos_g": round(carb100 * factor, 1),
        "gordura_g": round(fat100 * factor, 1),
    }


def calcular_itens(itens_form):
    """itens_form: lista de dicts {chave, quantidade, unidade}."""
    total = {"kcal": 0.0, "proteina_g": 0.0, "hidratos_g": 0.0, "gordura_g": 0.0}
    itens = []
    for it in itens_form:
        calc = calcular_item(it["chave"], it["quantidade"], it["unidade"])
        if calc:
            itens.append(calc)
            total["kcal"] += calc["kcal"]
            total["proteina_g"] += calc["proteina_g"]
            total["hidratos_g"] += calc["hidratos_g"]
            total["gordura_g"] += calc["gordura_g"]
    return total, itens


def itens_do_formulario(form):
    """Lê os campos repetidos chave[]/quantidade[]/unidade[] de um POST."""
    chaves = form.getlist("chave")
    quantidades = form.getlist("quantidade")
    unidades = form.getlist("unidade")
    itens = []
    for chave, qtd, unidade in zip(chaves, quantidades, unidades):
        chave = (chave or "").strip()
        if not chave:
            continue
        try:
            qtd_val = float((qtd or "0").replace(",", "."))
        except ValueError:
            qtd_val = 0
        if qtd_val <= 0:
            continue
        itens.append({"chave": chave, "quantidade": qtd_val, "unidade": unidade or "g"})
    return itens


def codificar(itens):
    """Lista de {chave, quantidade, unidade} -> texto para guardar na base de dados."""
    return ";".join(f"{it['chave']}|{it['quantidade']}|{it['unidade']}" for it in itens)


def descodificar(texto):
    """Lê o texto guardado de volta para uma lista de itens. Devolve None se
    o texto não estiver neste formato (ex: refeições antigas em texto livre,
    'Não comi nada', ou uma receita registada pelo nome)."""
    if not texto or "|" not in texto:
        return None
    itens = []
    try:
        for parte in texto.split(";"):
            parte = parte.strip()
            if not parte:
                continue
            chave, qtd, unidade = parte.split("|")
            itens.append({"chave": chave, "quantidade": float(qtd), "unidade": unidade})
    except ValueError:
        return None
    return itens or None
