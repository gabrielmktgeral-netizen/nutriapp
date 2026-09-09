"""Registo de refeições por lista de alimentos (em vez de texto livre).

A pessoa escreve o nome do alimento (com sugestões automáticas enquanto
escreve, via <datalist>), indica a quantidade e a unidade (gramas / dose /
unidade / lata). Se o alimento não existir na tabela local nem nos
alimentos que o próprio já criou, pode criá-lo (nome + macros por 100g) e
ele passa a ficar disponível para sempre.

Isto guarda-se num formato próprio (texto "canónico") no campo que antes
tinha o texto livre, para que ao editar a refeição seja possível voltar a
mostrar exatamente os alimentos e quantidades escolhidos.
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

# (chave usada em food_data.FOODS, nome para mostrar nas sugestões)
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
    ("peru", "Peru"),
    ("peru fatiado", "Peru fatiado (frios)"),
    ("fiambre", "Fiambre"),
    ("chouriço", "Chouriço"),
    ("presunto", "Presunto"),
    ("salsicha", "Salsicha"),
    ("costeleta de porco", "Costeleta de porco"),
    ("entrecosto", "Entrecosto"),
    ("camarão", "Camarão"),
    ("lulas", "Lulas"),
    ("polvo", "Polvo"),
    ("mexilhões", "Mexilhões"),
    ("sardinha", "Sardinha"),
    ("carapau", "Carapau"),
    ("dourada", "Dourada"),
    ("robalo", "Robalo"),
    ("truta", "Truta"),
    ("queijo mozzarella", "Queijo mozzarella"),
    ("queijo cheddar", "Queijo cheddar"),
    ("requeijão", "Requeijão"),
    ("kefir", "Kefir"),
    ("natas", "Natas"),
    ("pudim", "Pudim"),
    ("gelado", "Gelado"),
    ("chocolate preto", "Chocolate preto"),
    ("chocolate de leite", "Chocolate de leite"),
    ("mel", "Mel"),
    ("compota", "Compota"),
    ("cereais matinais", "Cereais matinais"),
    ("bolachas maria", "Bolachas Maria"),
    ("bolo simples", "Bolo simples"),
    ("croissant", "Croissant"),
    ("batata frita de pacote", "Batata frita de pacote"),
    ("pipocas", "Pipocas"),
    ("pizza", "Pizza"),
    ("hambúrguer", "Hambúrguer"),
    ("pinhões", "Pinhões"),
    ("castanhas", "Castanhas"),
    ("uva", "Uva"),
    ("morango", "Morango"),
    ("ananas", "Ananás"),
    ("melancia", "Melancia"),
    ("melão", "Melão"),
    ("pera", "Pera"),
    ("laranja", "Laranja"),
    ("kiwi", "Kiwi"),
    ("manga", "Manga"),
    ("abacate", "Abacate"),
    ("pepino", "Pepino"),
    ("courgette", "Courgette"),
    ("pimento", "Pimento"),
    ("couve", "Couve"),
    ("couve-flor", "Couve-flor"),
    ("cogumelos", "Cogumelos"),
    ("milho", "Milho"),
    ("ervilhas", "Ervilhas"),
    ("quinoa", "Quinoa"),
    ("vinho", "Vinho"),
    ("cerveja", "Cerveja"),
    ("refrigerante", "Refrigerante"),
    ("sumo de laranja", "Sumo de laranja"),
    ("água de coco", "Água de coco"),
    ("feijão miúdo", "Feijão miúdo"),
    ("feijão preto", "Feijão preto"),
    ("arroz com raspas de cenoura", "Arroz com raspas de cenoura"),
    ("arroz com ervilhas", "Arroz com ervilhas"),
    ("arroz com cenoura", "Arroz com cenoura"),
    ("pimentos", "Pimentos"),
    ("molho de tomate", "Molho de tomate"),
    ("rissóis", "Rissóis"),
    ("bolinhos de bacalhau", "Bolinhos de bacalhau"),
    ("hambúrguer de carne", "Hambúrguer (carne)"),
    ("bacon", "Bacon"),
    ("coca-cola", "Coca-Cola"),
    ("ice tea", "Ice Tea"),
]


def lista_completa(alimentos_custom):
    """Junta a lista fixa de alimentos com os personalizados do utilizador,
    para mostrar/editar tudo numa só página. Um alimento personalizado com o
    mesmo nome de um da lista fixa substitui os valores dele (uma 'edição')."""
    custom_by_name = {f["nome"].strip().lower(): f for f in (alimentos_custom or [])}
    vistos = set()
    linhas = []
    for chave, label in FOOD_CHOICES:
        vals = fd.FOODS.get(chave)
        if not vals:
            continue
        override = custom_by_name.get(label.strip().lower()) or custom_by_name.get(chave.strip().lower())
        if override:
            linhas.append({
                "nome": override["nome"], "kcal": override["kcal"], "proteina_g": override["proteina_g"],
                "hidratos_g": override["hidratos_g"], "gordura_g": override["gordura_g"],
                "page_id": override["page_id"], "personalizado": True,
            })
            vistos.add(override["nome"].strip().lower())
        else:
            kcal, prot, carb, fat = vals
            linhas.append({
                "nome": label, "kcal": kcal, "proteina_g": prot, "hidratos_g": carb, "gordura_g": fat,
                "page_id": None, "personalizado": False,
            })
    for f in (alimentos_custom or []):
        if f["nome"].strip().lower() not in vistos:
            linhas.append({
                "nome": f["nome"], "kcal": f["kcal"], "proteina_g": f["proteina_g"],
                "hidratos_g": f["hidratos_g"], "gordura_g": f["gordura_g"],
                "page_id": f["page_id"], "personalizado": True,
            })
    linhas.sort(key=lambda l: l["nome"].lower())
    return linhas


def opcoes_datalist(alimentos_custom):
    """Lista de nomes a mostrar como sugestões (fixos + os que o utilizador criou)."""
    fixos = [label for _key, label in FOOD_CHOICES]
    custom = [f["nome"] for f in (alimentos_custom or [])]
    return fixos + custom


def dict_custom(alimentos_custom):
    """{'nome em minúsculas': (kcal, proteina_g, hidratos_g, gordura_g)} para o food_data.lookup."""
    return {
        f["nome"].strip().lower(): (f["kcal"], f["proteina_g"], f["hidratos_g"], f["gordura_g"])
        for f in (alimentos_custom or [])
    }


def grams_for(texto, quantidade, unidade):
    if unidade == "g":
        return quantidade
    if unidade == "dose":
        return quantidade * fd.portion_grams(texto)
    if unidade == "unidade":
        return quantidade * fd.UNIT_G_DEFAULTS.get(texto.strip().lower(), 100)
    if unidade == "lata":
        return quantidade * fd.lata_grams(texto)
    return quantidade


def calcular_item(texto, quantidade, unidade, extra=None):
    vals = fd.lookup(texto, extra=extra)
    if vals is None or quantidade <= 0:
        return None
    gramas = grams_for(texto, quantidade, unidade)
    kcal100, prot100, carb100, fat100 = vals
    factor = gramas / 100.0
    return {
        "chave": texto,
        "nome": texto,
        "quantidade": quantidade,
        "unidade": unidade,
        "unidade_label": UNIT_LABELS.get(unidade, unidade),
        "gramas": round(gramas, 1),
        "kcal": round(kcal100 * factor, 1),
        "proteina_g": round(prot100 * factor, 1),
        "hidratos_g": round(carb100 * factor, 1),
        "gordura_g": round(fat100 * factor, 1),
    }


def calcular_itens(itens_form, extra=None):
    """itens_form: lista de dicts {chave, quantidade, unidade}.
    Devolve (total, itens_reconhecidos, nao_reconhecidos)."""
    total = {"kcal": 0.0, "proteina_g": 0.0, "hidratos_g": 0.0, "gordura_g": 0.0}
    itens = []
    nao_reconhecidos = []
    for it in itens_form:
        calc = calcular_item(it["chave"], it["quantidade"], it["unidade"], extra=extra)
        if calc:
            itens.append(calc)
            total["kcal"] += calc["kcal"]
            total["proteina_g"] += calc["proteina_g"]
            total["hidratos_g"] += calc["hidratos_g"]
            total["gordura_g"] += calc["gordura_g"]
        else:
            nao_reconhecidos.append(it["chave"])
    return total, itens, nao_reconhecidos


def itens_do_formulario(form):
    """Lê os campos repetidos chave[]/quantidade[]/unidade[] de um POST."""
    chaves = form.getlist("chave")
    quantidades = form.getlist("quantidade")
    unidades = form.getlist("unidade")
    itens = []
    for chave, qtd, unidade in zip(chaves, quantidades, unidades):
        chave = (chave or "").strip().replace("|", "/").replace(";", ",")
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


def resumo_itens(texto, extra=None):
    """Para mostrar 'quanto cada ingrediente pesa' numa refeição já guardada.
    Devolve a lista de itens com os macros de cada um, ou None se o texto
    não estiver no formato novo (refeição antiga em texto livre, receita, etc)."""
    itens_guardados = descodificar(texto)
    if itens_guardados is None:
        return None
    itens = []
    for it in itens_guardados:
        calc = calcular_item(it["chave"], it["quantidade"], it["unidade"], extra=extra)
        if calc:
            itens.append(calc)
    return itens or None


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
