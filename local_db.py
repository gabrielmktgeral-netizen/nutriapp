"""Backend de teste local — guarda tudo num ficheiro JSON (data/local_db.json).
Usa-se automaticamente quando não há NOTION_TOKEN configurado, para poderes
testar a app no PC sem ligar o Notion. Mesma 'interface' que notion_db.py."""
import json
import os
import uuid
from datetime import date

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "local_db.json")

_EMPTY = {"profile": None, "meals": [], "pantry": [], "weights": [], "exercises": []}


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
