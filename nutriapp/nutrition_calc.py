"""Cálculos nutricionais (BMR, TDEE, macros) - independentes da base de dados."""

ACTIVITY_FACTORS = {
    "sedentario": 1.2,
    "leve": 1.375,
    "moderado": 1.55,
    "ativo": 1.725,
    "muito_ativo": 1.9,
}

GOAL_ADJUST = {
    "perder_peso": -0.20,
    "perder_gordura": -0.15,
    "ganhar_massa": 0.12,
    "aumentar_peso": 0.15,
    "manter_peso": 0.0,
    "melhorar_condicao": 0.0,
    "recomposicao": -0.05,
}

GOAL_LABELS = {
    "perder_peso": "Perder peso",
    "perder_gordura": "Perder gordura",
    "ganhar_massa": "Ganhar massa muscular",
    "aumentar_peso": "Aumentar peso",
    "manter_peso": "Manter peso",
    "melhorar_condicao": "Melhorar condição física",
    "recomposicao": "Recomposição corporal",
}

ACTIVITY_LABELS = {
    "sedentario": "Sedentário",
    "leve": "Leve (1-3x/semana)",
    "moderado": "Moderado (3-5x/semana)",
    "ativo": "Ativo (6-7x/semana)",
    "muito_ativo": "Muito ativo (atleta)",
}

MEAL_LABELS = {
    "pequeno_almoco": ("🍳", "Pequeno-almoço"),
    "almoco": ("🍽️", "Almoço"),
    "lanche": ("🥪", "Lanche"),
    "jantar": ("🍗", "Jantar"),
}


def bmr(idade, sexo, altura_cm, peso_kg):
    if not (idade and sexo and altura_cm and peso_kg):
        return None
    base = 10 * peso_kg + 6.25 * altura_cm - 5 * idade
    return base + 5 if sexo == "M" else base - 161


def tdee(idade, sexo, altura_cm, peso_kg, nivel_atividade):
    b = bmr(idade, sexo, altura_cm, peso_kg)
    if b is None:
        return None
    factor = ACTIVITY_FACTORS.get(nivel_atividade, 1.375)
    return b * factor


def calorie_target(idade, sexo, altura_cm, peso_kg, nivel_atividade, objetivo):
    t = tdee(idade, sexo, altura_cm, peso_kg, nivel_atividade)
    if t is None:
        return None
    adjust = GOAL_ADJUST.get(objetivo, 0.0)
    return round(t * (1 + adjust))


def macro_targets(profile: dict):
    """profile: dict with idade, sexo, altura_cm, peso_kg, nivel_atividade, objetivo"""
    kcal = calorie_target(
        profile.get("idade"), profile.get("sexo"), profile.get("altura_cm"),
        profile.get("peso_kg"), profile.get("nivel_atividade"), profile.get("objetivo"),
    )
    peso_kg = profile.get("peso_kg")
    if kcal is None or not peso_kg:
        return None
    objetivo = profile.get("objetivo")
    protein_per_kg = 2.0 if objetivo in ("ganhar_massa", "recomposicao", "perder_gordura") else 1.6
    protein_g = round(peso_kg * protein_per_kg)
    protein_kcal = protein_g * 4
    fat_kcal = round(kcal * 0.28)
    fat_g = round(fat_kcal / 9)
    carbs_kcal = max(kcal - protein_kcal - fat_kcal, 0)
    carbs_g = round(carbs_kcal / 4)
    return {"kcal": kcal, "protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g}
