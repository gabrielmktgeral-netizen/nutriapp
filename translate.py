"""Tradução automática (EN -> PT) das receitas vindas da API externa, usando a
MyMemory Translation API — gratuita, sem chave, sem conta.
https://mymemory.translated.net (limite ~5000 palavras/dia por IP, suficiente
para uso pessoal)."""
import requests

_CACHE = {}


def _mymemory(text: str, source="en", target="pt") -> str:
    text = (text or "").strip()
    if not text:
        return text
    key = (source, target, text)
    if key in _CACHE:
        return _CACHE[key]
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text[:490], "langpair": f"{source}|{target}"},
            timeout=6,
        )
        r.raise_for_status()
        data = r.json()
        traduzido = (data.get("responseData") or {}).get("translatedText") or text
    except requests.RequestException:
        traduzido = text
    _CACHE[key] = traduzido
    return traduzido


def translate_recipe(nome: str, ingredientes: list, preparo: list):
    """Traduz nome + ingredientes + preparo, tentando poupar chamadas (agrupando
    listas num só pedido quando cabe no limite de caracteres da API)."""
    nome_pt = _mymemory(nome)

    ing_joined = " • ".join(ingredientes)
    if ing_joined and len(ing_joined) <= 480:
        ing_pt_joined = _mymemory(ing_joined)
        if ing_pt_joined.count("•") == ing_joined.count("•"):
            ingredientes_pt = [s.strip(" •") for s in ing_pt_joined.split("•")]
        else:
            ingredientes_pt = [_mymemory(i) for i in ingredientes]
    else:
        ingredientes_pt = [_mymemory(i) for i in ingredientes]

    prep_joined = " ||| ".join(preparo)
    if prep_joined and len(prep_joined) <= 480:
        prep_pt_joined = _mymemory(prep_joined)
        if prep_pt_joined.count("|||") == prep_joined.count("|||"):
            preparo_pt = [s.strip(" |") for s in prep_pt_joined.split("|||")]
        else:
            preparo_pt = [_mymemory(p) for p in preparo]
    else:
        preparo_pt = [_mymemory(p) for p in preparo]

    return nome_pt, ingredientes_pt, preparo_pt
