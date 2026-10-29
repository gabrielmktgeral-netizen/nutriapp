"""Login único da MONDAY para a NutriApp (OAuth 2.1 + PKCE, servidor = Supabase Auth).

Como funciona:
- Sem sessão, qualquer página manda o browser para a MONDAY (/sso/entrar).
- A MONDAY confirma quem és (ou pede login) e devolve um código a /sso/callback.
- O servidor troca o código por tokens e guarda-os no cookie de sessão (assinado, HttpOnly).
- Em cada pedido, o token é confirmado junto do cérebro da MONDAY (jarvis/quem):
  token válido + sessão ainda ativa + conta do dono. Cache de 30 s.
- A MONDAY (servidor) entra como serviço com o cabeçalho x-servico (segredo NUTRI_SERVICO).

Variáveis de ambiente (Render):
  MONDAY_CLIENTE  client_id desta app no Supabase Auth (não é segredo)
  NUTRI_SERVICO   chave só para o servidor da MONDAY (segredo)
  SECRET_KEY      assina o cookie de sessão (segredo)
"""
import base64
import hashlib
import hmac
import os
import secrets
import time
from urllib.parse import urlencode, urlparse

import requests
from flask import abort, jsonify, redirect, request, session

SUPA = "https://obxaqlempjyweraiaynr.supabase.co"
PUB = "sb_publishable_bzEOvCVmmI3nKGzitOSRPQ_3Tw81Q9Y"  # chave pública
JARVIS = SUPA + "/functions/v1/jarvis"
MONDAY = "https://monday-gabriel.netlify.app/"
REDIRECT = os.environ.get("MONDAY_REDIRECT", "https://nutriapp-rtwj.onrender.com/sso/callback")

# Rotas que não precisam de sessão (não mostram dados pessoais).
PUBLICAS = ("/static/", "/sso/", "/sw.js", "/saude", "/favicon.ico", "/manifest.json",
            # chamado pelo agendador externo; protegido pela sua própria chave (LEMBRETES_CHAVE)
            "/lembretes/verificar")

_cache = {}  # token -> (instante, ok)


def _cliente():
    return os.environ.get("MONDAY_CLIENTE", "").strip()


def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _token_ok(token):
    agora = time.time()
    c = _cache.get(token)
    if c and agora - c[0] < 30:
        return c[1]
    try:
        r = requests.get(JARVIS + "/quem", headers={"Authorization": "Bearer " + token}, timeout=10)
        ok = r.status_code == 200
    except requests.RequestException:
        ok = False  # sem confirmação = sem acesso
    if len(_cache) > 200:
        _cache.clear()
    _cache[token] = (agora, ok)
    return ok


def _pedir_token(campos):
    campos = dict(campos, client_id=_cliente())
    r = requests.post(SUPA + "/auth/v1/oauth/token", data=campos, headers={"apikey": PUB}, timeout=15)
    j = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
    if r.status_code != 200 or not j.get("access_token"):
        raise RuntimeError(j.get("error_description") or j.get("error") or f"Erro {r.status_code}")
    session["sso"] = {
        "a": j["access_token"],
        "r": j.get("refresh_token", ""),
        "e": int(time.time()) + int(j.get("expires_in") or 3600),
    }
    session.permanent = True
    return session["sso"]


def _token_atual():
    t = session.get("sso")
    if not t:
        return None
    if t["e"] - time.time() > 60:
        return t["a"]
    if not t.get("r"):
        return None
    try:
        return _pedir_token({"grant_type": "refresh_token", "refresh_token": t["r"]})["a"]
    except Exception:
        session.pop("sso", None)
        return None


def _e_servico():
    chave = os.environ.get("NUTRI_SERVICO", "")
    dado = request.headers.get("x-servico", "")
    return bool(chave) and hmac.compare_digest(chave, dado)


def _quer_json():
    aceita = request.headers.get("accept", "")
    if "text/html" in aceita:
        return False  # navegação normal (página ou formulário): vai pela MONDAY
    return request.is_json or "application/json" in aceita or request.method != "GET"


def ligar(app):
    """Liga o login único à app Flask."""
    sk = os.environ.get("SECRET_KEY", "")
    if not sk or sk == "dev-secret-troca-isto":
        # Sem segredo definido: usa um aleatório (as sessões caem quando o servidor reinicia).
        app.secret_key = secrets.token_hex(32)
    app.config.update(
        SESSION_COOKIE_SECURE=not app.debug,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 30,
    )

    @app.before_request
    def _exigir_sessao():
        p = request.path
        if p in PUBLICAS or any(p.startswith(x) for x in PUBLICAS if x.endswith("/")):
            return None
        if _e_servico():
            return None
        if not _cliente():
            abort(503, "Falta configurar MONDAY_CLIENTE")
        t = _token_atual()
        if t and _token_ok(t):
            return None
        session.pop("sso", None)
        if _quer_json():
            return jsonify({"erro": "Sessão inválida ou terminada", "sessao": False}), 401
        voltar = request.full_path.rstrip("?") if request.method == "GET" else "/"
        return redirect("/sso/entrar?" + urlencode({"voltar": voltar}))

    @app.route("/saude")
    def saude():
        return "ok", 200, {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"}

    @app.route("/sso/entrar")
    def sso_entrar():
        voltar = request.args.get("voltar", "/")
        if not voltar.startswith("/") or voltar.startswith("//"):
            voltar = "/"  # só caminhos desta app (sem saltos para outros sites)
        verificador = _b64(secrets.token_bytes(48))
        estado = _b64(secrets.token_bytes(24))
        session["sso_pkce"] = {"v": verificador, "s": estado, "voltar": voltar}
        q = {
            "response_type": "code",
            "client_id": _cliente(),
            "redirect_uri": REDIRECT,
            "scope": "openid email profile",
            "state": estado,
            "code_challenge": _b64(hashlib.sha256(verificador.encode()).digest()),
            "code_challenge_method": "S256",
        }
        return redirect(SUPA + "/auth/v1/oauth/authorize?" + urlencode(q))

    @app.route("/sso/callback")
    def sso_callback():
        p = session.pop("sso_pkce", None)
        if request.args.get("error"):
            return f"Entrada recusada: {request.args.get('error_description') or request.args.get('error')}", 403
        if not p or not request.args.get("code") or not hmac.compare_digest(p["s"], request.args.get("state", "")):
            return redirect("/sso/entrar")
        try:
            t = _pedir_token({
                "grant_type": "authorization_code",
                "code": request.args["code"],
                "redirect_uri": REDIRECT,
                "code_verifier": p["v"],
            })
        except Exception as e:
            return f"Não consegui entrar: {e}", 502
        lig = request.args.get("monday_ligacao", "")
        if lig:
            try:
                requests.post(JARVIS + "/confirmar", json={"ligacao": lig},
                              headers={"Authorization": "Bearer " + t["a"]}, timeout=10)
            except requests.RequestException:
                pass
        voltar = p.get("voltar") or "/"
        if urlparse(voltar).netloc:
            voltar = "/"
        return redirect(voltar)

    @app.route("/sso/sair")
    def sso_sair():
        t = session.pop("sso", None)
        if t:
            try:
                requests.post(SUPA + "/auth/v1/logout?scope=local", timeout=10,
                              headers={"Authorization": "Bearer " + t["a"], "apikey": PUB})
            except requests.RequestException:
                pass
        return redirect(MONDAY)
