"""Envio do relatório. Cada canal implementa a mesma função enviar(texto, anexo)."""

import json
import logging
import mimetypes
import urllib.request
import uuid
from pathlib import Path

from .config import Config

log = logging.getLogger(__name__)


class FalhaNoEnvio(Exception):
    """O canal de envio recusou ou não respondeu."""


def _post(url: str, corpo: bytes, tipo: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(url, data=corpo, headers={"Content-Type": tipo}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = resp.read()
            return json.loads(dados) if dados else {}
    except Exception as exc:  # erro de rede, HTTP 4xx/5xx, JSON inválido
        raise FalhaNoEnvio(str(exc)) from exc


def _multipart(campos: dict, arquivo: Path) -> tuple[bytes, str]:
    fronteira = uuid.uuid4().hex
    partes = []
    for nome, valor in campos.items():
        partes.append(f'--{fronteira}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'.encode())
    tipo = mimetypes.guess_type(arquivo.name)[0] or "application/octet-stream"
    partes.append(
        f'--{fronteira}\r\nContent-Disposition: form-data; name="document"; filename="{arquivo.name}"\r\n'
        f"Content-Type: {tipo}\r\n\r\n".encode() + arquivo.read_bytes() + b"\r\n"
    )
    partes.append(f"--{fronteira}--\r\n".encode())
    return b"".join(partes), f"multipart/form-data; boundary={fronteira}"


def enviar(cfg: Config, texto: str, anexo: Path) -> None:
    canal = cfg.notificador
    if canal == "console":
        print("\n" + texto + f"\n(anexo: {anexo})\n")
        return

    if canal == "telegram":
        if not (cfg.telegram_token and cfg.telegram_chat_id):
            raise FalhaNoEnvio("defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID")
        corpo, tipo = _multipart({"chat_id": cfg.telegram_chat_id, "caption": texto[:1000]}, anexo)
        resposta = _post(f"https://api.telegram.org/bot{cfg.telegram_token}/sendDocument", corpo, tipo)
        if not resposta.get("ok"):
            raise FalhaNoEnvio(f"Telegram recusou: {resposta.get('description')}")
        log.info("Relatório enviado pelo Telegram")
        return

    if canal == "webhook":
        if not cfg.webhook_url:
            raise FalhaNoEnvio("defina WEBHOOK_URL")
        _post(cfg.webhook_url, json.dumps({"text": texto, "arquivo": anexo.name}).encode(), "application/json")
        log.info("Relatório enviado para o webhook")
        return

    raise FalhaNoEnvio(f"canal desconhecido: {canal} (use console, telegram ou webhook)")
