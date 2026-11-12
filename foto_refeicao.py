"""Registar refeição por foto.

Como funciona:
1. O telemóvel envia a foto do prato (já reduzida no navegador, ~1280px).
2. A foto vai para o Gemini (IA da Google que "vê" imagens), com um pedido:
   "diz-me que alimentos estão no prato e quantas gramas de cada".
   Enviamos também a lista de nomes que a NutriApp já conhece, para a IA
   usar esses nomes sempre que possível (assim as contas batem certo).
3. A IA responde em JSON: [{nome, gramas, valores por 100 g}, ...].
4. As kcal/macros finais continuam a vir da tabela da app (food_data +
   alimentos criados por ti). Os valores da IA só são usados como
   proposta quando o alimento ainda não existe — e só se tu aceitares.

Configuração (variáveis de ambiente no Render):
* GEMINI_API_KEY  — obrigatória (https://aistudio.google.com/apikey)
* GEMINI_MODEL    — opcional (por omissão: gemini-2.5-flash)

Notas:
* No plano grátis do Gemini, a Google pode usar as fotos para melhorar os
  produtos dela. No plano pago, não.
* O gunicorn corta pedidos que demorem mais de 30 s, por isso o pedido ao
  Gemini tem um limite de 25 s.
"""
import base64
import json
import os

import requests

MODELO_PADRAO = "gemini-2.5-flash"
TIMEOUT_S = 25
MAX_BYTES = 6 * 1024 * 1024  # foto já vem reduzida; isto é só uma rede de segurança
TIPOS_ACEITES = {"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"}


class FotoErro(Exception):
    """Erro com mensagem pronta a mostrar à pessoa."""


def configurado():
    return bool(os.environ.get("GEMINI_API_KEY"))


_ESQUEMA = {
    "type": "OBJECT",
    "properties": {
        "e_comida": {"type": "BOOLEAN"},
        "aviso": {"type": "STRING"},
        "itens": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "nome": {"type": "STRING"},
                    "gramas": {"type": "NUMBER"},
                    "confianca": {"type": "STRING", "enum": ["alta", "media", "baixa"]},
                    "kcal_100g": {"type": "NUMBER"},
                    "proteina_100g": {"type": "NUMBER"},
                    "hidratos_100g": {"type": "NUMBER"},
                    "gordura_100g": {"type": "NUMBER"},
                },
                "required": ["nome", "gramas", "confianca", "kcal_100g",
                             "proteina_100g", "hidratos_100g", "gordura_100g"],
            },
        },
    },
    "required": ["e_comida", "itens"],
}


def _prompt(nomes_conhecidos):
    lista = ", ".join(sorted(set(nomes_conhecidos), key=str.lower))
    return f"""És um nutricionista português a analisar a foto de uma refeição.

Tarefa:
- Identifica cada alimento visível no prato (ou na mesa, se for claramente para comer agora).
- Estima as gramas da porção comestível, já cozinhada, como está no prato.
  Usa o prato, os talheres e o copo como escala (um prato raso tem ~26 cm).
- Se se virem gorduras ou molhos (brilho de azeite, manteiga, maionese, ketchup),
  junta-os como itens separados com uma estimativa prudente.
- Separa pratos misturados nos ingredientes principais quando for razoável
  (ex: "arroz de pato" → arroz + pato). Se não der para separar, usa o nome do prato.
- Para cada item, dá também valores nutricionais típicos por 100 g (tabela portuguesa/INSA).

Nomes:
- Escreve em português de Portugal, nomes curtos e comuns.
- Se o alimento corresponder a um destes nomes que a app já conhece, usa EXATAMENTE esse nome:
  {lista}

Se a foto não for de comida, responde com e_comida=false, itens vazios e um aviso curto.
Se tiveres dúvidas sobre um alimento, marca confianca="baixa" em vez de inventar."""


def _pedir_ao_gemini(foto_bytes, mime, nomes_conhecidos):
    chave = os.environ.get("GEMINI_API_KEY", "")
    modelo = os.environ.get("GEMINI_MODEL", MODELO_PADRAO).strip() or MODELO_PADRAO
    config = {
        "temperature": 0.2,
        "responseMimeType": "application/json",
        "responseSchema": _ESQUEMA,
    }
    if modelo.startswith("gemini-2.5"):
        # resposta mais rápida (sem "pensar" antes) — cabe no limite de 30 s do servidor
        config["thinkingConfig"] = {"thinkingBudget": 0}
    corpo = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": _prompt(nomes_conhecidos)},
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(foto_bytes).decode()}},
            ],
        }],
        "generationConfig": config,
    }
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
            headers={"x-goog-api-key": chave, "Content-Type": "application/json"},
            json=corpo, timeout=TIMEOUT_S,
        )
    except requests.Timeout:
        raise FotoErro("A análise demorou demasiado. Tenta outra vez.")
    except requests.RequestException:
        raise FotoErro("Não consegui ligar ao serviço de análise. Tenta outra vez.")

    if r.status_code == 429:
        raise FotoErro("Limite de análises atingido por agora. Tenta daqui a pouco.")
    if r.status_code in (400, 401, 403):
        print(f"[foto] Gemini {r.status_code}: {r.text[:300]}", flush=True)
        raise FotoErro("A chave do Gemini não foi aceite. Confirma GEMINI_API_KEY no Render.")
    if r.status_code >= 300:
        print(f"[foto] Gemini {r.status_code}: {r.text[:300]}", flush=True)
        raise FotoErro("O serviço de análise falhou. Tenta outra vez.")

    try:
        texto = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(texto)
    except (KeyError, IndexError, ValueError, TypeError):
        print(f"[foto] resposta inesperada: {r.text[:300]}", flush=True)
        raise FotoErro("Não consegui perceber a resposta da análise. Tenta outra foto.")


def _num(v, minimo=0.0, maximo=None):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return minimo
    v = max(minimo, v)
    return min(v, maximo) if maximo is not None else v


def analisar(foto_bytes, mime, nomes_conhecidos):
    """Devolve {"itens": [...], "aviso": str}. Lança FotoErro com mensagem amigável."""
    if not configurado():
        raise FotoErro("Falta configurar a chave do Gemini (GEMINI_API_KEY) no Render.")
    if not foto_bytes:
        raise FotoErro("Não recebi nenhuma foto.")
    if len(foto_bytes) > MAX_BYTES:
        raise FotoErro("A foto é demasiado grande. Tenta outra vez.")
    mime = (mime or "image/jpeg").lower()
    if mime not in TIPOS_ACEITES:
        raise FotoErro("Formato de imagem não suportado. Usa uma foto normal (JPG/PNG).")

    dados = _pedir_ao_gemini(foto_bytes, mime, nomes_conhecidos)
    if not dados.get("e_comida", True) or not dados.get("itens"):
        raise FotoErro(dados.get("aviso") or "Não encontrei comida nesta foto. Tenta outra, tirada de cima.")

    itens = []
    for it in dados["itens"][:12]:
        nome = " ".join(str(it.get("nome") or "").replace("|", "/").replace(";", ",").split())[:60]
        gramas = round(_num(it.get("gramas"), 0, 2000))
        if not nome or gramas <= 0:
            continue
        itens.append({
            "nome": nome,
            "gramas": gramas,
            "confianca": it.get("confianca") if it.get("confianca") in ("alta", "media", "baixa") else "media",
            "por100": {
                "kcal": round(_num(it.get("kcal_100g"), 0, 950), 1),
                "proteina_g": round(_num(it.get("proteina_100g"), 0, 100), 1),
                "hidratos_g": round(_num(it.get("hidratos_100g"), 0, 100), 1),
                "gordura_g": round(_num(it.get("gordura_100g"), 0, 100), 1),
            },
        })
    if not itens:
        raise FotoErro("Não consegui identificar alimentos nesta foto. Tenta outra, tirada de cima.")
    return {"itens": itens, "aviso": (dados.get("aviso") or "").strip()}
