"""Ponto de entrada: python -m robo [--mes AAAA-MM] [--demo]

Códigos de saída (para o cron, o PHP ou qualquer orquestrador saber o que aconteceu):
  0  relatório gerado e enviado
  1  erro inesperado
  2  o navegador não abriu ou o fluxo no portal falhou
  3  a planilha baixada é inválida ou está vazia
  4  o relatório foi gerado, mas o envio falhou
"""

import argparse
import logging
import sys

from . import notificador, relatorio, servidor_demo
from .config import Config, carregar_env
from .navegador import FalhaNoNavegador, baixar_planilha

log = logging.getLogger("robo")


def executar(cfg: Config) -> int:
    try:
        planilha = baixar_planilha(cfg)
    except FalhaNoNavegador as exc:
        log.error("Robô parou: %s", exc)
        return 2

    try:
        resumo = relatorio.resumir(relatorio.ler_planilha(planilha), cfg.mes)
    except relatorio.PlanilhaInvalida as exc:
        log.error("Planilha inválida: %s", exc)
        return 3

    arquivo_html = cfg.pasta_saida / f"relatorio_{cfg.mes}.html"
    arquivo_html.write_text(relatorio.html(resumo), encoding="utf-8")
    log.info("Relatório salvo em %s", arquivo_html)

    try:
        notificador.enviar(cfg, relatorio.texto_curto(resumo), arquivo_html)
    except notificador.FalhaNoEnvio as exc:
        log.error("Relatório gerado, mas o envio falhou: %s", exc)
        return 4
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Robô que baixa a planilha de vendas e envia o relatório")
    parser.add_argument("--mes", help="mês no formato AAAA-MM (padrão: RELATORIO_MES ou 2026-11)")
    parser.add_argument("--demo", action="store_true", help="sobe o portal de demonstração localmente")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    carregar_env()
    cfg = Config.do_ambiente(args.mes)

    servidor = servidor_demo.iniciar() if args.demo else None
    try:
        codigo = executar(cfg)
    except Exception:  # qualquer outra coisa: registra e sai com erro, nunca finge sucesso
        log.exception("Erro inesperado")
        codigo = 1
    finally:
        if servidor:
            servidor.shutdown()

    log.info("Finalizado com código %d", codigo)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
