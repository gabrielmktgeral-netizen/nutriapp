"""Lembretes automáticos (Web Push).

Verifica se já passou a hora de uma refeição (ou do exercício) sem estar
registada e envia uma notificação push para todos os dispositivos subscritos.

---------------------------------------------------------------------------
PORQUE É QUE NÃO BASTA UM RELÓGIO DENTRO DO SITE (limitação do Render)
---------------------------------------------------------------------------
* A notificação em si é Web Push: o servidor envia-a ao serviço de push do
  navegador (Google/Mozilla/Apple), que a entrega ao telemóvel através do
  Service Worker (static/sw.js). Isto funciona com o site fechado, o
  separador fechado e o telemóvel fora da app. ✅
* MAS alguém tem de decidir "agora é a hora" e mandar o envio. Até aqui era
  só o APScheduler, que corre DENTRO do processo do site no Render.
* No plano gratuito do Render o serviço adormece após ~15 min sem visitas.
  Adormecido = processo parado = APScheduler parado = nenhum lembrete. ❌
  Num reinício (deploy, falha) perdia-se também a memória do que já tinha
  sido enviado, podendo repetir avisos.

SOLUÇÃO
* Endpoint protegido GET/POST /lembretes/verificar (ver app.py), chamado a
  cada 5 minutos por um agendador externo gratuito (ex: cron-job.org).
  Cada chamada acorda o Render (se estiver a dormir) e corre esta função.
  Como as chamadas são frequentes, o serviço praticamente deixa de adormecer.
* O APScheduler continua ligado como reforço (quando o site está acordado).
* O registo do que já foi enviado hoje é guardado na base de dados (Perfil →
  "Lembretes Enviados"), por isso um reinício não causa avisos repetidos.
* Um cadeado (Lock) impede que o agendador interno e o externo enviem o
  mesmo aviso ao mesmo tempo.

LIMITAÇÕES QUE CONTINUAM A EXISTIR (fora do controlo do código)
* Se o Render estiver mesmo em baixo (falha do serviço), não há envios
  nesse período — o próximo ciclo apanha os lembretes ainda dentro da janela.
* No PC o navegador tem de estar a correr (pode estar sem separadores).
* No iPhone o site tem de estar instalado no ecrã principal (iOS 16.4+).
---------------------------------------------------------------------------
"""
import json
import threading
from datetime import datetime

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

# Janelas (minutos depois da hora definida) em que o aviso pode sair.
# Refeição: mantém o funcionamento que já existia (30-90 min depois).
# Exercício: à hora certa (até 60 min depois, caso o agendador atrase).
JANELA_REFEICAO = (30, 90)
JANELA_TREINO = (0, 60)

TREINO_TITULO = "🏋️ Hora de treinar"
TREINO_CORPO = "Está na hora de fazer o teu exercício de hoje."

# reforço em memória (caso a gravação na base de dados falhe)
_already_sent = set()
_lock = threading.Lock()

# última verificação (para mostrar na página Notificações)
ULTIMA_VERIFICACAO = {"quando": None, "origem": None, "enviados": 0}


def _now():
    return datetime.now(TZ) if TZ else datetime.now()


def _minutos_desde(hora_str, agora):
    try:
        h, m = [int(x) for x in hora_str.split(":")]
    except (ValueError, AttributeError, TypeError):
        return None
    alvo = agora.replace(hour=h, minute=m, second=0, microsecond=0)
    return (agora - alvo).total_seconds() / 60


def _na_janela(hora_str, agora, janela):
    minutos = _minutos_desde(hora_str, agora)
    return minutos is not None and janela[0] <= minutos <= janela[1]


def _ler_enviados(profile, hoje):
    """Devolve o conjunto de lembretes já enviados hoje (guardado no perfil)."""
    try:
        dados = json.loads(profile.get("lembretes_enviados") or "{}")
    except (TypeError, ValueError):
        dados = {}
    if dados.get("data") != hoje:
        return set()
    return set(dados.get("chaves") or [])


def _gravar_enviados(hoje, chaves):
    try:
        db.save_lembretes_enviados(json.dumps({"data": hoje, "chaves": sorted(chaves)}))
    except Exception as exc:  # noqa: BLE001
        print(f"[lembretes] falhou gravar controlo: {exc}", flush=True)


def _enviar_a_todos(subs, titulo, corpo, url="/"):
    enviados = 0
    for s in subs:
        ok, detalhe = send_notification({"endpoint": s["endpoint"], "keys": s["keys"]}, titulo, corpo, url)
        if not ok:
            db.delete_push_subscription(s["endpoint"])
        elif detalhe == "ok":
            enviados += 1
    return enviados


def verificar_lembretes(origem="interno"):
    """Corre uma verificação. Seguro de chamar várias vezes: cada lembrete
    sai no máximo uma vez por dia. Devolve um pequeno resumo (para o log
    e para a resposta do endpoint externo)."""
    resumo = {"ok": True, "origem": origem, "enviados": [], "motivo": ""}
    with _lock:
        try:
            resumo = _verificar(origem, resumo)
        except Exception as exc:  # noqa: BLE001
            print(f"[lembretes] erro na verificação: {exc!r}", flush=True)
            resumo.update(ok=False, motivo=f"erro: {exc}")
        ULTIMA_VERIFICACAO.update(quando=_now(), origem=origem, enviados=len(resumo["enviados"]))
    return resumo


def _verificar(origem, resumo):
    if not db.configured():
        resumo["motivo"] = "base de dados não configurada"
        return resumo
    subs = db.get_push_subscriptions()
    if not subs:
        resumo["motivo"] = "nenhum dispositivo subscrito"
        return resumo
    profile = db.get_profile()
    if not profile:
        resumo["motivo"] = "sem perfil"
        return resumo

    agora = _now()
    hoje = agora.date().isoformat()
    enviados = _ler_enviados(profile, hoje) | {c for (d, c) in _already_sent if d == hoje}

    # 1) o que está "na hora" e ainda não foi avisado — sem pedidos à BD
    refeicoes_candidatas = []
    for tipo, (campo_hora, label) in MEAL_HORAS.items():
        hora_str = profile.get(campo_hora)
        if not hora_str or profile.get(f"pular_lembrete_{tipo}") or tipo in enviados:
            continue
        if _na_janela(hora_str, agora, JANELA_REFEICAO):
            refeicoes_candidatas.append((tipo, label))

    hora_treino = (profile.get("hora_treino") or "").strip()
    treino_candidato = (
        bool(hora_treino)
        and not profile.get("pular_lembrete_treino")
        and "treino" not in enviados
        and _na_janela(hora_treino, agora, JANELA_TREINO)
    )

    if not refeicoes_candidatas and not treino_candidato:
        resumo["motivo"] = "nada para avisar agora"
        return resumo

    novos = set()

    # 2) refeições: só avisa se ainda não estiver registada (inclui "Não comi")
    if refeicoes_candidatas:
        registadas = {m["tipo"] for m in db.get_meals_for_day(hoje)}
        for tipo, label in refeicoes_candidatas:
            if tipo in registadas:
                continue
            _enviar_a_todos(subs, f"🍽️ {label}", f"Ainda não registaste o {label.lower()} de hoje.", "/")
            novos.add(tipo)

    # 3) exercício: só avisa se ainda não houver treino registado hoje
    if treino_candidato and not db.get_exercise_between(hoje, hoje):
        _enviar_a_todos(subs, TREINO_TITULO, TREINO_CORPO, "/exercicio")
        novos.add("treino")

    if novos:
        for c in novos:
            _already_sent.add((hoje, c))
        _gravar_enviados(hoje, enviados | novos)
        print(f"[lembretes] ({origem}) enviados: {sorted(novos)}", flush=True)
    resumo["enviados"] = sorted(novos)
    if not novos:
        resumo["motivo"] = "já estava tudo registado"
    return resumo
