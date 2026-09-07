"""Lembretes automáticos: de vez em quando verifica se já passou a hora
habitual de uma refeição (ou de treino) sem estar registada, e envia uma
notificação push. Corre dentro do próprio processo do site — não precisa de
nenhum serviço externo."""
from datetime import date, datetime

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Europe/Lisbon")
except Exception:
    TZ = None

import data_store as db
from push import send_notification

MEAL_HORAS = {
    "pequeno_almoco": ("hora_pequeno_almoco", "Pequeno-almoço"),
    "almoco": ("hora_almoco", "Almoço"),
    "lanche": ("hora_lanche", "Lanche"),
    "jantar": ("hora_jantar", "Jantar"),
}

# guarda o que já foi notificado nesta execução do servidor, para não repetir
_already_sent = set()


def _now():
    return datetime.now(TZ) if TZ else datetime.now()


def _minutos_desde(hora_str, agora):
    try:
        h, m = [int(x) for x in hora_str.split(":")]
    except (ValueError, AttributeError, TypeError):
        return None
    alvo = agora.replace(hour=h, minute=m, second=0, microsecond=0)
    return (agora - alvo).total_seconds() / 60


def _enviar_a_todos(titulo, corpo, url="/"):
    subs = db.get_push_subscriptions()
    for s in subs:
        ok = send_notification({"endpoint": s["endpoint"], "keys": s["keys"]}, titulo, corpo, url)
        if not ok:
            db.delete_push_subscription(s["endpoint"])
    return len(subs)


def verificar_lembretes():
    """Chamado periodicamente pelo agendador. Não faz nada se não houver
    ninguém subscrito ou perfil configurado."""
    if not db.configured():
        return
    subs = db.get_push_subscriptions()
    if not subs:
        return

    profile = db.get_profile()
    if not profile:
        return

    agora = _now()
    hoje = date.today().isoformat()
    meals_hoje = {m["tipo"]: m for m in db.get_meals_for_day(hoje)}

    for tipo, (campo_hora, label) in MEAL_HORAS.items():
        hora_str = profile.get(campo_hora)
        if not hora_str or tipo in meals_hoje:
            continue
        minutos = _minutos_desde(hora_str, agora)
        if minutos is not None and 30 <= minutos <= 90:
            chave = (hoje, tipo)
            if chave in _already_sent:
                continue
            _already_sent.add(chave)
            _enviar_a_todos(f"🍽️ {label}", f"Ainda não registaste o {label.lower()} de hoje.", "/")

    hora_treino = (profile.get("hora_treino") or "").strip()
    if hora_treino:
        treinos_hoje = db.get_exercise_between(hoje, hoje)
        if not treinos_hoje:
            minutos = _minutos_desde(hora_treino, agora)
            if minutos is not None and 0 <= minutos <= 45:
                chave = (hoje, "treino")
                if chave not in _already_sent:
                    _already_sent.add(chave)
                    _enviar_a_todos("💪 Hora de treino", "É a tua hora habitual de treino — vamos a isto?", "/exercicio")
