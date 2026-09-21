import os
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory

import data_store as db
import nutrition_calc as nc
from meal_parser import parse_meal_text
from food_data import lookup as food_lookup
from recipes import sugerir_receitas, find_recipe_by_name, RECIPES
import meal_items as mi
from workouts import get_workout_for_goal, youtube_search_url
from exercise_planner import plano_diario, plano_semanal
import push
from reminders import verificar_lembretes

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-troca-isto")
app.jinja_env.filters["youtube_url"] = youtube_search_url


def _start_scheduler():
    if os.environ.get("DISABLE_SCHEDULER"):
        return
    # evita arrancar 2 vezes por causa do reloader do modo debug
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(verificar_lembretes, "interval", minutes=15)
    scheduler.start()


_start_scheduler()

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

HABITO_CAMPO = {
    "pequeno_almoco": "habito_pequeno_almoco",
    "almoco": "habito_almoco",
    "lanche": "habito_lanche",
    "jantar": "habito_jantar",
}
HABITO_LABEL = {
    "pequeno_almoco": "Pequeno-almoço habitual",
    "almoco": "Almoço habitual",
    "lanche": "Lanche habitual",
    "jantar": "Jantar habitual",
}

# ícones (caminhos SVG) do ecrã "Início" redesenhado
ICONES_ORGANIC = {
    "pequeno_almoco": "M12 4v2 M12 18v2 M5 12H3 M21 12h-2 M17.5 6.5 19 5 M5 5l1.5 1.5 "
                       "M6.5 17.5 5 19 M19 19l-1.5-1.5 M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8",
    "almoco": "M7 3v18 M4 3v6a3 3 0 0 0 6 0V3 M17 3c2 0 3 1.6 3 4s-1 4-3 4v10",
    "lanche": "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18 M9 10h.01 M14.5 9.5h.01 M13 15h.01",
    "jantar": "M20 14A8 8 0 1 1 10 4a6 6 0 0 0 10 10Z",
}


def atualizar_perfil(**campos):
    """Muda só os campos indicados no perfil, sem apagar o resto — lê o
    perfil atual, junta as alterações, e grava tudo de novo."""
    atual = db.get_profile() or {}
    novo = dict(atual)
    novo.update(campos)
    db.save_profile(novo)
    return novo


def week_bounds(ref_date):
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


DIA_SEMANA_ABBR = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]


def dias_rapidos_duplicar(today):
    """Só 'Ontem' e 'Antes de ontem' — para o resto há o botão 'Mais
    antiga' (calendário) no template."""
    return [
        {"data": (today - timedelta(days=1)).isoformat(), "label": "Ontem"},
        {"data": (today - timedelta(days=2)).isoformat(), "label": "Antes de ontem"},
    ]


def data_valida(valor, default=None):
    """Confirma que `valor` é uma data YYYY-MM-DD válida; caso contrário
    devolve `default` (hoje, por omissão). Usa-se sempre que uma data vem
    de fora (query string / formulário) antes de guardar seja o que for —
    é o que evita o bug de registar sempre no dia de hoje por engano."""
    if default is None:
        default = date.today().isoformat()
    if not valor:
        return default
    try:
        date.fromisoformat(valor)
        return valor
    except ValueError:
        return default


def _construir_refeicoes_organic(meals_by_type, habitos, refeicoes_duplicaveis, data_destino, voltar, extra, peso_unidade):
    """Monta a lista de refeições no formato usado pelos cartões bonitos
    (ícones, itens, ações) — partilhado entre o Início (hoje) e a página
    de um dia específico, para os dois terem sempre o mesmo visual.

    `data_destino` é o dia para onde qualquer ação aqui (registar, não
    comi, habitual) vai gravar. `voltar` é só para onde o botão Editar
    volta depois de guardar ("index" ou a data ISO de outro dia)."""
    refeicoes_organic = []
    for tipo in ["pequeno_almoco", "almoco", "lanche", "jantar"]:
        meal = meals_by_type[tipo]
        label = nc.MEAL_LABELS[tipo][1]
        saltada = bool(meal) and meal.get("texto_original") == "Não comi nada"
        itens = mi.resumo_itens(meal.get("texto_original"), extra=extra, peso_unidade=peso_unidade) if meal and not saltada else None
        origens = [(t2, f"{nc.MEAL_LABELS[t2][0]} {nc.MEAL_LABELS[t2][1]}") for t2 in refeicoes_duplicaveis]
        refeicoes_organic.append({
            "tipo": label, "tipo_slug": tipo, "icone": ICONES_ORGANIC[tipo],
            "itens": [{"nome": it["nome"], "kcal": round(it["kcal"])} for it in itens] if itens else [],
            "registada": bool(meal), "saltada": saltada,
            "kcal": round(meal["kcal"]) if meal else 0,
            "p": round(meal["proteina_g"]) if meal else 0,
            "c": round(meal["hidratos_g"]) if meal else 0,
            "g": round(meal["gordura_g"]) if meal else 0,
            "editar_href": url_for("editar_refeicao", page_id=meal["page_id"], voltar=voltar) if meal else "",
            "registar_href": url_for("registar_refeicao", tipo=tipo, data=data_destino),
            "nao_comi_href": url_for("nao_comi", tipo=tipo, data=data_destino),
            "habitual_href": url_for("registar_habitual", tipo=tipo, data=data_destino) if (not meal and habitos.get(tipo)) else None,
            "duplicar_origens": origens if not meal else None,
        })
    return refeicoes_organic


def gerar_nota_periodica(targets, meals_ultimos_3_dias, excluidos_nomes=None):
    """De 3 em 3 dias: analisa a média de proteína consumida e, se estiver
    abaixo do objetivo, devolve uma nota com sugestões de receitas ricas
    em proteína. Devolve None se não houver nada a assinalar."""
    if not targets or not targets.get("protein_g"):
        return None
    dias = 3
    media_prot = sum(m["proteina_g"] for m in meals_ultimos_3_dias) / dias
    alvo = targets["protein_g"]
    if media_prot >= alvo * 0.85:
        return None

    excluidos_nomes = set(excluidos_nomes or [])
    candidatas = [r for r in RECIPES if r["nome"] not in excluidos_nomes]
    candidatas = sorted(candidatas, key=lambda r: -r["proteina_g"])[:4]

    return {
        "mensagem": (
            f"Nos últimos 3 dias comeste em média {round(media_prot)}g de proteína por dia "
            f"(o teu objetivo é {alvo}g). Tenta incluir mais fontes de proteína nas refeições."
        ),
        "sugestoes": [r["nome"] for r in candidatas],
    }


@app.context_processor
def inject_globals():
    return {"notion_configured": db.configured(), "using_notion": db.USING_NOTION, "backend_name": db.BACKEND_NAME}


@app.route("/")
def index():
    today = date.today()
    today_iso = today.isoformat()
    monday, sunday = week_bounds(today)

    if db.configured():
        # Perfil e refeições da semana são independentes — corremos os dois
        # pedidos ao mesmo tempo em vez de um a seguir ao outro.
        with ThreadPoolExecutor(max_workers=2) as ex:
            f_profile = ex.submit(db.get_profile)
            f_week = ex.submit(db.get_meals_between, monday.isoformat(), sunday.isoformat())
            profile = f_profile.result()
            week_meals = f_week.result()
    else:
        profile = None
        week_meals = []

    if not profile or not profile.get("idade"):
        return redirect(url_for("onboarding"))

    # Um único pedido à base de dados cobre a semana toda (incluindo hoje) —
    # evita repetir o mesmo pedido duas vezes, o que torna a página mais rápida.
    meals_today = [m for m in week_meals if m["data"] == today_iso]

    totals = {"kcal": 0, "proteina_g": 0, "hidratos_g": 0, "gordura_g": 0}
    for m in meals_today:
        totals["kcal"] += m["kcal"]
        totals["proteina_g"] += m["proteina_g"]
        totals["hidratos_g"] += m["hidratos_g"]
        totals["gordura_g"] += m["gordura_g"]

    targets = nc.macro_targets(profile) or {"kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}

    meals_by_type = {"pequeno_almoco": None, "almoco": None, "lanche": None, "jantar": None}
    for m in meals_today:
        meals_by_type[m["tipo"]] = m

    week_summary = []
    for i in range(7):
        d = monday + timedelta(days=i)
        d_iso = d.isoformat()
        day_meals = [m for m in week_meals if m["data"] == d_iso]
        day_kcal = sum(m["kcal"] for m in day_meals)
        day_prot = sum(m["proteina_g"] for m in day_meals)
        week_summary.append({
            "label": DIAS_SEMANA[i],
            "date": d_iso,
            "is_today": d_iso == today_iso,
            "kcal": round(day_kcal),
            "proteina_g": round(day_prot),
            "n_refeicoes": len(day_meals),
        })

    restante_kcal = max(round(targets["kcal"] - totals["kcal"]), 0)
    restante_prot = max(round(targets["protein_g"] - totals["proteina_g"]), 0)

    habitos = {tipo: (profile.get(campo) or "").strip() for tipo, campo in HABITO_CAMPO.items()}
    refeicoes_duplicaveis = [t for t, m in meals_by_type.items() if m and m.get("texto_original") != "Não comi nada"]

    # De 3 em 3 dias mostramos uma nota nutricional (sem precisar de guardar
    # estado — o dia do ano garante que só aparece 1 em cada 3 dias).
    nota_nutricional = None
    if today.toordinal() % 3 == 0:
        inicio = (today - timedelta(days=2)).isoformat()
        meals_recentes = [m for m in week_meals if inicio <= m["data"] <= today_iso]
        if inicio < monday.isoformat():
            # os últimos 3 dias atravessam para a semana anterior — vai buscar essa parte
            extra = db.get_meals_between(inicio, monday.isoformat())
            vistos = {m["page_id"] for m in meals_recentes}
            meals_recentes += [m for m in extra if m["page_id"] not in vistos]
        excluidos_nomes = [e["nome"] for e in db.get_excluidos()]
        nota_nutricional = gerar_nota_periodica(targets, meals_recentes, excluidos_nomes)

    # ---------- dados para o novo visual (Início) ----------
    alimentos_custom_hoje = db.get_custom_foods() if db.configured() else []
    extra_hoje = mi.dict_custom(alimentos_custom_hoje)
    peso_unidade_hoje = mi.dict_peso_unidade(alimentos_custom_hoje)

    refeicoes_organic = _construir_refeicoes_organic(
        meals_by_type, habitos, refeicoes_duplicaveis,
        data_destino=today_iso, voltar="index", extra=extra_hoje, peso_unidade=peso_unidade_hoje,
    )

    dia_semana_abbr = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"][today.weekday()]
    mes_abbr = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][today.month - 1]

    dia_organic = {
        "data_legivel": f"{dia_semana_abbr}, {today.day} {mes_abbr}",
        "kcal": f"{round(totals['kcal']):,}".replace(",", " "),
        "pct": min(1.0, (totals["kcal"] / targets["kcal"]) if targets["kcal"] else 0),
        "refeicoes": refeicoes_organic,
        "macros": [
            {"nome": "Proteína", "valor": round(totals["proteina_g"]), "meta": round(targets["protein_g"]),
             "pct": min(100, round(totals["proteina_g"] / targets["protein_g"] * 100)) if targets["protein_g"] else 0, "classe": ""},
            {"nome": "Hidratos", "valor": round(totals["hidratos_g"]), "meta": round(targets["carbs_g"]),
             "pct": min(100, round(totals["hidratos_g"] / targets["carbs_g"] * 100)) if targets["carbs_g"] else 0, "classe": "m-carb"},
            {"nome": "Gordura", "valor": round(totals["gordura_g"]), "meta": round(targets["fat_g"]),
             "pct": min(100, round(totals["gordura_g"] / targets["fat_g"] * 100)) if targets["fat_g"] else 0, "classe": "m-fat"},
        ],
    }

    peso_kg = profile.get("peso_kg")
    peso_organic = {
        "atual": (f"{peso_kg:.1f}".replace(".", ",") + " kg") if peso_kg else "—",
        "pontos": "", "ultimo": None, "variacao": "Atualiza no teu Perfil",
    }

    semana_organic = [
        {"dia": s["label"][:3], "pct": max(5, min(100, round(s["kcal"] / targets["kcal"] * 100))) if targets["kcal"] else 5,
         "hoje": s["is_today"], "href": url_for("dia", data_iso=s["date"])}
        for s in week_summary
    ]

    plano_treino = plano_diario(profile.get("objetivo"), totals, targets, weekday=today.weekday())
    treino_organic = {"nome": plano_treino["workout"]["titulo"], "detalhe": plano_treino["mensagem"]}

    tipo_proxima = next((t for t in ["pequeno_almoco", "almoco", "lanche", "jantar"] if not meals_by_type[t]), "almoco")
    proxima_refeicao_href = url_for("registar_refeicao", tipo=tipo_proxima)

    return render_template(
        "inicio.html", profile=profile, totals=totals, targets=targets,
        meals_by_type=meals_by_type, meal_labels=nc.MEAL_LABELS,
        week_summary=week_summary, today=today_iso, habitos=habitos,
        restante_kcal=restante_kcal, restante_prot=restante_prot,
        goal_label=nc.GOAL_LABELS.get(profile.get("objetivo"), ""),
        nota_nutricional=nota_nutricional,
        refeicoes_duplicaveis=refeicoes_duplicaveis,
        ecra="inicio", notificacoes_novas=False,
        perfil={"objetivo": nc.GOAL_LABELS.get(profile.get("objetivo"), "")},
        objetivo={"kcal": round(targets["kcal"]), "p": round(targets["protein_g"]),
                  "c": round(targets["carbs_g"]), "g": round(targets["fat_g"])},
        dia=dia_organic, peso=peso_organic, semana=semana_organic,
        treino=treino_organic, proxima_refeicao_href=proxima_refeicao_href,
        abrir=request.args.get("abrir"),
        dias_rapidos_duplicar=dias_rapidos_duplicar(today),
    )


LEMBRETE_TIPOS = [
    ("pequeno_almoco", "Lembrar pequeno-almoço"),
    ("almoco", "Lembrar almoço"),
    ("lanche", "Lembrar lanche"),
    ("jantar", "Lembrar jantar"),
]


GOAL_META = {
    "perder_peso": "−20% kcal", "perder_gordura": "−15% kcal", "ganhar_massa": "+12% kcal",
    "aumentar_peso": "+15% kcal", "manter_peso": "manutenção",
    "melhorar_condicao": "manutenção", "recomposicao": "−5% kcal",
}
HORA_CAMPO_POR_TIPO = {"pequeno_almoco": "hora_pequeno_almoco", "almoco": "hora_almoco",
                       "lanche": "hora_lanche", "jantar": "hora_jantar"}


@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    if request.method == "POST":
        data = {
            "idade": int(request.form["idade"]),
            "sexo": request.form["sexo"],
            "altura_cm": float(request.form["altura_cm"]),
            "peso_kg": float(request.form["peso_kg"]),
            "nivel_atividade": request.form["nivel_atividade"],
            "peso_pretendido": float(request.form["peso_pretendido"]) if request.form.get("peso_pretendido") else None,
            "hora_pequeno_almoco": request.form.get("hora_pequeno_almoco", "08:00"),
            "hora_almoco": request.form.get("hora_almoco", "13:00"),
            "hora_lanche": request.form.get("hora_lanche", "17:00"),
            "hora_jantar": request.form.get("hora_jantar", "20:00"),
            "hora_treino": request.form.get("hora_treino", ""),
        }
        # atualizar_perfil só muda estes campos — o objetivo (form à parte),
        # as refeições habituais e os lembretes não se perdem.
        atualizar_perfil(**data)
        flash("Dados guardados! 🎉", "success")
        return redirect(url_for("perfil"))

    profile = db.get_profile() if db.configured() else None
    if not profile or not profile.get("idade"):
        return redirect(url_for("onboarding"))

    targets = nc.macro_targets(profile) or {"kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}

    alimentos_custom = db.get_custom_foods() if db.configured() else []
    extra = mi.dict_custom(alimentos_custom)
    peso_unidade = mi.dict_peso_unidade(alimentos_custom)

    refeicoes_habituais = []
    for tipo, campo in HABITO_CAMPO.items():
        texto = (profile.get(campo) or "").strip()
        if not texto:
            continue
        itens_guardados = mi.descodificar(texto)
        if itens_guardados is not None:
            total, itens_calc, _ = mi.calcular_itens(itens_guardados, extra=extra, peso_unidade=peso_unidade)
            kcal = round(total["kcal"])
            itens = [{"nome": it["nome"], "quantidade": f'{it["quantidade"]:g} {it["unidade_label"]}'} for it in itens_calc]
        else:
            kcal = 0
            itens = [{"nome": texto, "quantidade": ""}]
        refeicoes_habituais.append({
            "tipo": tipo, "hora": profile.get(HORA_CAMPO_POR_TIPO[tipo], ""),
            "nome": HABITO_LABEL.get(tipo, tipo), "kcal": kcal, "itens": itens,
        })
    refeicoes_habituais.sort(key=lambda r: r["hora"] or "99:99")

    minhas_receitas = db.get_custom_recipes() if db.configured() else []

    lembretes = []
    for chave, nome in LEMBRETE_TIPOS:
        lembretes.append({
            "chave": chave, "nome": nome,
            "detalhe": f"Por volta das {profile.get(HORA_CAMPO_POR_TIPO[chave], '')}",
            "ativo": not profile.get(f"pular_lembrete_{chave}"),
        })

    objetivos = [{"id": k, "nome": v, "meta": GOAL_META.get(k, "")} for k, v in nc.GOAL_LABELS.items()]

    return render_template(
        "perfil.html", ecra="perfil", notificacoes_novas=False, profile=profile,
        objetivo={"kcal": round(targets["kcal"]), "p": round(targets["protein_g"]),
                  "c": round(targets["carbs_g"]), "g": round(targets["fat_g"])},
        activity_labels=nc.ACTIVITY_LABELS,
        perfil={"objetivo": nc.GOAL_LABELS.get(profile.get("objetivo"), "")},
        objetivos=objetivos, objetivo_atual=profile.get("objetivo"),
        refeicoes_habituais=refeicoes_habituais, minhas_receitas=minhas_receitas,
        lembretes=lembretes,
    )


@app.route("/perfil/objetivo", methods=["POST"])
def guardar_objetivo():
    objetivo = request.form.get("objetivo", "")
    if objetivo in nc.GOAL_LABELS:
        atualizar_perfil(objetivo=objetivo)
        flash("Objetivo atualizado! As tuas metas diárias já foram recalculadas.", "success")
    return redirect(url_for("perfil"))


@app.route("/perfil/lembrete", methods=["POST"])
def alternar_lembrete():
    chave = request.form.get("chave", "")
    if chave in HABITO_CAMPO:
        profile = db.get_profile() or {}
        campo = f"pular_lembrete_{chave}"
        atualizar_perfil(**{campo: not profile.get(campo)})
    return redirect(url_for("perfil"))


@app.route("/onboarding", methods=["GET", "POST"])
def onboarding():
    if request.method == "POST":
        data = {
            "idade": int(request.form["idade"]),
            "sexo": request.form["sexo"],
            "altura_cm": float(request.form["altura_cm"]),
            "peso_kg": float(request.form["peso_kg"]),
            "nivel_atividade": request.form["nivel_atividade"],
            "objetivo": request.form["objetivo"],
            "peso_pretendido": float(request.form["peso_pretendido"]) if request.form.get("peso_pretendido") else None,
            "hora_pequeno_almoco": request.form.get("hora_pequeno_almoco", "08:00"),
            "hora_almoco": request.form.get("hora_almoco", "13:00"),
            "hora_lanche": request.form.get("hora_lanche", "17:00"),
            "hora_jantar": request.form.get("hora_jantar", "20:00"),
            "hora_treino": request.form.get("hora_treino", ""),
            "pular_lembrete_pequeno_almoco": bool(request.form.get("pular_lembrete_pequeno_almoco")),
            "pular_lembrete_almoco": bool(request.form.get("pular_lembrete_almoco")),
            "pular_lembrete_lanche": bool(request.form.get("pular_lembrete_lanche")),
            "pular_lembrete_jantar": bool(request.form.get("pular_lembrete_jantar")),
        }
        # as refeições habituais agora editam-se numa página própria (/perfil/habitual/<tipo>) —
        # aqui mantemos os valores já guardados para não os apagar ao gravar o resto do perfil.
        perfil_atual = db.get_profile() or {}
        for campo in HABITO_CAMPO.values():
            data[campo] = perfil_atual.get(campo, "")
        db.save_profile(data)
        flash("Perfil guardado! 🎉", "success")
        return redirect(url_for("index"))

    profile = db.get_profile() if db.configured() else None
    habitos_resumo = {}
    if profile:
        alimentos_custom = db.get_custom_foods() if db.configured() else []
        extra = mi.dict_custom(alimentos_custom)
        peso_unidade = mi.dict_peso_unidade(alimentos_custom)
        for tipo, campo in HABITO_CAMPO.items():
            texto = (profile.get(campo) or "").strip()
            if not texto:
                habitos_resumo[tipo] = None
            else:
                itens = mi.resumo_itens(texto, extra=extra, peso_unidade=peso_unidade)
                habitos_resumo[tipo] = ", ".join(it["nome"] for it in itens) if itens else texto
    return render_template(
        "onboarding.html", profile=profile, habitos_resumo=habitos_resumo,
        goal_labels=nc.GOAL_LABELS, activity_labels=nc.ACTIVITY_LABELS,
    )


@app.route("/registar-refeicao", methods=["GET", "POST"])
def registar_refeicao():
    tipo_padrao = request.args.get("tipo", "almoco")
    hoje_iso = date.today().isoformat()
    data_destino = data_valida(request.values.get("data"), default=hoje_iso)
    resultado = None
    alimentos_custom = db.get_custom_foods() if db.configured() else []
    extra = mi.dict_custom(alimentos_custom)
    peso_unidade = mi.dict_peso_unidade(alimentos_custom)
    if request.method == "POST":
        tipo = request.form["tipo"]
        data_destino = data_valida(request.form.get("data"), default=hoje_iso)
        itens_form = mi.itens_do_formulario(request.form)
        if itens_form:
            total, itens, nao_reconhecidos = mi.calcular_itens(itens_form, extra=extra, peso_unidade=peso_unidade)
            if itens:
                texto_canonico = mi.codificar([it for it in itens_form if it["chave"] not in nao_reconhecidos])
                db.add_meal(data_destino, tipo, texto_canonico,
                            total["kcal"], total["proteina_g"], total["hidratos_g"], total["gordura_g"])
                resultado = {"total": total, "itens": itens}
                flash("Refeição registada! ✅", "success")
            if nao_reconhecidos:
                flash("Não conheço: " + ", ".join(nao_reconhecidos) +
                      ". Cria estes alimentos em baixo (⬇️ Não encontraste o alimento?) e volta a tentar.", "error")
        else:
            flash("Escolhe pelo menos um alimento.", "error")
        tipo_padrao = tipo

    receitas_sugeridas = []
    if db.configured():
        profile = db.get_profile()
        targets = nc.macro_targets(profile) if profile else None
        meals_dia = db.get_meals_for_day(data_destino)
        consumido_kcal = sum(m["kcal"] for m in meals_dia)
        consumido_prot = sum(m["proteina_g"] for m in meals_dia)
        restante_kcal = round((targets["kcal"] if targets else 0) - consumido_kcal)
        restante_prot = round((targets["protein_g"] if targets else 0) - consumido_prot)
        pantry_nomes = [p["nome"] for p in db.get_pantry()]
        excluidos_nomes = [e["nome"] for e in db.get_excluidos()]
        minhas_receitas = db.get_custom_recipes()
        prontas, _quase = sugerir_receitas(pantry_nomes, restante_kcal, restante_prot,
                                            excluidos_nomes=excluidos_nomes, top_n=10,
                                            receitas_extra=minhas_receitas)
        receitas_sugeridas = [it["receita"]["nome"] for it in prontas]

    return render_template("registar_refeicao.html", tipo_padrao=tipo_padrao,
                            meal_labels=nc.MEAL_LABELS, resultado=resultado,
                            receitas_sugeridas=receitas_sugeridas,
                            unit_order=mi.UNIT_ORDER, unit_labels=mi.UNIT_LABELS,
                            datalist_opcoes=mi.opcoes_datalist(alimentos_custom),
                            hoje_iso=hoje_iso, data_destino=data_destino,
                            voltar_href=(url_for("index") if data_destino == hoje_iso else url_for("dia", data_iso=data_destino)))


@app.route("/alimentos/pesquisar")
def pesquisar_alimento():
    """Vai à Open Food Facts (base de dados livre de alimentos) tentar
    preencher automaticamente kcal/proteína/hidratos/gordura por 100g,
    a partir do nome escrito pela pessoa. Devolve {"encontrado": false}
    se não conseguir (sem internet, alimento não existe lá, etc) — nesse
    caso a pessoa preenche à mão como antes."""
    nome = (request.args.get("nome") or "").strip()
    if not nome:
        return jsonify({"encontrado": False})
    try:
        r = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": nome, "search_simple": 1, "json": 1,
                "page_size": 5, "fields": "product_name,nutriments",
            },
            timeout=6,
            headers={"User-Agent": "NutriApp/1.0 (app pessoal)"},
        )
        r.raise_for_status()
        produtos = r.json().get("products", [])
    except Exception:
        return jsonify({"encontrado": False})

    opcoes = []
    for p in produtos:
        nutri = p.get("nutriments", {})
        kcal = nutri.get("energy-kcal_100g")
        proteina = nutri.get("proteins_100g")
        hidratos = nutri.get("carbohydrates_100g")
        gordura = nutri.get("fat_100g")
        if kcal is None:
            continue
        opcoes.append({
            "nome_produto": p.get("product_name") or nome,
            "kcal": round(kcal, 1),
            "proteina_g": round(proteina or 0, 1),
            "hidratos_g": round(hidratos or 0, 1),
            "gordura_g": round(gordura or 0, 1),
        })
    if not opcoes:
        return jsonify({"encontrado": False})
    return jsonify({"encontrado": True, "opcoes": opcoes})


@app.route("/alimentos/novo", methods=["POST"])
def criar_alimento():
    nome = request.form.get("nome", "").strip()
    seguinte = request.form.get("next") or ""
    if not seguinte.startswith("/"):
        seguinte = url_for("registar_refeicao")

    def voltar():
        return redirect(seguinte)

    if not nome:
        flash("Escreve o nome do alimento.", "error")
        return voltar()
    try:
        kcal = float((request.form.get("kcal") or "0").replace(",", "."))
        proteina = float((request.form.get("proteina") or "0").replace(",", "."))
        hidratos = float((request.form.get("hidratos") or "0").replace(",", "."))
        gordura = float((request.form.get("gordura") or "0").replace(",", "."))
        peso_unidade_txt = (request.form.get("peso_unidade") or "").strip()
        peso_unidade = float(peso_unidade_txt.replace(",", ".")) if peso_unidade_txt else None
    except ValueError:
        flash("Os valores têm de ser números.", "error")
        return voltar()

    db.add_custom_food(nome, kcal, proteina, hidratos, gordura, peso_unidade_g=peso_unidade)
    flash(f"'{nome}' criado! Já podes escrever o nome dele na refeição. ✅", "success")
    return voltar()


@app.route("/alimentos")
def gerir_alimentos():
    alimentos_custom = db.get_custom_foods() if db.configured() else []
    return render_template("gerir_alimentos.html", alimentos=mi.lista_completa(alimentos_custom))


@app.route("/alimentos/guardar", methods=["POST"])
def guardar_alimento():
    nome = request.form.get("nome", "").strip()
    page_id = request.form.get("page_id", "").strip()
    if not nome:
        flash("Escreve o nome do alimento.", "error")
        return redirect(url_for("gerir_alimentos"))
    try:
        kcal = float((request.form.get("kcal") or "0").replace(",", "."))
        proteina = float((request.form.get("proteina") or "0").replace(",", "."))
        hidratos = float((request.form.get("hidratos") or "0").replace(",", "."))
        gordura = float((request.form.get("gordura") or "0").replace(",", "."))
        peso_unidade_txt = (request.form.get("peso_unidade") or "").strip()
        peso_unidade = float(peso_unidade_txt.replace(",", ".")) if peso_unidade_txt else None
    except ValueError:
        flash("Os valores têm de ser números.", "error")
        return redirect(url_for("gerir_alimentos"))

    if page_id:
        db.update_custom_food(page_id, nome, kcal, proteina, hidratos, gordura, peso_unidade_g=peso_unidade)
        flash(f"'{nome}' atualizado! ✏️", "success")
    else:
        db.add_custom_food(nome, kcal, proteina, hidratos, gordura, peso_unidade_g=peso_unidade)
        flash(f"'{nome}' guardado com os teus valores. ✅", "success")
    return redirect(url_for("gerir_alimentos"))


@app.route("/alimentos/<page_id>/remover-personalizacao", methods=["POST"])
def remover_personalizacao_alimento(page_id):
    db.delete_custom_food(page_id)
    flash("Voltou aos valores por omissão (ou foi removido, se era só teu).", "success")
    return redirect(url_for("gerir_alimentos"))


@app.route("/registar-refeicao/receita", methods=["POST"])
def registar_refeicao_receita():
    tipo = request.form.get("tipo", "almoco")
    nome_receita = request.form.get("nome_receita", "").strip()
    data_destino = data_valida(request.form.get("data"))
    if not nome_receita:
        flash("Escolhe uma receita da lista.", "error")
        return redirect(url_for("registar_refeicao", tipo=tipo, data=data_destino))

    minhas_receitas = db.get_custom_recipes() if db.configured() else []
    receita = find_recipe_by_name(nome_receita, receitas_extra=minhas_receitas)
    if not receita:
        flash("Não encontrei essa receita.", "error")
        return redirect(url_for("registar_refeicao", tipo=tipo, data=data_destino))

    db.add_meal(data_destino, tipo, receita["nome"],
                receita["kcal"], receita["proteina_g"], receita["hidratos_g"], receita["gordura_g"])
    flash(f"'{receita['nome']}' registada! ✅", "success")
    if data_destino == date.today().isoformat():
        return redirect(url_for("index"))
    return redirect(url_for("dia", data_iso=data_destino))


@app.route("/refeicao/<page_id>/editar", methods=["GET", "POST"])
def editar_refeicao(page_id):
    voltar = request.values.get("voltar", "")
    meal = db.get_meal(page_id)
    if not meal:
        flash("Não encontrei essa refeição.", "error")
        return redirect(url_for("index"))

    alimentos_custom = db.get_custom_foods() if db.configured() else []
    extra = mi.dict_custom(alimentos_custom)
    peso_unidade = mi.dict_peso_unidade(alimentos_custom)

    if request.method == "POST":
        itens_form = mi.itens_do_formulario(request.form)
        guardou = False
        if itens_form:
            total, itens, nao_reconhecidos = mi.calcular_itens(itens_form, extra=extra, peso_unidade=peso_unidade)
            if itens:
                texto_canonico = mi.codificar([it for it in itens_form if it["chave"] not in nao_reconhecidos])
                db.update_meal(page_id, texto_canonico, total["kcal"], total["proteina_g"],
                                total["hidratos_g"], total["gordura_g"])
                flash("Refeição atualizada! ✏️", "success")
                guardou = True
            if nao_reconhecidos:
                flash("Não conheço: " + ", ".join(nao_reconhecidos) +
                      ". Cria estes alimentos em baixo (⬇️ Não encontraste o alimento?) e volta a tentar.", "error")
        else:
            flash("Escolhe pelo menos um alimento.", "error")
        if guardou:
            if voltar and voltar != "index":
                return redirect(url_for("dia", data_iso=voltar))
            return redirect(url_for("index"))

    itens_atuais = mi.resumo_itens(meal.get("texto_original"), extra=extra, peso_unidade=peso_unidade)
    return render_template("editar_refeicao.html", meal=meal, meal_labels=nc.MEAL_LABELS, voltar=voltar,
                            itens_atuais=itens_atuais,
                            unit_order=mi.UNIT_ORDER, unit_labels=mi.UNIT_LABELS,
                            datalist_opcoes=mi.opcoes_datalist(alimentos_custom))


@app.route("/refeicao/<page_id>/remover", methods=["POST"])
def remover_refeicao(page_id):
    voltar = request.form.get("voltar", "")
    db.delete_meal(page_id)
    flash("Refeição removida.", "success")
    if voltar and voltar != "index":
        return redirect(url_for("dia", data_iso=voltar))
    return redirect(url_for("index"))


@app.route("/nao-comi/<tipo>", methods=["POST"])
def nao_comi(tipo):
    data_destino = data_valida(request.args.get("data") or request.form.get("data"))
    db.add_meal(data_destino, tipo, "Não comi nada", 0, 0, 0, 0)
    flash("Registado — sem problema, fica marcado.", "success")
    if data_destino == date.today().isoformat():
        return redirect(url_for("index"))
    return redirect(url_for("dia", data_iso=data_destino))


@app.route("/receitas", methods=["GET", "POST"])
def receitas():
    resultado = None
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        ingredientes_raw = request.form.get("ingredientes", "").strip()
        preparo_raw = request.form.get("preparo", "").strip()
        ingredientes = [l.strip() for l in ingredientes_raw.splitlines() if l.strip()]
        preparo = [l.strip() for l in preparo_raw.splitlines() if l.strip()]

        if nome and ingredientes and preparo:
            total = {"kcal": 0.0, "proteina_g": 0.0, "hidratos_g": 0.0, "gordura_g": 0.0}
            itens = []
            chave_despensa = []
            for linha in ingredientes:
                sub_total, sub_itens = parse_meal_text(linha)
                total["kcal"] += sub_total["kcal"]
                total["proteina_g"] += sub_total["proteina_g"]
                total["hidratos_g"] += sub_total["hidratos_g"]
                total["gordura_g"] += sub_total["gordura_g"]
                itens.extend(sub_itens)
                for it in sub_itens:
                    if it["encontrado"] and it["alimento_encontrado"].lower() not in chave_despensa:
                        chave_despensa.append(it["alimento_encontrado"].lower())

            db.add_custom_recipe(nome, ingredientes, preparo, chave_despensa,
                                  total["kcal"], total["proteina_g"], total["hidratos_g"], total["gordura_g"])
            resultado = {"total": total, "itens": itens}
            flash("Receita guardada! 📖 Já entra nas sugestões.", "success")
        else:
            flash("Preenche o título, os ingredientes e o preparo.", "error")

    minhas = db.get_custom_recipes() if db.configured() else []
    return render_template("receitas.html", minhas=minhas, resultado=resultado)


@app.route("/receitas/<page_id>/editar", methods=["GET", "POST"])
def editar_receita(page_id):
    receita = db.get_custom_recipe(page_id)
    if not receita:
        flash("Não encontrei essa receita.", "error")
        return redirect(url_for("receitas"))

    resultado = None
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        ingredientes_raw = request.form.get("ingredientes", "").strip()
        preparo_raw = request.form.get("preparo", "").strip()
        ingredientes = [l.strip() for l in ingredientes_raw.splitlines() if l.strip()]
        preparo = [l.strip() for l in preparo_raw.splitlines() if l.strip()]

        if nome and ingredientes and preparo:
            total = {"kcal": 0.0, "proteina_g": 0.0, "hidratos_g": 0.0, "gordura_g": 0.0}
            chave_despensa = []
            for linha in ingredientes:
                sub_total, sub_itens = parse_meal_text(linha)
                total["kcal"] += sub_total["kcal"]
                total["proteina_g"] += sub_total["proteina_g"]
                total["hidratos_g"] += sub_total["hidratos_g"]
                total["gordura_g"] += sub_total["gordura_g"]
                for it in sub_itens:
                    if it["encontrado"] and it["alimento_encontrado"].lower() not in chave_despensa:
                        chave_despensa.append(it["alimento_encontrado"].lower())

            db.update_custom_recipe(page_id, nome, ingredientes, preparo, chave_despensa,
                                     total["kcal"], total["proteina_g"], total["hidratos_g"], total["gordura_g"])
            flash("Receita atualizada! ✏️", "success")
            return redirect(url_for("receitas"))
        else:
            flash("Preenche o título, os ingredientes e o preparo.", "error")

    return render_template("editar_receita.html", receita=receita)


@app.route("/receitas/remover/<page_id>", methods=["POST"])
def remover_receita(page_id):
    db.delete_custom_recipe(page_id)
    flash("Receita removida.", "success")
    return redirect(url_for("receitas"))


@app.route("/sw.js")
def service_worker():
    # servido na raiz (não em /static/) para o scope do service worker cobrir o site todo
    return send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")


@app.route("/notificacoes")
def notificacoes():
    n_subs = len(db.get_push_subscriptions()) if db.configured() else 0
    return render_template("notificacoes.html", vapid_public_key=push.get_public_key(), n_subs=n_subs)


@app.route("/notificacoes/subscrever", methods=["POST"])
def notificacoes_subscrever():
    sub = request.get_json(silent=True) or {}
    if not sub.get("endpoint"):
        return jsonify({"ok": False}), 400
    db.add_push_subscription(sub)
    return jsonify({"ok": True})


@app.route("/notificacoes/cancelar", methods=["POST"])
def notificacoes_cancelar():
    body = request.get_json(silent=True) or {}
    endpoint = body.get("endpoint")
    if endpoint:
        db.delete_push_subscription(endpoint)
    return jsonify({"ok": True})


@app.route("/notificacoes/teste", methods=["POST"])
def notificacoes_teste():
    subs = db.get_push_subscriptions()
    if not subs:
        flash("Ainda não há nenhum dispositivo a receber notificações. Ativa primeiro.", "error")
        return redirect(url_for("notificacoes"))

    enviados_ok = 0
    erros = []
    for s in subs:
        ok, detalhe = push.send_notification({"endpoint": s["endpoint"], "keys": s["keys"]},
                                               "🥗 NutriApp", "Notificações a funcionar! 🎉", "/")
        if not ok:
            db.delete_push_subscription(s["endpoint"])
            erros.append(detalhe)
        elif detalhe == "ok":
            enviados_ok += 1
        else:
            erros.append(detalhe)

    if enviados_ok:
        flash(f"Notificação de teste enviada ({enviados_ok}). Devias recebê-la em segundos.", "success")
    if erros:
        flash("Alguns envios falharam: " + " | ".join(erros[:3]), "error")
    return redirect(url_for("notificacoes"))


@app.route("/registar-habitual/<tipo>", methods=["POST"])
def registar_habitual(tipo):
    data_destino = data_valida(request.args.get("data") or request.form.get("data"))
    voltar_href = url_for("index") if data_destino == date.today().isoformat() else url_for("dia", data_iso=data_destino)

    profile = db.get_profile()
    campo = HABITO_CAMPO.get(tipo)
    texto = (profile.get(campo) if profile and campo else "") or ""
    texto = texto.strip()
    if not texto:
        flash("Ainda não configuraste esta refeição habitual no Perfil.", "error")
        return redirect(voltar_href)

    alimentos_custom = db.get_custom_foods() if db.configured() else []
    extra = mi.dict_custom(alimentos_custom)
    peso_unidade = mi.dict_peso_unidade(alimentos_custom)
    itens_guardados = mi.descodificar(texto)
    if itens_guardados is not None:
        total, itens, _nao_reconhecidos = mi.calcular_itens(itens_guardados, extra=extra, peso_unidade=peso_unidade)
    else:
        # formato antigo (texto livre escrito antes desta alteração)
        total, itens = parse_meal_text(texto)

    db.add_meal(data_destino, tipo, texto,
                total["kcal"], total["proteina_g"], total["hidratos_g"], total["gordura_g"])
    flash("Refeição habitual registada! ⚡", "success")
    return redirect(voltar_href)


@app.route("/perfil/habitual/<tipo>", methods=["GET", "POST"])
def editar_habitual(tipo):
    if tipo not in HABITO_CAMPO:
        return redirect(url_for("onboarding"))
    campo = HABITO_CAMPO[tipo]
    profile = db.get_profile() or {}
    alimentos_custom = db.get_custom_foods() if db.configured() else []
    extra = mi.dict_custom(alimentos_custom)
    peso_unidade = mi.dict_peso_unidade(alimentos_custom)

    if request.method == "POST":
        itens_form = mi.itens_do_formulario(request.form)
        texto_canonico = mi.codificar(itens_form) if itens_form else ""
        novo_profile = dict(profile)
        novo_profile[campo] = texto_canonico
        db.save_profile(novo_profile)
        flash("Refeição habitual guardada! ⚡", "success")
        return redirect(url_for("onboarding"))

    texto_atual = (profile.get(campo) or "").strip()
    itens_atuais = mi.resumo_itens(texto_atual, extra=extra, peso_unidade=peso_unidade) if texto_atual else None
    formato_antigo = bool(texto_atual) and itens_atuais is None
    return render_template(
        "editar_habitual.html", tipo=tipo, titulo=HABITO_LABEL.get(tipo, tipo),
        itens_atuais=itens_atuais, texto_atual=texto_atual, formato_antigo=formato_antigo,
        unit_order=mi.UNIT_ORDER, unit_labels=mi.UNIT_LABELS,
        datalist_opcoes=mi.opcoes_datalist(alimentos_custom),
    )


@app.route("/dia/<data_iso>")
def dia(data_iso):
    try:
        dia_ref = date.fromisoformat(data_iso)
    except ValueError:
        return redirect(url_for("index"))

    today = date.today()
    today_iso = today.isoformat()
    if data_iso == today_iso:
        # o dia de hoje já tem a sua própria página (Início) — evita ter
        # o mesmo conteúdo duplicado em dois sítios
        return redirect(url_for("index"))

    profile = db.get_profile()
    meals = db.get_meals_for_day(data_iso)
    totals = {"kcal": 0, "proteina_g": 0, "hidratos_g": 0, "gordura_g": 0}
    for m in meals:
        totals["kcal"] += m["kcal"]
        totals["proteina_g"] += m["proteina_g"]
        totals["hidratos_g"] += m["hidratos_g"]
        totals["gordura_g"] += m["gordura_g"]

    targets = nc.macro_targets(profile) if profile else {"kcal": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
    alimentos_custom_dia = db.get_custom_foods() if db.configured() else []
    extra = mi.dict_custom(alimentos_custom_dia)
    peso_unidade = mi.dict_peso_unidade(alimentos_custom_dia)
    meals_by_type = {"pequeno_almoco": None, "almoco": None, "lanche": None, "jantar": None}
    for m in meals:
        meals_by_type[m["tipo"]] = m

    anterior = (dia_ref - timedelta(days=1)).isoformat()
    seguinte = (dia_ref + timedelta(days=1)).isoformat()
    refeicoes_duplicaveis = [t for t, m in meals_by_type.items() if m and m.get("texto_original") != "Não comi nada"]
    habitos = {tipo: (profile.get(campo) or "").strip() for tipo, campo in HABITO_CAMPO.items()} if profile else {}

    # ---------- mesmos dados/visual que o Início (cartões de refeição, anel de calorias) ----------
    refeicoes_organic = _construir_refeicoes_organic(
        meals_by_type, habitos, refeicoes_duplicaveis,
        data_destino=data_iso, voltar=data_iso, extra=extra, peso_unidade=peso_unidade,
    )

    dia_semana_abbr = DIA_SEMANA_ABBR[dia_ref.weekday()]
    mes_abbr = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"][dia_ref.month - 1]
    dia_organic = {
        "data_legivel": f"{dia_semana_abbr}, {dia_ref.day} {mes_abbr}",
        "kcal": f"{round(totals['kcal']):,}".replace(",", " "),
        "pct": min(1.0, (totals["kcal"] / targets["kcal"]) if targets["kcal"] else 0),
        "refeicoes": refeicoes_organic,
        "macros": [
            {"nome": "Proteína", "valor": round(totals["proteina_g"]), "meta": round(targets["protein_g"]),
             "pct": min(100, round(totals["proteina_g"] / targets["protein_g"] * 100)) if targets["protein_g"] else 0, "classe": ""},
            {"nome": "Hidratos", "valor": round(totals["hidratos_g"]), "meta": round(targets["carbs_g"]),
             "pct": min(100, round(totals["hidratos_g"] / targets["carbs_g"] * 100)) if targets["carbs_g"] else 0, "classe": "m-carb"},
            {"nome": "Gordura", "valor": round(totals["gordura_g"]), "meta": round(targets["fat_g"]),
             "pct": min(100, round(totals["gordura_g"] / targets["fat_g"] * 100)) if targets["fat_g"] else 0, "classe": "m-fat"},
        ],
    }

    objetivo = {"kcal": round(targets["kcal"]), "p": round(targets["protein_g"]),
                "c": round(targets["carbs_g"]), "g": round(targets["fat_g"])}

    return render_template(
        "dia.html", data_iso=data_iso, dia_ref=dia_ref, meal_labels=nc.MEAL_LABELS,
        is_today=False, anterior=anterior, seguinte=seguinte, today=today_iso,
        dias_semana=DIAS_SEMANA, dia=dia_organic, objetivo=objetivo,
        dias_rapidos_duplicar=dias_rapidos_duplicar(today),
    )


@app.route("/refeicao/duplicar", methods=["POST"])
def duplicar_refeicao():
    data_iso = request.form.get("data") or date.today().isoformat()
    tipo_destino = request.form.get("tipo_destino")
    tipo_origem = request.form.get("tipo_origem")
    meals = db.get_meals_for_day(data_iso)
    origem = next((m for m in meals if m["tipo"] == tipo_origem), None)
    ja_existe = any(m["tipo"] == tipo_destino for m in meals)

    if not origem:
        flash("Não encontrei essa refeição para duplicar.", "error")
    elif ja_existe:
        flash("Já tens essa refeição registada — edita-a se quiseres mudar.", "error")
    else:
        db.add_meal(data_iso, tipo_destino, origem["texto_original"],
                    origem["kcal"], origem["proteina_g"], origem["hidratos_g"], origem["gordura_g"])
        flash("Refeição duplicada! 📋", "success")

    if data_iso == date.today().isoformat():
        return redirect(url_for("index"))
    return redirect(url_for("dia", data_iso=data_iso))


@app.route("/registar-refeicao/duplicar-de-outro-dia", methods=["POST"])
def duplicar_de_outro_dia():
    """Duplica uma refeição de QUALQUER dia passado para uma refeição de
    outro dia (por omissão hoje). Usado a partir do cartão de uma
    refeição por registar, tanto no Início como na página de um dia
    específico (ex: estou a registar o jantar de dia 18 e quero copiar
    o almoço de terça-feira passada)."""
    tipo_destino = request.form.get("tipo_destino", "almoco")
    data_origem = request.form.get("data_origem", "")
    tipo_origem = request.form.get("tipo_origem", "")
    data_destino = data_valida(request.form.get("data_destino"))

    if not data_origem or tipo_origem not in nc.MEAL_LABELS:
        flash("Escolhe o dia e a refeição que queres duplicar.", "error")
        return redirect(url_for("registar_refeicao", tipo=tipo_destino, data=data_destino))

    meals = db.get_meals_for_day(data_origem)
    origem = next((m for m in meals if m["tipo"] == tipo_origem), None)

    if not origem or origem.get("texto_original") == "Não comi nada":
        flash("Não encontrei essa refeição nesse dia.", "error")
        return redirect(url_for("registar_refeicao", tipo=tipo_destino, data=data_destino))

    ja_existe = any(m["tipo"] == tipo_destino and m.get("texto_original") != "Não comi nada"
                    for m in db.get_meals_for_day(data_destino))
    if ja_existe:
        flash("Já tens essa refeição registada nesse dia — edita-a se quiseres mudar.", "error")
        return redirect(url_for("registar_refeicao", tipo=tipo_destino, data=data_destino))

    db.add_meal(data_destino, tipo_destino, origem["texto_original"],
                origem["kcal"], origem["proteina_g"], origem["hidratos_g"], origem["gordura_g"])
    flash("Refeição duplicada! 📋", "success")
    if data_destino == date.today().isoformat():
        return redirect(url_for("index"))
    return redirect(url_for("dia", data_iso=data_destino))


def _preco_do_formulario(form, campo="preco"):
    """Lê um preço opcional do formulário (aceita vírgula ou ponto).
    Devolve None se estiver vazio ou não for um número válido."""
    bruto = (form.get(campo) or "").strip().replace("€", "").replace(",", ".")
    if not bruto:
        return None
    try:
        valor = float(bruto)
    except ValueError:
        return None
    return valor if valor > 0 else None


@app.route("/despensa", methods=["GET", "POST"])
def despensa():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        quantidade = request.form.get("quantidade", "").strip()
        preco = _preco_do_formulario(request.form)
        if nome:
            db.add_pantry_item(nome, quantidade, preco)
            flash(f"'{nome}' adicionado à despensa.", "success")
        return redirect(url_for("despensa"))

    items = db.get_pantry() if db.configured() else []
    excluidos = db.get_excluidos() if db.configured() else []
    return render_template("despensa.html", ecra="sugestoes", notificacoes_novas=False,
                            alimentos=items, excluidos=excluidos)


@app.route("/despensa/<page_id>/editar", methods=["POST"])
def editar_despensa(page_id):
    nome = request.form.get("nome", "").strip()
    quantidade = request.form.get("quantidade", "").strip()
    preco = _preco_do_formulario(request.form)
    db.update_pantry_item(page_id, quantidade, preco, nome=nome or None)
    flash("Item atualizado.", "success")
    return redirect(url_for("despensa"))


@app.route("/despensa/remover/<page_id>", methods=["POST"])
def remover_despensa(page_id):
    db.delete_pantry_item(page_id)
    flash("Item removido.", "success")
    return redirect(url_for("despensa"))


@app.route("/despensa/excluir", methods=["POST"])
def adicionar_excluido():
    nome = request.form.get("nome", "").strip()
    if nome:
        db.add_excluido(nome)
        flash(f"'{nome}' não vai voltar a ser sugerido.", "success")
    return redirect(url_for("despensa"))


@app.route("/sugestao", methods=["GET", "POST"])
def sugestao():
    if request.method == "POST":
        acao = request.form.get("acao", "add_pantry")
        if acao == "add_excluido":
            nome = request.form.get("nome_excluido", "").strip()
            if nome:
                db.add_excluido(nome)
                flash(f"'{nome}' não vai voltar a ser sugerido.", "success")
        else:
            nome = request.form.get("nome", "").strip()
            quantidade = request.form.get("quantidade", "").strip()
            if nome:
                db.add_pantry_item(nome, quantidade)
                flash(f"'{nome}' adicionado à despensa.", "success")
        return redirect(url_for("sugestao"))

    today_iso = date.today().isoformat()
    # Estes 5 pedidos são independentes entre si — corremos em paralelo em vez
    # de um a seguir ao outro, para a página carregar mais depressa.
    with ThreadPoolExecutor(max_workers=5) as ex:
        f_profile = ex.submit(db.get_profile)
        f_meals = ex.submit(db.get_meals_for_day, today_iso)
        f_pantry = ex.submit(db.get_pantry)
        f_excluidos = ex.submit(db.get_excluidos)
        f_receitas = ex.submit(db.get_custom_recipes)
        profile = f_profile.result()
        meals_today = f_meals.result()
        pantry = f_pantry.result()
        excluidos = f_excluidos.result()
        minhas_receitas = f_receitas.result()

    targets = nc.macro_targets(profile) if profile else None
    consumido_kcal = sum(m["kcal"] for m in meals_today)
    consumido_prot = sum(m["proteina_g"] for m in meals_today)

    restante_kcal = round((targets["kcal"] if targets else 0) - consumido_kcal)
    restante_prot = round((targets["protein_g"] if targets else 0) - consumido_prot)

    pantry_nomes = [p["nome"] for p in pantry]
    excluidos_nomes = [e["nome"] for e in excluidos]

    receitas_prontas, receitas_quase = sugerir_receitas(
        pantry_nomes, restante_kcal, restante_prot, excluidos_nomes=excluidos_nomes, top_n=6,
        receitas_extra=minhas_receitas)

    prontas = [{
        "id": it["receita"]["nome"], "nome": it["receita"]["nome"], "kcal": round(it["receita"]["kcal"]),
        "p": round(it["receita"]["proteina_g"]), "c": round(it["receita"]["hidratos_g"]), "g": round(it["receita"]["gordura_g"]),
        "ingredientes": it["receita"].get("ingredientes", []), "preparo": it["receita"].get("preparo", []),
    } for it in receitas_prontas]
    quase_la = [{
        "id": it["receita"]["nome"], "nome": it["receita"]["nome"], "kcal": round(it["receita"]["kcal"]),
        "p": round(it["receita"]["proteina_g"]), "c": round(it["receita"]["hidratos_g"]), "g": round(it["receita"]["gordura_g"]),
        "falta": it["faltam"][0] if it["faltam"] else "",
        "ingredientes": it["receita"].get("ingredientes", []), "preparo": it["receita"].get("preparo", []),
    } for it in receitas_quase]

    return render_template(
        "sugestao.html", ecra="sugestoes", notificacoes_novas=False,
        disponivel={"kcal": f"{max(restante_kcal, 0):,}".replace(",", " "), "proteina": max(restante_prot, 0)},
        prontas=prontas, quase_la=quase_la, despensa_total=len(pantry),
    )


@app.route("/sugestao/registar", methods=["POST"])
def registar_receita():
    nome_receita = request.form.get("receita_id", "").strip()
    if not nome_receita:
        flash("Escolhe uma receita.", "error")
        return redirect(url_for("sugestao"))

    minhas_receitas = db.get_custom_recipes() if db.configured() else []
    receita = find_recipe_by_name(nome_receita, receitas_extra=minhas_receitas)
    if not receita:
        flash("Não encontrei essa receita.", "error")
        return redirect(url_for("sugestao"))

    meals_today = db.get_meals_for_day(date.today().isoformat()) if db.configured() else []
    registados = {m["tipo"] for m in meals_today}
    tipo = next((t for t in ["pequeno_almoco", "almoco", "lanche", "jantar"] if t not in registados), "almoco")

    db.add_meal(date.today().isoformat(), tipo, receita["nome"],
                receita["kcal"], receita["proteina_g"], receita["hidratos_g"], receita["gordura_g"])
    flash(f"'{receita['nome']}' registada no(a) {nc.MEAL_LABELS[tipo][1]}! ✅", "success")
    return redirect(url_for("index"))


@app.route("/sugestao/lista-compras", methods=["POST"])
def lista_compras():
    nome_receita = request.form.get("receita_id", "").strip()
    minhas_receitas = db.get_custom_recipes() if db.configured() else []
    receita = find_recipe_by_name(nome_receita, receitas_extra=minhas_receitas)
    if receita:
        pantry_nomes = {p["nome"].strip().lower() for p in db.get_pantry()}
        for chave in receita.get("chave_despensa", []):
            if chave.strip().lower() not in pantry_nomes:
                db.add_pantry_item(chave, "por comprar")
        flash("Adicionado à despensa como 'por comprar'.", "success")
    return redirect(url_for("sugestao"))


@app.route("/sugestao/excluidos/remover/<page_id>", methods=["POST"])
def remover_excluido(page_id):
    db.delete_excluido(page_id)
    flash("Removido da lista de excluídos.", "success")
    return redirect(url_for("despensa"))


@app.route("/exercicio", methods=["GET", "POST"])
def exercicio():
    profile = db.get_profile()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        duracao = request.form.get("duracao_min")
        kcal = request.form.get("kcal_estimadas")
        if nome:
            db.add_exercise(
                date.today().isoformat(), nome,
                int(duracao) if duracao else None,
                int(kcal) if kcal else None,
            )
            flash("Treino registado! 💪", "success")
        return redirect(url_for("exercicio"))

    goal_label = nc.GOAL_LABELS.get(profile.get("objetivo"), "") if profile else ""
    objetivo = profile.get("objetivo") if profile else None
    targets = nc.macro_targets(profile) if profile else None

    modo = request.args.get("modo", "diario")
    if modo != "semanal":
        modo = "diario"

    today = date.today()
    monday, sunday = week_bounds(today)

    if db.configured():
        # Estes 3 pedidos são independentes entre si — corremos em paralelo
        # em vez de um a seguir ao outro, para a página carregar mais depressa.
        with ThreadPoolExecutor(max_workers=3) as ex:
            f_week_ex = ex.submit(db.get_exercise_between, monday.isoformat(), sunday.isoformat())
            if modo == "semanal":
                f_meals = ex.submit(db.get_meals_between, monday.isoformat(), sunday.isoformat())
            else:
                f_meals = ex.submit(db.get_meals_for_day, today.isoformat())
            f_active = ex.submit(db.get_active_exercise)
            week_ex = f_week_ex.result()
            meals_result = f_meals.result()
            active_exercise = f_active.result()
    else:
        week_ex, meals_result, active_exercise = [], [], None

    plano = None
    if modo == "semanal":
        week_meals = meals_result
        dias_totais = []
        for i in range(7):
            d_iso = (monday + timedelta(days=i)).isoformat()
            day_meals = [m for m in week_meals if m["data"] == d_iso]
            dias_totais.append({
                "kcal": sum(m["kcal"] for m in day_meals),
                "proteina_g": sum(m["proteina_g"] for m in day_meals),
            })
        plano = plano_semanal(objetivo, dias_totais, targets)
    else:
        meals_today = meals_result
        totals = {
            "kcal": sum(m["kcal"] for m in meals_today),
            "proteina_g": sum(m["proteina_g"] for m in meals_today),
        }
        plano = plano_diario(objetivo, totals, targets, weekday=today.weekday())

    dias_label = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    data_legivel = f"{dias_label[today.weekday()]}, {today.day} {['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'][today.month-1]}"

    if modo == "semanal":
        treino_organic = {"nome": "Plano da semana", "motivo": plano["mensagem"]}
        exercicios_organic = []
        plano_semanal_organic = [
            {"dia": dias_label[i], "foco": foco, "duracao": "—" if foco == "Descanso" else "20-45 min"}
            for i, foco in enumerate(plano["estrutura"])
        ]
    else:
        treino_organic = {"nome": plano["workout"]["titulo"], "motivo": plano["mensagem"]}
        exercicios_organic = plano["workout"]["exercicios"]
        plano_semanal_organic = []

    minutos_por_dia = [0] * 7
    for e in week_ex:
        try:
            d_idx = date.fromisoformat(e["data"]).weekday()
            minutos_por_dia[d_idx] += e.get("duracao_min") or 0
        except (ValueError, KeyError):
            pass
    semana_organic = [
        {"dia": dias_label[i], "minutos": minutos_por_dia[i],
         "pct": max(6, round(min(1, minutos_por_dia[i] / 60) * 100)), "hoje": i == today.weekday()}
        for i in range(7)
    ]
    total_min = sum(minutos_por_dia)
    dias_com_treino = sum(1 for m in minutos_por_dia if m)
    resumo_semana = [
        {"label": "Tempo total", "valor": f"{total_min} min"},
        {"label": "Treinos feitos", "valor": f"{len(week_ex)}"},
        {"label": "Média por treino", "valor": f"{round(total_min / len(week_ex))} min" if week_ex else "—"},
    ]

    return render_template(
        "exercicio.html", ecra="exercicio", notificacoes_novas=False,
        data_legivel=data_legivel, modo=modo, treino=treino_organic, exercicios=exercicios_organic,
        plano_semanal=plano_semanal_organic, semana=semana_organic, resumo_semana=resumo_semana,
        week_ex=week_ex, active_exercise=active_exercise,
    )


@app.route("/exercicio/iniciar", methods=["POST"])
def iniciar_exercicio():
    nome = request.form.get("nome", "").strip()
    if not nome:
        flash("Falta o nome do treino.", "error")
        return redirect(url_for("exercicio"))
    if db.get_active_exercise():
        flash("Já tens um treino em curso — termina-o primeiro.", "error")
        return redirect(url_for("exercicio"))
    db.start_exercise(nome)
    flash("Treino iniciado! ⏱️ Boa sorte!", "success")
    return redirect(url_for("exercicio"))


@app.route("/exercicio/finalizar/<page_id>", methods=["POST"])
def finalizar_exercicio(page_id):
    kcal = request.form.get("kcal_estimadas")
    db.finish_exercise(page_id, int(kcal) if kcal else None)
    flash("Treino finalizado! 💪 Bom trabalho!", "success")
    return redirect(url_for("exercicio"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
