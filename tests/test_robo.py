import os
import sys
from datetime import date
from pathlib import Path

import pytest
from openpyxl import Workbook

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from robo import relatorio, servidor_demo  # noqa: E402
from robo.__main__ import executar  # noqa: E402
from robo.config import Config  # noqa: E402


def planilha(tmp_path, linhas, cabecalho=relatorio.COLUNAS):
    wb = Workbook()
    ws = wb.active
    ws.append(cabecalho)
    for linha in linhas:
        ws.append(linha)
    caminho = tmp_path / "vendas.xlsx"
    wb.save(caminho)
    return caminho


# ---------- relatório ----------

def test_resumo_calcula_indicadores(tmp_path):
    arq = planilha(tmp_path, [
        [date(2026, 11, 3), 1, "Sul", "Ana", "Mouse", 2, 50.0, 100.0],
        [date(2026, 11, 3), 1, "Sul", "Ana", "Teclado", 1, 200.0, 200.0],
        [date(2026, 11, 4), 2, "Norte", "Bruno", "Monitor", 1, 900.0, 900.0],
    ])
    r = relatorio.resumir(relatorio.ler_planilha(arq), "2026-11")
    assert r.pedidos == 2 and r.itens == 4
    assert r.faturamento == 1200.0 and r.ticket_medio == 600.0
    assert r.por_regiao[0] == ("Norte", 900.0)
    assert r.melhor_dia == (date(2026, 11, 4), 900.0)


def test_planilha_sem_colunas_e_recusada(tmp_path):
    arq = planilha(tmp_path, [[1, 2]], cabecalho=["Data", "Pedido"])
    with pytest.raises(relatorio.PlanilhaInvalida, match="colunas ausentes"):
        relatorio.ler_planilha(arq)


def test_planilha_vazia_e_recusada(tmp_path):
    with pytest.raises(relatorio.PlanilhaInvalida, match="nenhuma venda"):
        relatorio.ler_planilha(planilha(tmp_path, []))


def test_arquivo_inexistente_e_recusado(tmp_path):
    with pytest.raises(relatorio.PlanilhaInvalida, match="não encontrado"):
        relatorio.ler_planilha(tmp_path / "nao_existe.xlsx")


def test_formato_em_reais():
    assert relatorio.brl(1234567.8) == "R$ 1.234.567,80"


# ---------- robô completo contra o portal de demonstração ----------

def config(tmp_path, porta, **extra):
    base = dict(
        portal_url=f"http://127.0.0.1:{porta}/index.html", usuario="demo", senha="demo123", mes="2026-10",
        pasta_saida=tmp_path, notificador="console", headless=True,
        navegador_path=os.environ.get("NAVEGADOR_PATH") or None, timeout_ms=15000, tentativas=1,
        telegram_token=None, telegram_chat_id=None, webhook_url=None,
    )
    base.update(extra)
    return Config(**base)


@pytest.fixture(scope="module")
def portal():
    servidor = servidor_demo.iniciar(porta=8799)
    yield 8799
    servidor.shutdown()


@pytest.fixture(scope="module")
def navegador_disponivel():
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            p.chromium.launch(executable_path=os.environ.get("NAVEGADOR_PATH") or None).close()
    except Exception as exc:
        pytest.skip(f"navegador indisponível: {exc}")


def test_fluxo_completo(tmp_path, portal, navegador_disponivel):
    assert executar(config(tmp_path, portal)) == 0
    assert (tmp_path / "vendas_2026-10.xlsx").exists()
    assert "Relatório de vendas" in (tmp_path / "relatorio_2026-10.html").read_text(encoding="utf-8")


def test_senha_errada_sai_com_codigo_2(tmp_path, portal, navegador_disponivel):
    assert executar(config(tmp_path, portal, senha="errada")) == 2


def test_envio_sem_configuracao_sai_com_codigo_4(tmp_path, portal, navegador_disponivel):
    assert executar(config(tmp_path, portal, notificador="webhook")) == 4
