"""Sugestões de treino baseadas no objetivo escolhido no perfil.

Em vez de um único treino fixo por objetivo, cada objetivo tem 2-3 variantes
que se alternam ao longo da semana (dia A / dia B / dia C) — inspirado em
como apps de treino em casa organizam a semana por divisão de grupos
musculares ou tipo de estímulo (ex: força vs. cardio vs. mobilidade),
em vez de repetir sempre o mesmo treino."""
import re
from urllib.parse import quote_plus

WORKOUTS_BY_GOAL = {
    "perder_peso": [
        {
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
        {
            "titulo": "Superior + core",
            "duracao": "30-35 min",
            "exercicios": [
                "5 min de aquecimento articular",
                "3x12 flexões (ou joelhos apoiados)",
                "3x12 remada (elástico ou halteres)",
                "3x10 press militar",
                "3x30 seg prancha",
            ],
        },
        {
            "titulo": "Funcional completo",
            "duracao": "35 min",
            "exercicios": [
                "5 min de aquecimento",
                "3x12 afundos alternados",
                "3x15 mountain climbers",
                "3x12 elevações laterais",
                "10 min de dança ou cardio à escolha",
            ],
        },
    ],
    "perder_gordura": [
        {
            "titulo": "Força — membros inferiores + finisher",
            "duracao": "40-45 min",
            "exercicios": [
                "3x10 agachamento com peso",
                "3x12 afundos",
                "3x15 elevação de gémeos",
                "3x15 elevações de perna",
                "8 min de HIIT no final",
            ],
        },
        {
            "titulo": "Força — membros superiores + finisher",
            "duracao": "40-45 min",
            "exercicios": [
                "3x10 remada (elástico ou halteres)",
                "3x10 press militar",
                "3x10 flexões",
                "3x12 rosca bíceps",
                "8 min de HIIT no final",
            ],
        },
    ],
    "ganhar_massa": [
        {
            "titulo": "Push — peito, ombros, tríceps",
            "duracao": "45-55 min",
            "exercicios": [
                "4x8 supino ou flexões com peso",
                "3x10 desenvolvimento de ombros",
                "3x10 elevações laterais",
                "3x12 extensão de tríceps",
            ],
        },
        {
            "titulo": "Pull — costas, bíceps",
            "duracao": "45-55 min",
            "exercicios": [
                "4x8 remada curvada",
                "3x10 puxada (elástico ou barra)",
                "3x12 rosca bíceps",
                "3x30 seg prancha",
            ],
        },
        {
            "titulo": "Pernas — quadríceps, posterior, glúteos",
            "duracao": "45-55 min",
            "exercicios": [
                "4x8 agachamento",
                "3x10 afundos",
                "3x12 elevação de gémeos",
                "3x15 ponte de glúteos",
            ],
        },
    ],
    "aumentar_peso": [
        {
            "titulo": "Push — foco em progressão de carga",
            "duracao": "45-55 min",
            "exercicios": [
                "4x6-8 supino ou press (carga progressiva)",
                "4x6-8 desenvolvimento de ombros",
                "3x8 extensão de tríceps",
                "Termina sem cardio extra — foco em comer bem depois",
            ],
        },
        {
            "titulo": "Pull — foco em progressão de carga",
            "duracao": "45-55 min",
            "exercicios": [
                "4x6-8 remada (carga progressiva)",
                "4x6-8 puxada",
                "3x8 rosca bíceps",
                "Termina sem cardio extra — foco em comer bem depois",
            ],
        },
        {
            "titulo": "Pernas — foco em progressão de carga",
            "duracao": "45-55 min",
            "exercicios": [
                "4x6-8 agachamento (carga progressiva)",
                "4x6-8 afundos",
                "3x10 elevação de gémeos",
                "Termina sem cardio extra — foco em comer bem depois",
            ],
        },
    ],
    "manter_peso": [
        {
            "titulo": "Funcional total-body",
            "duracao": "35-40 min",
            "exercicios": [
                "3x12 agachamentos",
                "3x12 flexões",
                "3x12 remada",
                "3x30-45 seg prancha",
            ],
        },
        {
            "titulo": "Cardio à escolha",
            "duracao": "30 min",
            "exercicios": [
                "5 min de aquecimento",
                "20 min de cardio contínuo (caminhada, corrida, bicicleta)",
                "5 min de alongamentos",
            ],
        },
        {
            "titulo": "Mobilidade + core",
            "duracao": "30 min",
            "exercicios": [
                "15 min de mobilidade articular / yoga",
                "3x30-45 seg prancha",
                "3x15 elevações de perna",
            ],
        },
    ],
    "melhorar_condicao": [
        {
            "titulo": "Circuito intervalado (HIIT)",
            "duracao": "30 min",
            "exercicios": [
                "5 min de aquecimento",
                "4 rondas: 30 seg burpees + 30 seg descanso",
                "4 rondas: 30 seg mountain climbers + 30 seg descanso",
                "4 rondas: 30 seg jumping jacks + 30 seg descanso",
            ],
        },
        {
            "titulo": "Cardio contínuo",
            "duracao": "30-35 min",
            "exercicios": [
                "5 min de aquecimento",
                "25 min de corrida, bicicleta ou caminhada rápida a ritmo constante",
                "5 min de alongamentos",
            ],
        },
        {
            "titulo": "Mobilidade + core",
            "duracao": "25 min",
            "exercicios": [
                "15 min de mobilidade articular / yoga",
                "3x30-45 seg prancha",
                "3x15 elevações de perna",
            ],
        },
    ],
    "recomposicao": [
        {
            "titulo": "Push moderado — peito, ombros, tríceps",
            "duracao": "40-45 min",
            "exercicios": [
                "3x10 supino ou flexões",
                "3x10 press militar",
                "3x12 extensão de tríceps",
            ],
        },
        {
            "titulo": "Pull moderado — costas, bíceps",
            "duracao": "40-45 min",
            "exercicios": [
                "3x10 remada",
                "3x10 puxada",
                "3x12 rosca bíceps",
            ],
        },
        {
            "titulo": "Pernas moderado + core",
            "duracao": "40-45 min",
            "exercicios": [
                "3x10 agachamento",
                "3x10 afundos",
                "3x30 seg prancha + elevações de perna",
            ],
        },
    ],
}


def get_variants_for_goal(objetivo):
    return WORKOUTS_BY_GOAL.get(objetivo, WORKOUTS_BY_GOAL["manter_peso"])


def get_workout_for_goal(objetivo, indice=0):
    """Devolve UMA variante do treino do objetivo. `indice` escolhe qual
    (por exemplo, o dia da semana) — sem índice devolve sempre a primeira,
    por compatibilidade com quem só quer 'o treino base'."""
    variantes = get_variants_for_goal(objetivo)
    return variantes[indice % len(variantes)]


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
