"""Lê a planilha baixada, calcula os indicadores e monta o relatório."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from html import escape
from pathlib import Path

from openpyxl import load_workbook

COLUNAS = ["Data", "Pedido", "Região", "Vendedor", "Produto", "Quantidade", "Valor unitário", "Valor total"]


class PlanilhaInvalida(Exception):
    """A planilha não existe, está vazia ou não tem as colunas esperadas."""


@dataclass
class Resumo:
    mes: str
    pedidos: int
    itens: int
    faturamento: float
    ticket_medio: float
    por_regiao: list[tuple[str, float]]
    top_vendedores: list[tuple[str, float]]
    por_produto: list[tuple[str, int, float]]
    melhor_dia: tuple[date, float]


def ler_planilha(caminho: Path) -> list[dict]:
    if not caminho.exists():
        raise PlanilhaInvalida(f"arquivo não encontrado: {caminho}")
    ws = load_workbook(caminho, read_only=True, data_only=True).active
    linhas = ws.iter_rows(values_only=True)
    cabecalho = [str(c).strip() if c is not None else "" for c in next(linhas, [])]
    faltando = [c for c in COLUNAS if c not in cabecalho]
    if faltando:
        raise PlanilhaInvalida(f"colunas ausentes na planilha: {', '.join(faltando)}")
    registros = [dict(zip(cabecalho, linha)) for linha in linhas if any(v is not None for v in linha)]
    if not registros:
        raise PlanilhaInvalida("a planilha não tem nenhuma venda")
    return registros


def _data(valor) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor), "%d/%m/%Y").date()


def resumir(registros: list[dict], mes: str) -> Resumo:
    por_regiao, por_vendedor, por_dia = defaultdict(float), defaultdict(float), defaultdict(float)
    por_produto = defaultdict(lambda: [0, 0.0])
    pedidos, itens, total = set(), 0, 0.0

    for r in registros:
        valor = float(r["Valor total"])
        qtd = int(r["Quantidade"])
        total += valor
        itens += qtd
        pedidos.add(r["Pedido"])
        por_regiao[r["Região"]] += valor
        por_vendedor[r["Vendedor"]] += valor
        por_dia[_data(r["Data"])] += valor
        por_produto[r["Produto"]][0] += qtd
        por_produto[r["Produto"]][1] += valor

    ordenar = lambda d: sorted(d.items(), key=lambda kv: kv[1], reverse=True)  # noqa: E731
    return Resumo(
        mes=mes,
        pedidos=len(pedidos),
        itens=itens,
        faturamento=round(total, 2),
        ticket_medio=round(total / len(pedidos), 2),
        por_regiao=ordenar(por_regiao),
        top_vendedores=ordenar(por_vendedor)[:3],
        por_produto=sorted(((p, q, v) for p, (q, v) in por_produto.items()), key=lambda x: x[2], reverse=True),
        melhor_dia=max(por_dia.items(), key=lambda kv: kv[1]),
    )


def brl(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def texto_curto(r: Resumo) -> str:
    """Resumo para mensagem de chat."""
    linhas = [
        f"Relatório de vendas {r.mes}",
        f"Faturamento: {brl(r.faturamento)}",
        f"Pedidos: {r.pedidos} | Ticket médio: {brl(r.ticket_medio)}",
        f"Melhor região: {r.por_regiao[0][0]} ({brl(r.por_regiao[0][1])})",
        "Top vendedores: " + ", ".join(f"{n} ({brl(v)})" for n, v in r.top_vendedores),
        f"Melhor dia: {r.melhor_dia[0]:%d/%m} ({brl(r.melhor_dia[1])})",
    ]
    return "\n".join(linhas)


def html(r: Resumo) -> str:
    def tabela(titulo, cabecalho, linhas):
        th = "".join(f"<th>{escape(c)}</th>" for c in cabecalho)
        tr = "".join("<tr>" + "".join(f"<td>{escape(str(c))}</td>" for c in linha) + "</tr>" for linha in linhas)
        return f"<h2>{escape(titulo)}</h2><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Relatório de vendas {escape(r.mes)}</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:760px;margin:32px auto;padding:0 16px;color:#1d2433}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}
.kpi{{background:#f2f4f7;border-radius:10px;padding:14px}} .kpi b{{display:block;font-size:22px}}
table{{border-collapse:collapse;width:100%}} th,td{{text-align:left;padding:8px;border-bottom:1px solid #e1e5ec}}
td:last-child,th:last-child{{text-align:right}}
</style></head><body>
<h1>Relatório de vendas · {escape(r.mes)}</h1>
<div class="kpis">
<div class="kpi">Faturamento<b>{brl(r.faturamento)}</b></div>
<div class="kpi">Pedidos<b>{r.pedidos}</b></div>
<div class="kpi">Ticket médio<b>{brl(r.ticket_medio)}</b></div>
<div class="kpi">Melhor dia<b>{r.melhor_dia[0]:%d/%m}</b></div>
</div>
{tabela("Faturamento por região", ["Região", "Faturamento"], [(n, brl(v)) for n, v in r.por_regiao])}
{tabela("Top 3 vendedores", ["Vendedor", "Faturamento"], [(n, brl(v)) for n, v in r.top_vendedores])}
{tabela("Produtos", ["Produto", "Unidades", "Faturamento"], [(p, q, brl(v)) for p, q, v in r.por_produto])}
</body></html>
"""
