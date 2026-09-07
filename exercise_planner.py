"""Plano de treino que reage ao que realmente comeste (hoje ou esta semana),
em vez de mostrar sempre o mesmo treino fixo para o objetivo.

Ideia baseada em "nutrition periodization": a fisiologia do desporto diz que a
alimentação deve ser ajustada à exigência do treino — e o inverso também faz
sentido para um treino recreativo: se comeste pouco (défice grande) ou pouca
proteína, treinar pesado é mais arriscado (mais fadiga, pior recuperação);
se comeste bem, tens mais "combustível" para um treino completo ou mais intenso.
Fontes usadas para calibrar os limiares: TrainingPeaks (nutrition periodization)
e MacroFactor (treino em défice calórico) — ver README."""

from workouts import get_workout_for_goal

TREINO_LEVE = {
    "titulo": "Treino leve de recuperação",
    "duracao": "20-25 min",
    "exercicios": [
        "10 min de caminhada ou mobilidade articular",
        "2x10 agachamento sem peso",
        "2x10 elevações de braço",
        "5 min de alongamentos",
    ],
}


def _percentagens(totals, targets):
    kcal_target = (targets or {}).get("kcal") or 0
    protein_target = (targets or {}).get("protein_g") or 0
    kcal_pct = (totals["kcal"] / kcal_target) if kcal_target else None
    protein_pct = (totals["proteina_g"] / protein_target) if protein_target else None
    return kcal_pct, protein_pct


def plano_diario(objetivo, totals, targets):
    """Decide o treino de hoje com base no que já foi registado hoje."""
    base = get_workout_for_goal(objetivo)

    if not totals or totals.get("kcal", 0) == 0:
        return {
            "nivel": "sem_dados",
            "mensagem": "Ainda não registaste nenhuma refeição hoje — aqui fica o treino base do teu objetivo. "
                        "Regista o que comeste para eu ajustar a intensidade.",
            "workout": base,
        }

    kcal_pct, protein_pct = _percentagens(totals, targets)

    if kcal_pct is not None and (kcal_pct < 0.6 or (protein_pct is not None and protein_pct < 0.5)):
        return {
            "nivel": "leve",
            "mensagem": f"Hoje comeste cerca de {round((kcal_pct or 0) * 100)}% do teu objetivo calórico — "
                        "vamos com algo mais leve, para não sobrecarregar sem combustível suficiente.",
            "workout": TREINO_LEVE,
        }

    if kcal_pct is not None and kcal_pct > 1.15:
        extra = dict(base)
        extra["exercicios"] = base["exercicios"] + ["Finisher: 10 min de cardio extra (aproveita a energia de hoje)"]
        return {
            "nivel": "intenso",
            "mensagem": f"Hoje comeste bem ({round(kcal_pct * 100)}% do objetivo) — tens combustível para um treino mais completo.",
            "workout": extra,
        }

    return {
        "nivel": "normal",
        "mensagem": "A tua alimentação hoje está equilibrada com o teu objetivo — treino normal.",
        "workout": base,
    }


def plano_semanal(objetivo, dias_semana_totais, targets):
    """dias_semana_totais: lista de 7 dicts {kcal, proteina_g} (um por dia, Seg-Dom).
    Decide uma estrutura semanal (treino completo / leve / descanso por dia)."""
    base_titulo = get_workout_for_goal(objetivo)["titulo"]

    dias_com_dados = [d for d in dias_semana_totais if d["kcal"] > 0]
    dias_logados = len(dias_com_dados)

    if dias_logados == 0:
        return {
            "nivel": "sem_dados",
            "mensagem": "Ainda não há refeições registadas esta semana — regista alguns dias para eu montar um plano ajustado.",
            "estrutura": ["Treino leve", "Descanso", "Treino leve", "Descanso", "Treino leve", "Descanso", "Descanso"],
        }

    kcal_target = (targets or {}).get("kcal") or 0
    protein_target = (targets or {}).get("protein_g") or 0
    media_kcal_pct = sum(d["kcal"] / kcal_target for d in dias_com_dados) / dias_logados if kcal_target else 0
    media_protein_pct = sum(d["proteina_g"] / protein_target for d in dias_com_dados) / dias_logados if protein_target else 0

    if dias_logados < 4:
        return {
            "nivel": "inconsistente",
            "mensagem": f"Só registaste refeições em {dias_logados}/7 dias — com poucos dados, vamos com uma "
                        "semana mais leve até teres mais consistência a registar.",
            "estrutura": ["Treino leve", "Descanso", "Treino leve", "Descanso", "Treino leve", "Descanso", "Descanso"],
        }

    if media_kcal_pct < 0.7 or media_protein_pct < 0.5:
        return {
            "nivel": "baixo",
            "mensagem": f"Em média comeste {round(media_kcal_pct * 100)}% do teu objetivo calórico esta semana — "
                        "mantemos os treinos mais leves para não sobrecarregar a recuperação.",
            "estrutura": ["Treino leve", "Descanso", "Treino leve", "Treino leve", "Descanso", "Treino leve", "Descanso"],
        }

    if media_kcal_pct > 1.15:
        return {
            "nivel": "alto",
            "mensagem": f"Em média comeste {round(media_kcal_pct * 100)}% do teu objetivo esta semana — "
                        "tens margem para uma semana mais completa, com um dia extra de treino.",
            "estrutura": [base_titulo, base_titulo, "Descanso", base_titulo, base_titulo, "Cardio extra", "Descanso"],
        }

    return {
        "nivel": "equilibrado",
        "mensagem": "A tua alimentação esteve equilibrada com o teu objetivo esta semana — mantemos um plano completo.",
        "estrutura": [base_titulo, "Descanso", base_titulo, base_titulo, "Descanso", base_titulo, "Descanso"],
    }
