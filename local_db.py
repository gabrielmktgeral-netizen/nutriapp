"""Backend de teste local — guarda tudo num ficheiro JSON (data/local_db.json).
Usa-se automaticamente quando não há NOTION_TOKEN configurado, para poderes
testar a app no PC sem ligar o Notion. Mesma 'interface' que notion_db.py."""
import json
import os
import uuid
from datetime import date, datetime

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "local_db.json")

_EMPTY = {"profile": None, "meals": [], "pantry": [], "weights": [], "exercises": [], "excluidos": [],
          "push_subscriptions": [], "custom_recipes": []}


def configured():
    return True  # o modo local está sempre "pronto a usar"


def _load():
    if not os.path.exists(DATA_FILE):
        return dict(_EMPTY)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k, v in _EMPTY.items():
        data.setdefault(k, v)
    return data


def _save(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- PERFIL ----------

def get_profile():
    data = _load()
    return data["profile"]


def save_profile(profile: dict):
    data = _load()
    current = data["profile"] or {}
    current.update(profile)
    current["page_id"] = "local-profile"
    data["profile"] = current
    _save(data)
    return current


# ---------- REFEIÇÕES ----------

def add_meal(data_iso, tipo, texto_original, kcal, proteina_g, hidratos_g, gordura_g):
    data = _load()
    meal = {
        "page_id": str(uuid.uuid4()), "data": data_iso, "tipo": tipo,
        "texto_original": texto_original,
        "kcal": round(kcal, 1), "proteina_g": round(proteina_g, 1),
        "hidratos_g": round(hidratos_g, 1), "gordura_g": round(gordura_g, 1),
    }
    data["meals"].append(meal)
    _save(data)
    return meal


def get_meals_between(start_iso, end_iso):
    data = _load()
    return [m for m in data["meals"] if start_iso <= m["data"] <= end_iso]


def get_meals_for_day(data_iso):
    return get_meals_between(data_iso, data_iso)


def get_meal(page_id):
    data = _load()
    for m in data["meals"]:
        if m["page_id"] == page_id:
            return m
    return None


def update_meal(page_id, texto_original, kcal, proteina_g, hidratos_g, gordura_g):
    data = _load()
    for m in data["meals"]:
        if m["page_id"] == page_id:
            m["texto_original"] = texto_original
            m["kcal"] = round(kcal, 1)
            m["proteina_g"] = round(proteina_g, 1)
            m["hidratos_g"] = round(hidratos_g, 1)
            m["gordura_g"] = round(gordura_g, 1)
            _save(data)
            return m
    return None


def delete_meal(page_id):
    data = _load()
    data["meals"] = [m for m in data["meals"] if m["page_id"] != page_id]
    _save(data)


# ---------- DESPENSA ----------

def get_pantry():
    return _load()["pantry"]


def add_pantry_item(nome, quantidade=""):
    data = _load()
    item = {"page_id": str(uuid.uuid4()), "nome": nome, "quantidade": quantidade}
    data["pantry"].append(item)
    _save(data)
    return item


def delete_pantry_item(page_id):
    data = _load()
    data["pantry"] = [p for p in data["pantry"] if p["page_id"] != page_id]
    _save(data)


# ---------- EXCLUÍDOS ----------

def get_excluidos():
    return _load()["excluidos"]


def add_excluido(nome):
    data = _load()
    item = {"page_id": str(uuid.uuid4()), "nome": nome}
    data["excluidos"].append(item)
    _save(data)
    return item


def delete_excluido(page_id):
    data = _load()
    data["excluidos"] = [e for e in data["excluidos"] if e["page_id"] != page_id]
    _save(data)


# ---------- PESO ----------

def add_weight(data_iso, peso_kg):
    data = _load()
    item = {"data": data_iso, "peso_kg": peso_kg}
    data["weights"].append(item)
    _save(data)
    return item


def get_weight_history(limit=12):
    data = _load()
    return sorted(data["weights"], key=lambda w: w["data"], reverse=True)[:limit]


# ---------- EXERCÍCIO ----------

def add_exercise(data_iso, nome, duracao_min=None, kcal_estimadas=None):
    data = _load()
    item = {
        "page_id": str(uuid.uuid4()), "data": data_iso, "nome": nome,
        "duracao_min": duracao_min, "kcal_estimadas": kcal_estimadas,
    }
    data["exercises"].append(item)
    _save(data)
    return item


def get_exercise_between(start_iso, end_iso):
    data = _load()
    return [e for e in data["exercises"] if start_iso <= e["data"] <= end_iso]


def start_exercise(nome):
    data = _load()
    item = {
        "page_id": str(uuid.uuid4()), "data": date.today().isoformat(), "nome": nome,
        "duracao_min": None, "kcal_estimadas": None,
        "inicio": datetime.now().isoformat(), "fim": None,
    }
    data["exercises"].append(item)
    _save(data)
    return item


def get_active_exercise():
    data = _load()
    for e in data["exercises"]:
        if e.get("inicio") and not e.get("fim"):
            return {"page_id": e["page_id"], "nome": e["nome"], "inicio": e["inicio"]}
    return None


def finish_exercise(page_id, kcal_estimadas=None):
    data = _load()
    for e in data["exercises"]:
        if e["page_id"] == page_id:
            agora = datetime.now()
            e["fim"] = agora.isoformat()
            if e.get("inicio"):
                try:
                    inicio_dt = datetime.fromisoformat(e["inicio"])
                    e["duracao_min"] = max(1, round((agora - inicio_dt).total_seconds() / 60))
                except (ValueError, TypeError):
                    pass
            if kcal_estimadas is not None:
                e["kcal_estimadas"] = kcal_estimadas
            _save(data)
            return e
    return None


# ---------- NOTIFICAÇÕES PUSH ----------

def get_push_subscriptions():
    data = _load()
    return data.setdefault("push_subscriptions", [])


def add_push_subscription(subscription_info: dict):
    data = _load()
    subs = data.setdefault("push_subscriptions", [])
    endpoint = subscription_info.get("endpoint", "")
    for s in subs:
        if s["endpoint"] == endpoint:
            return s
    item = {"page_id": str(uuid.uuid4()), "endpoint": endpoint, "keys": subscription_info.get("keys", {})}
    subs.append(item)
    _save(data)
    return item


def delete_push_subscription(endpoint):
    data = _load()
    subs = data.setdefault("push_subscriptions", [])
    data["push_subscriptions"] = [s for s in subs if s["endpoint"] != endpoint]
    _save(data)


# ---------- RECEITAS PERSONALIZADAS ----------

def get_custom_recipes():
    data = _load()
    return data.setdefault("custom_recipes", [])


def add_custom_recipe(nome, ingredientes, preparo, chave_despensa, kcal, proteina_g, hidratos_g, gordura_g):
    data = _load()
    recipes = data.setdefault("custom_recipes", [])
    item = {
        "page_id": str(uuid.uuid4()), "nome": nome,
        "ingredientes": list(ingredientes), "preparo": list(preparo),
        "chave_despensa": list(chave_despensa), "tags": [],
        "kcal": round(kcal, 1), "proteina_g": round(proteina_g, 1),
        "hidratos_g": round(hidratos_g, 1), "gordura_g": round(gordura_g, 1),
    }
    recipes.append(item)
    _save(data)
    return item


def delete_custom_recipe(page_id):
    data = _load()
    recipes = data.setdefault("custom_recipes", [])
    data["custom_recipes"] = [r for r in recipes if r["page_id"] != page_id]
    _save(data)


def get_custom_recipe(page_id):
    data = _load()
    for r in data.setdefault("custom_recipes", []):
        if r["page_id"] == page_id:
            return r
    return None


def update_custom_recipe(page_id, nome, ingredientes, preparo, chave_despensa, kcal, proteina_g, hidratos_g, gordura_g):
    data = _load()
    for r in data.setdefault("custom_recipes", []):
        if r["page_id"] == page_id:
            r.update({
                "nome": nome, "ingredientes": list(ingredientes), "preparo": list(preparo),
                "chave_despensa": list(chave_despensa),
                "kcal": round(kcal, 1), "proteina_g": round(proteina_g, 1),
                "hidratos_g": round(hidratos_g, 1), "gordura_g": round(gordura_g, 1),
            })
            _save(data)
            return r
    return None
