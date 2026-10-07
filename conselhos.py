"""Conselhos automáticos a partir dos registos do utilizador.

Tudo aqui são funções puras (não falam com a base de dados), por isso é fácil
testar. O app.py trata de ir buscar as refeições e o histórico de peso e passa
os dados para `gerar_conselhos`.

Cada conselho é um dict:
    {"tipo": "macros|padrao|peso|info", "nivel": "ok|aviso|info",
     "icone": "🥩", "titulo": "...", "texto": "...", "sugestoes": [..opcional..]}
"""
import re
import unicodedata
from datetime import date, timedelta

import meal_items as mi

TIPOS_REFEICAO = ("pequeno_almoco", "almoco", "lanche", "jantar")

# Palavras (sem acentos, minúsculas) que indicam doces / bebidas açucaradas.
PALAVRAS_DOCES = (
    "chocolate", "bolo", "bolacha", "bolachas", "gelado", "oreo", "pudim", "compota",
    "mel", "croissant", "refrigerante", "coca", "ice tea", "sumo", "doce", "docinho",
    "donut", "pastel", "nutella", "caramelo", "gomas", "bomboca", "sobremesa",
    "brigadeiro", "waffle", "panqueca", "cereais matinais", "leite chocolate",
    "leite com chocolate", "acucar", "biscoito", "barra de cereais", "muffin", "tarte",
)

# Alimentos que são boa fonte de fibra (frutas, legumes, leguminosas, integrais...).
PALAVRAS_FIBRA = (
    "aveia", "integral", "feijao", "grao", "lentilha", "ervilha", "quinoa", "milho",
    "brocolo", "espinafre", "couve", "cenoura", "tomate", "alface", "pepino", "pimento",
    "courgette", "cogumelo", "legume", "salada", "abacate", "maca", "pera", "banana",
    "laranja", "kiwi", "morango", "uva", "manga", "ananas", "melao", "melancia",
    "fruta", "amendoa", "amendoim", "noz", "nozes", "pinhoes", "castanha", "batata doce",
    "sopa", "vegetais", "cebola",
)


# ---------------------------------------------------------------- utilitários

def _norm(texto):
    texto = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in texto if not unicodedata.combining(c))


def _texto_refeicao(meal):
    """Texto normalizado com os alimentos de uma refeição (funciona tanto para
    refeições novas, codificadas, como para texto livre antigo)."""
    original = meal.get("texto_original") or ""
    itens = mi.descodificar(original)
    if itens:
        return " ; ".join(_norm(it["chave"]) for it in itens)
    return _norm(original)


def _contem(texto, palavras):
    """True se alguma das palavras aparece como palavra inteira (com 's' final
    opcional). Evita falsos positivos como 'mel' em 'melão' ou 'bolo' em 'bolonhesa'."""
    return any(re.search(r"\b" + re.escape(p) + r"s?\b", texto) for p in palavras)


def _contem_doces(texto):
    # 'batata doce' é um legume, não um doce
    return _contem(texto.replace("batata doce", "batatadoce"), PALAVRAS_DOCES)


def _fmt(n):
    return f"{round(n)}"


def _pt_num(n, casas=1):
    return f"{n:.{casas}f}".replace(".", ",")


def _agrupar_por_dia(meals):
    dias = {}
    for m in meals:
        dias.setdefault(m["data"], []).append(m)
    return dias


def _conselho(tipo, nivel, icone, titulo, texto, sugestoes=None):
    c = {"tipo": tipo, "nivel": nivel, "icone": icone, "titulo": titulo, "texto": texto}
    if sugestoes:
        c["sugestoes"] = sugestoes
    return c


# ------------------------------------------------------------- 1) Macros (3 dias)

def analisar_macros(targets, meals, hoje, dias=3, receitas=None, excluidos_nomes=None):
    """Compara a média diária (últimos `dias` dias) com os objetivos de kcal,
    proteína, hidratos e gordura. Só conta dias em que registaste alguma coisa,
    para não penalizar quem ainda não registou nada."""
    if not targets:
        return []
    inicio = (hoje - timedelta(days=dias - 1)).isoformat()
    recentes = [m for m in meals if inicio <= m["data"] <= hoje.isoformat()]
    por_dia = _agrupar_por_dia(recentes)
    # o dia de hoje pode estar incompleto — só conta se já tiver 3+ refeições
    por_dia = {d: ms for d, ms in por_dia.items() if d != hoje.isoformat() or len(ms) >= 3}
    n = len(por_dia)
    if n < 2:
        return []

    def media(campo):
        return sum(m[campo] for ms in por_dia.values() for m in ms) / n

    kcal, prot = media("kcal"), media("proteina_g")
    hidr, gord = media("hidratos_g"), media("gordura_g")
    conselhos = []

    # --- Proteína
    alvo_p = targets.get("protein_g") or 0
    if alvo_p:
        if prot < alvo_p * 0.85:
            excl = set(excluidos_nomes or [])
            cands = sorted((r for r in (receitas or []) if r["nome"] not in excl),
                           key=lambda r: -r["proteina_g"])[:4]
            conselhos.append(_conselho(
                "macros", "aviso", "🥩", "Proteína abaixo do objetivo",
                f"Nos últimos {n} dias com registos comeste em média {_fmt(prot)} g de proteína "
                f"por dia (objetivo: {_fmt(alvo_p)} g). Tenta pôr uma fonte de proteína em cada refeição: "
                f"ovos, iogurte grego, peixe, frango ou leguminosas.",
                [r["nome"] for r in cands]))
        elif prot >= alvo_p * 1.0:
            conselhos.append(_conselho(
                "macros", "ok", "💪", "Proteína em dia",
                f"Média de {_fmt(prot)} g por dia — objetivo de {_fmt(alvo_p)} g cumprido. Continua assim."))

    # --- Hidratos
    alvo_h = targets.get("carbs_g") or 0
    if alvo_h:
        if hidr > alvo_h * 1.20:
            conselhos.append(_conselho(
                "macros", "aviso", "🍞", "Hidratos acima do objetivo",
                f"Média de {_fmt(hidr)} g por dia (objetivo: {_fmt(alvo_h)} g). Troca pão branco, massa "
                f"e doces por versões integrais, legumes ou fruta inteira, e cuida das porções de arroz e batata."))
        elif hidr < alvo_h * 0.60:
            conselhos.append(_conselho(
                "macros", "info", "🍚", "Poucos hidratos",
                f"Média de {_fmt(hidr)} g por dia (objetivo: {_fmt(alvo_h)} g). Se treinas, pode faltar-te "
                f"energia — junta aveia, arroz, batata-doce ou fruta, sobretudo antes do treino."))

    # --- Gordura
    alvo_g = targets.get("fat_g") or 0
    if alvo_g:
        if gord > alvo_g * 1.25:
            conselhos.append(_conselho(
                "macros", "aviso", "🧈", "Gordura acima do objetivo",
                f"Média de {_fmt(gord)} g por dia (objetivo: {_fmt(alvo_g)} g). Reduz fritos, molhos, "
                f"charcutaria e queijos gordos; prefere grelhados e usa o azeite com medida."))
        elif gord < alvo_g * 0.55:
            conselhos.append(_conselho(
                "macros", "info", "🥑", "Pouca gordura",
                f"Média de {_fmt(gord)} g por dia (objetivo: {_fmt(alvo_g)} g). Gorduras boas ajudam "
                f"as hormonas e a saciedade: azeite, abacate, frutos secos, peixe gordo."))

    # --- Calorias
    alvo_k = targets.get("kcal") or 0
    if alvo_k:
        if kcal > alvo_k * 1.15:
            conselhos.append(_conselho(
                "macros", "aviso", "🔥", "Calorias acima do objetivo",
                f"Média de {_fmt(kcal)} kcal por dia (objetivo: {_fmt(alvo_k)} kcal). "
                f"Diferença de cerca de {_fmt(kcal - alvo_k)} kcal por dia."))
        elif kcal < alvo_k * 0.75:
            conselhos.append(_conselho(
                "macros", "aviso", "⚠️", "Estás a comer pouco",
                f"Média de {_fmt(kcal)} kcal por dia (objetivo: {_fmt(alvo_k)} kcal). Comer muito abaixo "
                f"do objetivo gera cansaço e perda de massa muscular. Não saltes refeições."))
    return conselhos


# ------------------------------------------------- 2) Padrões (últimos 7 dias)

def analisar_padroes(meals, hoje, dias=7):
    """Procura hábitos repetidos: pequeno-almoço saltado, muitos doces,
    pouca fibra. Só avalia dias completos com registos (hoje fica de fora)."""
    inicio = (hoje - timedelta(days=dias)).isoformat()
    ontem = (hoje - timedelta(days=1)).isoformat()
    janela = [m for m in meals if inicio <= m["data"] <= ontem]
    por_dia = _agrupar_por_dia(janela)
    n = len(por_dia)
    if n < 3:
        return []

    conselhos = []

    # --- Pequeno-almoço saltado
    saltou = 0
    for ms in por_dia.values():
        pa = [m for m in ms if m["tipo"] == "pequeno_almoco" and m.get("texto_original") != "Não comi nada"]
        if not pa:
            saltou += 1
    if saltou >= 3 and saltou / n >= 0.5:
        conselhos.append(_conselho(
            "padrao", "aviso", "🌅", "Estás a saltar o pequeno-almoço",
            f"Em {saltou} de {n} dias não registaste pequeno-almoço. Quem salta a primeira refeição tende a "
            f"ter mais fome e a comer mais ao fim do dia. Experimenta algo simples e rápido: "
            f"iogurte com aveia e fruta, ovos ou pão integral com queijo fresco."))

    # --- Doces e bebidas açucaradas
    ocorrencias, dias_com_doces = 0, set()
    for dia, ms in por_dia.items():
        for m in ms:
            if m.get("texto_original") == "Não comi nada":
                continue
            if _contem_doces(_texto_refeicao(m)):
                ocorrencias += 1
                dias_com_doces.add(dia)
    if ocorrencias >= 4 or len(dias_com_doces) >= 4:
        conselhos.append(_conselho(
            "padrao", "aviso", "🍫", "Muitos doces e açúcar",
            f"Registaste doces ou bebidas açucaradas {ocorrencias} vezes em {len(dias_com_doces)} dos últimos {n} dias. "
            f"O açúcar acrescenta calorias que não saciam. Tenta guardar os doces para 1 ou 2 vezes por semana "
            f"e troca por fruta, iogurte natural ou chocolate preto."))

    # --- Fibra (só se a maioria das refeições estiver registada por alimentos;
    # em texto livre antigo não conseguimos saber o que lá está)
    todas = [m for ms in por_dia.values() for m in ms if m.get("texto_original") != "Não comi nada"]
    estruturadas = sum(1 for m in todas if mi.descodificar(m.get("texto_original")))
    avaliar_fibra = bool(todas) and estruturadas / len(todas) >= 0.5

    dias_sem_fibra = 0
    for ms in por_dia.values():
        texto_dia = " ; ".join(_texto_refeicao(m) for m in ms if m.get("texto_original") != "Não comi nada")
        if not _contem(texto_dia, PALAVRAS_FIBRA):
            dias_sem_fibra += 1
    if avaliar_fibra and dias_sem_fibra >= 3 and dias_sem_fibra / n >= 0.5:
        conselhos.append(_conselho(
            "padrao", "aviso", "🥦", "Pouca fibra",
            f"Em {dias_sem_fibra} de {n} dias não registaste fruta, legumes, leguminosas nem cereais integrais. "
            f"A fibra (25 g por dia, aproximadamente) ajuda na digestão e na saciedade. "
            f"Põe legumes ao almoço e ao jantar, uma peça de fruta no lanche e troca o pão branco por integral."))

    return conselhos


# ------------------------------------------------------------- 3) Peso

OBJETIVOS_PERDER = ("perder_peso", "perder_gordura")
OBJETIVOS_GANHAR = ("ganhar_massa", "aumentar_peso")
OBJETIVOS_MANTER = ("manter_peso", "melhorar_condicao", "recomposicao")


def analisar_peso(profile, pesos, hoje, janela_dias=28):
    """`pesos`: lista de {data, peso_kg} (qualquer ordem). Compara a tendência
    com o objetivo do utilizador."""
    if not profile:
        return []
    objetivo = profile.get("objetivo")
    pesos = [{"data": str(p["data"])[:10], "peso_kg": float(p["peso_kg"])}
             for p in (pesos or []) if p.get("data") and p.get("peso_kg")]
    pesos.sort(key=lambda p: p["data"])

    # pouca informação -> pede para registar o peso
    if not pesos:
        return [_conselho(
            "peso", "info", "⚖️", "Regista o teu peso",
            "Ainda não tenho histórico de peso. Atualiza o peso no Perfil uma vez por semana "
            "(sempre ao mesmo dia e hora) e passo a avisar-te se estás a ir na direção certa.")]

    ultimo = pesos[-1]
    dias_desde_ultimo = (hoje - date.fromisoformat(ultimo["data"])).days

    limite = (hoje - timedelta(days=janela_dias)).isoformat()
    recentes = [p for p in pesos if p["data"] >= limite]
    if len(recentes) < 2 or (date.fromisoformat(recentes[-1]["data"]) - date.fromisoformat(recentes[0]["data"])).days < 6:
        texto = ("Só tenho um registo de peso recente. Atualiza o peso no Perfil daqui a uns dias "
                 "para eu perceber a tendência.")
        if dias_desde_ultimo > 10:
            texto = (f"O último peso registado foi há {dias_desde_ultimo} dias. "
                     "Atualiza no Perfil para eu acompanhar a tua evolução.")
        return [_conselho("peso", "info", "⚖️", "Atualiza o teu peso", texto)]

    primeiro = recentes[0]
    dias_span = (date.fromisoformat(ultimo["data"]) - date.fromisoformat(primeiro["data"])).days
    delta = ultimo["peso_kg"] - primeiro["peso_kg"]
    por_semana = delta / dias_span * 7
    sinal = "+" if delta > 0 else ""
    resumo = (f"{_pt_num(primeiro['peso_kg'])} kg → {_pt_num(ultimo['peso_kg'])} kg "
              f"({sinal}{_pt_num(delta)} kg em {dias_span} dias)")

    alvo = profile.get("peso_pretendido")
    falta = None
    if alvo:
        falta = ultimo["peso_kg"] - alvo  # >0 = ainda tens de perder

    # --- Perder peso
    if objetivo in OBJETIVOS_PERDER:
        if por_semana < -1.0:
            return [_conselho("peso", "aviso", "⚠️", "Estás a perder peso depressa demais",
                f"{resumo}. Mais de 1 kg por semana, em regra, faz perder músculo. "
                f"Come um pouco mais e mantém a proteína alta.")]
        if por_semana <= -0.2:
            extra = f" Faltam {_pt_num(abs(falta))} kg para os {_pt_num(alvo)} kg que pretendes." if falta and falta > 0 else ""
            return [_conselho("peso", "ok", "📉", "A perder peso, no ritmo certo",
                f"{resumo}. Ritmo de cerca de {_pt_num(abs(por_semana))} kg por semana.{extra}")]
        if por_semana < 0.2:
            return [_conselho("peso", "aviso", "➖", "Peso estagnado",
                f"{resumo}. O objetivo é perder peso, mas o peso não mexeu. "
                f"Confirma se estás a registar tudo (molhos, óleos e beliscos contam) e acrescenta mais passos ou treino.")]
        return [_conselho("peso", "aviso", "📈", "O peso está a subir",
            f"{resumo}. O teu objetivo é perder peso, mas o peso aumentou. "
            f"Vê as calorias médias dos últimos dias e a secção dos doces.")]

    # --- Ganhar peso / massa
    if objetivo in OBJETIVOS_GANHAR:
        if por_semana > 0.75:
            return [_conselho("peso", "aviso", "⚠️", "Estás a ganhar peso depressa demais",
                f"{resumo}. Acima de 0,5 kg por semana, grande parte tende a ser gordura. Reduz um pouco as calorias.")]
        if por_semana >= 0.15:
            extra = f" Faltam {_pt_num(abs(falta))} kg para os {_pt_num(alvo)} kg." if falta and falta < 0 else ""
            return [_conselho("peso", "ok", "📈", "A ganhar peso, no ritmo certo",
                f"{resumo}. Ritmo de cerca de {_pt_num(por_semana)} kg por semana.{extra}")]
        if por_semana > -0.15:
            return [_conselho("peso", "aviso", "➖", "Peso estagnado",
                f"{resumo}. Queres ganhar peso mas ele não mexeu. Aumenta cerca de 200 a 300 kcal por dia "
                f"(aveia, frutos secos, azeite, arroz).")]
        return [_conselho("peso", "aviso", "📉", "O peso está a descer",
            f"{resumo}. O objetivo é ganhar peso mas ele está a descer. Estás a comer abaixo do que gastas, "
            f"por isso come mais e não saltes refeições.")]

    # --- Manter / condição / recomposição
    if abs(por_semana) <= 0.3:
        return [_conselho("peso", "ok", "⚖️", "Peso estável",
            f"{resumo}. Está estável, como pretendes.")]
    direcao = "a subir" if por_semana > 0 else "a descer"
    return [_conselho("peso", "aviso", "⚖️", f"O peso está {direcao}",
        f"{resumo}. O teu objetivo é manter o peso. Ajusta as calorias para voltares ao equilíbrio.")]


# ----------------------------------------------------------------- Orquestração

def gerar_conselhos(profile, targets, meals, pesos, hoje, receitas=None, excluidos_nomes=None):
    """Junta tudo. Ordem: avisos primeiro, depois informação e, por fim, o que está bem."""
    conselhos = []
    conselhos += analisar_macros(targets, meals, hoje, receitas=receitas, excluidos_nomes=excluidos_nomes)
    conselhos += analisar_padroes(meals, hoje)
    conselhos += analisar_peso(profile, pesos, hoje)
    ordem = {"aviso": 0, "info": 1, "ok": 2}
    conselhos.sort(key=lambda c: ordem.get(c["nivel"], 1))
    return conselhos
