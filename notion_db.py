"""Camada de acesso à base de dados Notion (usada como 'BD' da app)."""
import os
import requests

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_VERSION = "2025-09-03"
BASE_URL = "https://api.notion.com/v1"

# IDs dos data sources criados no workspace do utilizador
DS_PERFIL = "3f001973-d562-4d0f-861f-171df57a8e6b"
DS_REFEICOES = "02e052d2-9ff1-4f7e-a5ad-28dc7d5d0233"
DS_DESPENSA = "257fb7a6-e34a-49b2-8a3b-ec21aec0ff05"
DS_PESO = "8952c054-bfb7-4f3f-8920-0876a84e82b1"
DS_EXERCICIO = "818ab87d-0b92-46fb-ab11-e60b522b514d"


def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def configured():
    return bool(NOTION_TOKEN)


def _query(data_source_id, filter_=None, sorts=None):
    url = f"{BASE_URL}/data_sources/{data_source_id}/query"
    body = {}
    if filter_:
        body["filter"] = filter_
    if sorts:
        body["sorts"] = sorts
    r = requests.post(url, headers=_headers(), json=body, timeout=15)
    r.raise_for_status()
    return r.json().get("results", [])


def _create_page(data_source_id, properties):
    url = f"{BASE_URL}/pages"
    body = {"parent": {"data_source_id": data_source_id}, "properties": properties}
    r = requests.post(url, headers=_headers(), json=body, timeout=15)
    r.raise_for_status()
    return r.json()


def _update_page(page_id, properties):
    url = f"{BASE_URL}/pages/{page_id}"
    r = requests.patch(url, headers=_headers(), json={"properties": properties}, timeout=15)
    r.raise_for_status()
    return r.json()


def _delete_page(page_id):
    url = f"{BASE_URL}/pages/{page_id}"
    r = requests.patch(url, headers=_headers(), json={"archived": True}, timeout=15)
    r.raise_for_status()
    return r.json()


def _prop(page, name, kind):
    p = page["properties"].get(name)
    if not p:
        return None
    if kind == "title":
        arr = p.get("title", [])
        return arr[0]["plain_text"] if arr else ""
    if kind == "number":
        return p.get("number")
    if kind == "select":
        s = p.get("select")
        return s["name"] if s else None
    if kind == "text":
        arr = p.get("rich_text", [])
        return arr[0]["plain_text"] if arr else ""
    if kind == "date":
        d = p.get("date")
        return d["start"] if d else None
    return None


# ---------- PERFIL ----------

def get_profile():
    results = _query(DS_PERFIL)
    if not results:
        return None
    page = results[0]
    return {
        "page_id": page["id"],
        "idade": _prop(page, "Idade", "number"),
        "sexo": _prop(page, "Sexo", "select"),
        "altura_cm": _prop(page, "Altura cm", "number"),
        "peso_kg": _prop(page, "Peso kg", "number"),
        "nivel_atividade": _prop(page, "Nivel Atividade", "select") or "moderado",
        "objetivo": _prop(page, "Objetivo", "select") or "manter_peso",
        "peso_pretendido": _prop(page, "Peso Pretendido", "number"),
        "hora_pequeno_almoco": _prop(page, "Hora Pequeno Almoco", "text") or "08:00",
        "hora_almoco": _prop(page, "Hora Almoco", "text") or "13:00",
        "hora_lanche": _prop(page, "Hora Lanche", "text") or "17:00",
        "hora_jantar": _prop(page, "Hora Jantar", "text") or "20:00",
        "hora_treino": _prop(page, "Hora Treino", "text") or "",
    }


def save_profile(data: dict):
    properties = {
        "Nome": {"title": [{"text": {"content": "Perfil do utilizador"}}]},
        "Idade": {"number": data.get("idade")},
        "Sexo": {"select": {"name": data.get("sexo")}} if data.get("sexo") else None,
        "Altura cm": {"number": data.get("altura_cm")},
        "Peso kg": {"number": data.get("peso_kg")},
        "Nivel Atividade": {"select": {"name": data.get("nivel_atividade")}} if data.get("nivel_atividade") else None,
        "Objetivo": {"select": {"name": data.get("objetivo")}} if data.get("objetivo") else None,
        "Peso Pretendido": {"number": data.get("peso_pretendido")},
        "Hora Pequeno Almoco": {"rich_text": [{"text": {"content": data.get("hora_pequeno_almoco", "")}}]},
        "Hora Almoco": {"rich_text": [{"text": {"content": data.get("hora_almoco", "")}}]},
        "Hora Lanche": {"rich_text": [{"text": {"content": data.get("hora_lanche", "")}}]},
        "Hora Jantar": {"rich_text": [{"text": {"content": data.get("hora_jantar", "")}}]},
        "Hora Treino": {"rich_text": [{"text": {"content": data.get("hora_treino", "")}}]},
    }
    properties = {k: v for k, v in properties.items() if v is not None}

    existing = get_profile()
    if existing:
        return _update_page(existing["page_id"], properties)
    return _create_page(DS_PERFIL, properties)


# ---------- REFEIÇÕES ----------

def add_meal(data_iso, tipo, texto_original, kcal, proteina_g, hidratos_g, gordura_g):
    label = {"pequeno_almoco": "Pequeno-almoço", "almoco": "Almoço", "lanche": "Lanche", "jantar": "Jantar"}.get(tipo, tipo)
    properties = {
        "Nome": {"title": [{"text": {"content": f"{label} - {data_iso}"}}]},
        "Data": {"date": {"start": data_iso}},
        "Tipo": {"select": {"name": tipo}},
        "Texto Original": {"rich_text": [{"text": {"content": texto_original[:1900]}}]},
        "Kcal": {"number": round(kcal, 1)},
        "Proteina g": {"number": round(proteina_g, 1)},
        "Hidratos g": {"number": round(hidratos_g, 1)},
        "Gordura g": {"number": round(gordura_g, 1)},
    }
    return _create_page(DS_REFEICOES, properties)


def get_meals_between(start_iso, end_iso):
    filter_ = {"and": [
        {"property": "Data", "date": {"on_or_after": start_iso}},
        {"property": "Data", "date": {"on_or_before": end_iso}},
    ]}
    results = _query(DS_REFEICOES, filter_=filter_, sorts=[{"property": "Data", "direction": "ascending"}])
    meals = []
    for page in results:
        meals.append({
            "page_id": page["id"],
            "data": _prop(page, "Data", "date"),
            "tipo": _prop(page, "Tipo", "select"),
            "texto_original": _prop(page, "Texto Original", "text"),
            "kcal": _prop(page, "Kcal", "number") or 0,
            "proteina_g": _prop(page, "Proteina g", "number") or 0,
            "hidratos_g": _prop(page, "Hidratos g", "number") or 0,
            "gordura_g": _prop(page, "Gordura g", "number") or 0,
        })
    return meals


def get_meals_for_day(data_iso):
    return get_meals_between(data_iso, data_iso)


# ---------- DESPENSA ----------

def get_pantry():
    results = _query(DS_DESPENSA)
    return [{
        "page_id": p["id"],
        "nome": _prop(p, "Nome", "title"),
        "quantidade": _prop(p, "Quantidade", "text"),
    } for p in results]


def add_pantry_item(nome, quantidade=""):
    properties = {
        "Nome": {"title": [{"text": {"content": nome}}]},
        "Quantidade": {"rich_text": [{"text": {"content": quantidade}}]},
    }
    return _create_page(DS_DESPENSA, properties)


def delete_pantry_item(page_id):
    return _delete_page(page_id)


# ---------- PESO ----------

def add_weight(data_iso, peso_kg):
    properties = {
        "Nome": {"title": [{"text": {"content": f"Peso {data_iso}"}}]},
        "Data": {"date": {"start": data_iso}},
        "Peso kg": {"number": peso_kg},
    }
    return _create_page(DS_PESO, properties)


def get_weight_history(limit=12):
    results = _query(DS_PESO, sorts=[{"property": "Data", "direction": "descending"}])
    out = [{"data": _prop(p, "Data", "date"), "peso_kg": _prop(p, "Peso kg", "number")} for p in results]
    return out[:limit]


# ---------- EXERCÍCIO ----------

def add_exercise(data_iso, nome, duracao_min=None, kcal_estimadas=None):
    properties = {
        "Nome": {"title": [{"text": {"content": nome}}]},
        "Data": {"date": {"start": data_iso}},
        "Duracao min": {"number": duracao_min},
        "Kcal Estimadas": {"number": kcal_estimadas},
    }
    properties = {k: v for k, v in properties.items() if v is not None}
    return _create_page(DS_EXERCICIO, properties)


def get_exercise_between(start_iso, end_iso):
    filter_ = {"and": [
        {"property": "Data", "date": {"on_or_after": start_iso}},
        {"property": "Data", "date": {"on_or_before": end_iso}},
    ]}
    results = _query(DS_EXERCICIO, filter_=filter_)
    return [{
        "page_id": p["id"],
        "data": _prop(p, "Data", "date"),
        "nome": _prop(p, "Nome", "title"),
        "duracao_min": _prop(p, "Duracao min", "number"),
        "kcal_estimadas": _prop(p, "Kcal Estimadas", "number"),
    } for p in results]
