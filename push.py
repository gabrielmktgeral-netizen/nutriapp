"""Notificações push (Web Push) — avisa no telemóvel mesmo com o site fechado
(ex: "ainda não registaste o almoço", "hora de treino").

Funciona em Android em qualquer navegador. No iPhone só depois de
adicionares o site ao ecrã principal (Partilhar → Adicionar ao ecrã principal).

Não precisas de configurar nada para testar: se não houver chaves VAPID
configuradas (env vars), geram-se automaticamente e guardam-se em
data/vapid_keys.json — tal como o resto do modo de teste local.
"""
import base64
import json
import os

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pywebpush import webpush, WebPushException

_LOCAL_KEY_FILE = os.path.join(os.path.dirname(__file__), "data", "vapid_keys.json")
VAPID_SUB = os.environ.get("VAPID_SUB", "mailto:testeeeclaude1@gmail.com")

_keys_cache = None


def _generate_keys():
    key = ec.generate_private_key(ec.SECP256R1())
    priv_bytes = key.private_numbers().private_value.to_bytes(32, "big")
    priv_b64 = base64.urlsafe_b64encode(priv_bytes).rstrip(b"=").decode()
    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()
    return priv_b64, pub_b64


def _load_keys():
    global _keys_cache
    if _keys_cache:
        return _keys_cache

    env_priv = os.environ.get("VAPID_PRIVATE_KEY")
    env_pub = os.environ.get("VAPID_PUBLIC_KEY")
    if env_priv and env_pub:
        _keys_cache = (env_priv, env_pub)
        return _keys_cache

    if os.path.exists(_LOCAL_KEY_FILE):
        with open(_LOCAL_KEY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _keys_cache = (data["private"], data["public"])
            return _keys_cache

    priv, pub = _generate_keys()
    os.makedirs(os.path.dirname(_LOCAL_KEY_FILE), exist_ok=True)
    with open(_LOCAL_KEY_FILE, "w", encoding="utf-8") as f:
        json.dump({"private": priv, "public": pub}, f)
    _keys_cache = (priv, pub)
    return _keys_cache


def get_public_key():
    return _load_keys()[1]


def send_notification(subscription_info, title, body, url="/"):
    """Envia uma notificação. Devolve False se a subscrição já não é válida
    (expirou ou o utilizador desativou no navegador) — nesse caso deve ser
    removida da base de dados."""
    priv, _ = _load_keys()
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body, "url": url}),
            vapid_private_key=priv,
            vapid_claims={"sub": VAPID_SUB},
        )
        return True
    except WebPushException as ex:
        status = getattr(ex.response, "status_code", None)
        if status in (404, 410):
            return False
        return True
    except Exception:
        # erro de rede ou outro problema temporário — não remove a subscrição
        return True
