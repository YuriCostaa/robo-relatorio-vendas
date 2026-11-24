"""Configuração do robô, lida de variáveis de ambiente (ou de um arquivo .env)."""

import os
from dataclasses import dataclass
from pathlib import Path


def carregar_env(caminho: Path = Path(".env")) -> None:
    """Lê um .env simples (CHAVE=valor) sem sobrescrever variáveis já definidas."""
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            chave, valor = linha.split("=", 1)
            os.environ.setdefault(chave.strip(), valor.strip().strip('"'))


@dataclass(frozen=True)
class Config:
    portal_url: str
    usuario: str
    senha: str
    mes: str
    pasta_saida: Path
    notificador: str            # console | telegram | webhook
    headless: bool
    navegador_path: str | None  # caminho de um Chrome já instalado (opcional)
    timeout_ms: int
    tentativas: int
    telegram_token: str | None
    telegram_chat_id: str | None
    webhook_url: str | None

    @classmethod
    def do_ambiente(cls, mes: str | None = None) -> "Config":
        e = os.environ.get
        return cls(
            portal_url=e("PORTAL_URL", "http://127.0.0.1:8765/index.html"),
            usuario=e("PORTAL_USUARIO", "demo"),
            senha=e("PORTAL_SENHA", "demo123"),
            mes=mes or e("RELATORIO_MES", "2026-11"),
            pasta_saida=Path(e("PASTA_SAIDA", "saida")),
            notificador=e("NOTIFICADOR", "console").lower(),
            headless=e("HEADLESS", "true").lower() != "false",
            navegador_path=e("NAVEGADOR_PATH") or None,
            timeout_ms=int(e("TIMEOUT_MS", "30000")),
            tentativas=int(e("TENTATIVAS", "3")),
            telegram_token=e("TELEGRAM_TOKEN"),
            telegram_chat_id=e("TELEGRAM_CHAT_ID"),
            webhook_url=e("WEBHOOK_URL"),
        )
