"""Integração com a TheMealDB (API pública e gratuita de receitas).
https://www.themealdb.com/api.php — chave de teste '1', uso livre.

Isto é o que torna as sugestões verdadeiramente dinâmicas: em vez de uma
lista fixa escrita à mão, vai buscar receitas reais a uma base de dados
com milhares de opções, filtradas pelo que tens em casa."""
import requests

from translate import translate_recipe

BASE = "https://www.themealdb.com/api/json/v1/1"
TIMEOUT = 6

_DETAILS_CACHE = {}


def search_by_ingredient(ingredient_en: str):
    """Devolve lista de {id, nome, imagem} para um ingrediente em inglês."""
    try:
        r = requests.get(f"{BASE}/filter.php", params={"i": ingredient_en}, timeout=TIMEOUT)
        r.raise_for_status()
        meals = r.json().get("meals") or []
    except requests.RequestException:
        return []
    return [{"id": m["idMeal"], "nome": m["strMeal"], "imagem": m["strMealThumb"]} for m in meals]


def get_recipe_details(meal_id: str):
    """Devolve {nome, imagem, ingredientes: [...], preparo: [...], fonte_url} já em português.
    Guarda em cache (por processo) para não traduzir a mesma receita repetidamente."""
    if meal_id in _DETAILS_CACHE:
        return _DETAILS_CACHE[meal_id]

    try:
        r = requests.get(f"{BASE}/lookup.php", params={"i": meal_id}, timeout=TIMEOUT)
        r.raise_for_status()
        meals = r.json().get("meals") or []
    except requests.RequestException:
        return None
    if not meals:
        return None
    m = meals[0]

    ingredientes_en = []
    for i in range(1, 21):
        nome = (m.get(f"strIngredient{i}") or "").strip()
        medida = (m.get(f"strMeasure{i}") or "").strip()
        if nome:
            ingredientes_en.append(f"{medida} {nome}".strip())

    instrucoes = m.get("strInstructions") or ""
    passos_en = [p.strip() for p in instrucoes.replace("\r\n", "\n").split("\n") if p.strip()]
    if len(passos_en) <= 1:
        # algumas receitas vêm num único parágrafo — divide por frases
        passos_en = [p.strip() if p.strip().endswith(".") else p.strip() + "."
                     for p in instrucoes.split(". ") if p.strip()]

    ingredientes_texto = " ".join(ingredientes_en).lower()  # mantém em inglês, usado para filtrar excluídos

    nome_pt, ingredientes_pt, preparo_pt = translate_recipe(m.get("strMeal"), ingredientes_en, passos_en)

    detalhe = {
        "nome": nome_pt,
        "imagem": m.get("strMealThumb"),
        "ingredientes": ingredientes_pt,
        "preparo": preparo_pt,
        "fonte_url": f"https://www.themealdb.com/meal/{m.get('idMeal')}",
        "ingredientes_texto": ingredientes_texto,
    }
    _DETAILS_CACHE[meal_id] = detalhe
    return detalhe


def buscar_receitas_dinamicas(ingredientes_en, excluidos_en, limite=3):
    """Cruza vários ingredientes traduzidos, pega nos IDs mais frequentes,
    busca os detalhes e filtra os que têm algum ingrediente excluído."""
    contagem = {}
    nomes_por_id = {}
    for ing in ingredientes_en[:4]:  # limite de chamadas por pedido
        for m in search_by_ingredient(ing):
            contagem[m["id"]] = contagem.get(m["id"], 0) + 1
            nomes_por_id[m["id"]] = m

    if not contagem:
        # sem despensa reconhecida -> mostra receitas de uma categoria genérica proteica
        for m in search_by_ingredient("chicken_breast"):
            contagem[m["id"]] = 1
            nomes_por_id[m["id"]] = m

    ids_ordenados = sorted(contagem, key=lambda i: -contagem[i])

    resultados = []
    for meal_id in ids_ordenados:
        if len(resultados) >= limite:
            break
        detalhe = get_recipe_details(meal_id)
        if not detalhe:
            continue
        if any(exc in detalhe["ingredientes_texto"] for exc in excluidos_en if exc):
            continue
        resultados.append({"receita": detalhe, "match_count": contagem[meal_id]})

    return resultados
