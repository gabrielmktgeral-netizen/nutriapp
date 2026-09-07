import os
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

import data_store as db
import nutrition_calc as nc
from meal_parser import parse_meal_text
from food_data import lookup as food_lookup

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-troca-isto")

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def week_bounds(ref_date):
    monday = ref_date - timedelta(days=ref_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


@app.context_processor
def inject_globals():
    return {"notion_configured": db.configured(), "using_notion": db.USING_NOTION, "backend_name": db.BACKEND_NAME}


@app.route("/")
def index():
    profile = db.get_profile() if db.configured() else None
    if not profile or not profile.get("idade"):
        return redirect(url_for("onboarding"))

    today = date.today()
    today_iso = today.isoformat()
    meals_today = db.get_meals_for_day(today_iso)

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

    monday, sunday = week_bounds(today)
    week_meals = db.get_meals_between(monday.isoformat(), sunday.isoformat())
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

    return render_template(
        "index.html", profile=profile, totals=totals, targets=targets,
        meals_by_type=meals_by_type, meal_labels=nc.MEAL_LABELS,
        week_summary=week_summary, today=today_iso,
        restante_kcal=restante_kcal, restante_prot=restante_prot,
        goal_label=nc.GOAL_LABELS.get(profile.get("objetivo"), ""),
    )


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
        }
        db.save_profile(data)
        flash("Perfil guardado! 🎉", "success")
        return redirect(url_for("index"))

    profile = db.get_profile() if db.configured() else None
    return render_template(
        "onboarding.html", profile=profile,
        goal_labels=nc.GOAL_LABELS, activity_labels=nc.ACTIVITY_LABELS,
    )


@app.route("/registar-refeicao", methods=["GET", "POST"])
def registar_refeicao():
    tipo_padrao = request.args.get("tipo", "almoco")
    resultado = None
    if request.method == "POST":
        tipo = request.form["tipo"]
        texto = request.form["texto"].strip()
        if texto:
            total, itens = parse_meal_text(texto)
            db.add_meal(date.today().isoformat(), tipo, texto,
                        total["kcal"], total["proteina_g"], total["hidratos_g"], total["gordura_g"])
            resultado = {"total": total, "itens": itens}
            flash("Refeição registada! ✅", "success")
        tipo_padrao = tipo

    return render_template("registar_refeicao.html", tipo_padrao=tipo_padrao,
                            meal_labels=nc.MEAL_LABELS, resultado=resultado)


@app.route("/despensa", methods=["GET", "POST"])
def despensa():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        quantidade = request.form.get("quantidade", "").strip()
        if nome:
            db.add_pantry_item(nome, quantidade)
            flash(f"'{nome}' adicionado à despensa.", "success")
        return redirect(url_for("despensa"))

    items = db.get_pantry() if db.configured() else []
    return render_template("despensa.html", items=items)


@app.route("/despensa/remover/<page_id>", methods=["POST"])
def remover_despensa(page_id):
    db.delete_pantry_item(page_id)
    flash("Item removido.", "success")
    return redirect(url_for("despensa"))


@app.route("/sugestao")
def sugestao():
    profile = db.get_profile()
    targets = nc.macro_targets(profile) if profile else None
    today_iso = date.today().isoformat()
    meals_today = db.get_meals_for_day(today_iso)
    consumido_kcal = sum(m["kcal"] for m in meals_today)
    consumido_prot = sum(m["proteina_g"] for m in meals_today)

    restante_kcal = round((targets["kcal"] if targets else 0) - consumido_kcal)
    restante_prot = round((targets["protein_g"] if targets else 0) - consumido_prot)

    pantry = db.get_pantry()
    sugestoes = []
    for item in pantry:
        vals = food_lookup(item["nome"])
        if vals:
            kcal100, prot100, carb100, fat100 = vals
            sugestoes.append({"nome": item["nome"], "kcal_100g": kcal100, "proteina_100g": prot100})
    # ordena por mais proteína por caloria, prioriza quem ajuda a fechar o objetivo de proteína
    sugestoes.sort(key=lambda x: -(x["proteina_100g"] / max(x["kcal_100g"], 1)))

    return render_template("sugestao.html", restante_kcal=restante_kcal, restante_prot=restante_prot,
                            sugestoes=sugestoes[:6], pantry=pantry)


@app.route("/peso", methods=["GET", "POST"])
def peso():
    if request.method == "POST":
        peso_kg = float(request.form["peso_kg"])
        db.add_weight(date.today().isoformat(), peso_kg)
        db.save_profile({**db.get_profile(), "peso_kg": peso_kg})
        flash("Peso registado.", "success")
        return redirect(url_for("peso"))

    history = db.get_weight_history(20) if db.configured() else []
    return render_template("peso.html", history=history)


@app.route("/exercicio", methods=["GET", "POST"])
def exercicio():
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
            flash("Exercício registado! 💪", "success")
        return redirect(url_for("exercicio"))

    today = date.today()
    monday, sunday = week_bounds(today)
    week_ex = db.get_exercise_between(monday.isoformat(), sunday.isoformat()) if db.configured() else []
    return render_template("exercicio.html", week_ex=week_ex)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
