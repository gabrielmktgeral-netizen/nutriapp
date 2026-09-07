"""Sugestões de treino baseadas no objetivo escolhido no perfil."""
import re
from urllib.parse import quote_plus

WORKOUTS_BY_GOAL = {
    "perder_peso": {
        "titulo": "Cardio + full body",
        "duracao": "35-40 min",
        "exercicios": [
            "10 min de caminhada rápida ou bicicleta (aquecimento)",
            "3x15 agachamentos",
            "3x12 flexões (ou joelhos apoiados)",
            "3x15 elevações de perna",
            "10 min de cardio contínuo (final)",
        ],
    },
    "perder_gordura": {
        "titulo": "Treino de força + finisher cardio",
        "duracao": "40-45 min",
        "exercicios": [
            "3x10 agachamento com peso",
            "3x10 remada (elástico ou halteres)",
            "3x10 press militar",
            "3x12 afundos",
            "8 min de HIIT no final",
        ],
    },
    "ganhar_massa": {
        "titulo": "Treino de força — hipertrofia",
        "duracao": "45-55 min",
        "exercicios": [
            "4x8 agachamento",
            "4x8 supino ou flexões com peso",
            "4x8 remada curvada",
            "3x10 desenvolvimento de ombros",
            "3x12 rosca bíceps + tríceps",
        ],
    },
    "aumentar_peso": {
        "titulo": "Treino de força — foco em progressão de carga",
        "duracao": "45-55 min",
        "exercicios": [
            "4x6-8 agachamento (carga progressiva)",
            "4x6-8 supino ou press",
            "4x6-8 remada",
            "3x10 elevações laterais",
            "Termina sem cardio extra — foco em comer bem depois",
        ],
    },
    "manter_peso": {
        "titulo": "Treino equilibrado full body",
        "duracao": "35-40 min",
        "exercicios": [
            "3x12 agachamentos",
            "3x12 flexões",
            "3x12 remada",
            "3x15 prancha (30-45 seg)",
        ],
    },
    "melhorar_condicao": {
        "titulo": "Circuito de condição física",
        "duracao": "30 min",
        "exercicios": [
            "5 min de aquecimento",
            "4 rondas: 30 seg burpees + 30 seg descanso",
            "4 rondas: 30 seg mountain climbers + 30 seg descanso",
            "4 rondas: 30 seg jumping jacks + 30 seg descanso",
        ],
    },
    "recomposicao": {
        "titulo": "Treino de força moderado",
        "duracao": "40-45 min",
        "exercicios": [
            "3x10 agachamento",
            "3x10 supino ou flexões",
            "3x10 remada",
            "3x12 prancha + elevações de perna",
        ],
    },
}


def get_workout_for_goal(objetivo):
    return WORKOUTS_BY_GOAL.get(objetivo, WORKOUTS_BY_GOAL["manter_peso"])


_PREFIX_RE = re.compile(r"^\s*\d+x[\d\-]+\s*", flags=re.IGNORECASE)
_PAREN_RE = re.compile(r"\(.*?\)")


def nome_exercicio_limpo(texto_exercicio: str) -> str:
    """Remove '3x10 ' e parênteses, deixando só o nome do exercício, para pesquisar um vídeo."""
    t = _PREFIX_RE.sub("", texto_exercicio)
    t = _PAREN_RE.sub("", t)
    t = t.split(" ou ")[0]  # fica só com a primeira opção quando há alternativa
    return t.strip(" .")


def youtube_search_url(texto_exercicio: str) -> str:
    nome = nome_exercicio_limpo(texto_exercicio)
    query = quote_plus(f"como fazer {nome} técnica correta")
    return f"https://www.youtube.com/results?search_query={query}"
