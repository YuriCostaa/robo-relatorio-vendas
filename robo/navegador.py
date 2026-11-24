"""Parte do robô que abre o navegador, faz login no portal e baixa a planilha."""

import logging
import time
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .config import Config

log = logging.getLogger(__name__)


class FalhaNoNavegador(Exception):
    """O navegador não abriu ou o fluxo no portal não pôde ser concluído."""


def baixar_planilha(cfg: Config) -> Path:
    """Tenta baixar a planilha até cfg.tentativas vezes e devolve o caminho do arquivo salvo."""
    ultima_falha = None
    for tentativa in range(1, cfg.tentativas + 1):
        try:
            log.info("Tentativa %d de %d de baixar a planilha de %s", tentativa, cfg.tentativas, cfg.mes)
            return _baixar(cfg)
        except (PlaywrightError, FalhaNoNavegador) as exc:
            ultima_falha = exc
            log.warning("Falhou: %s", str(exc).splitlines()[0])
            if tentativa < cfg.tentativas:
                time.sleep(2 * tentativa)
    raise FalhaNoNavegador(f"não consegui baixar a planilha após {cfg.tentativas} tentativas: {ultima_falha}")


def _baixar(cfg: Config) -> Path:
    cfg.pasta_saida.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        try:
            # Usa o Chromium do próprio Playwright (instalado com `playwright install chromium`),
            # e não o Chromium do snap, que falha quando o robô roda pelo cron ou por um serviço.
            navegador = p.chromium.launch(headless=cfg.headless, executable_path=cfg.navegador_path)
        except PlaywrightError as exc:
            raise FalhaNoNavegador(f"o navegador não abriu: {exc}") from exc

        try:
            pagina = navegador.new_context(accept_downloads=True).new_page()
            pagina.set_default_timeout(cfg.timeout_ms)

            pagina.goto(cfg.portal_url)
            pagina.fill("#usuario", cfg.usuario)
            pagina.fill("#senha", cfg.senha)
            pagina.click("#entrar")

            erro = pagina.locator("#erro")
            pagina.wait_for_function(
                "() => location.pathname.endsWith('painel.html') || !document.getElementById('erro')?.hidden"
            )
            if erro.count() and erro.is_visible():
                raise FalhaNoNavegador("login recusado pelo portal (confira usuário e senha)")
            log.info("Login feito")

            pagina.select_option("#mes", cfg.mes)
            with pagina.expect_download() as info:
                pagina.click("#exportar")
            download = info.value
            destino = cfg.pasta_saida / download.suggested_filename
            download.save_as(destino)
        finally:
            navegador.close()

    if not destino.exists() or destino.stat().st_size == 0:
        raise FalhaNoNavegador("o download terminou, mas o arquivo está vazio")
    log.info("Planilha salva em %s", destino)
    return destino
