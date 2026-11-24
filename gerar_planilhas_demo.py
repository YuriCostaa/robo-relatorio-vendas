"""Gera as planilhas fictícias de vendas que o portal de demonstração oferece para download."""

import random
from datetime import date, timedelta
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

PASTA = Path(__file__).parent / "portal_demo" / "arquivos"
REGIOES = ["Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"]
VENDEDORES = ["Ana Lima", "Bruno Costa", "Carla Souza", "Diego Rocha", "Elisa Martins", "Felipe Alves"]
PRODUTOS = {"Notebook": 4200.0, "Monitor": 1100.0, "Teclado": 180.0, "Mouse": 90.0, "Headset": 350.0, "Webcam": 260.0}


def gerar_mes(ano: int, mes: int, semente: int) -> Path:
    rnd = random.Random(semente)
    wb = Workbook()
    ws = wb.active
    ws.title = "Vendas"
    ws.append(["Data", "Pedido", "Região", "Vendedor", "Produto", "Quantidade", "Valor unitário", "Valor total"])
    for c in ws[1]:
        c.font = Font(bold=True)
    dia = date(ano, mes, 1)
    pedido = 1000 * mes
    while dia.month == mes:
        for _ in range(rnd.randint(3, 9) if dia.weekday() < 5 else rnd.randint(0, 2)):
            pedido += 1
            produto = rnd.choice(list(PRODUTOS))
            qtd = rnd.randint(1, 8)
            unit = round(PRODUTOS[produto] * rnd.uniform(0.9, 1.1), 2)
            ws.append([dia, pedido, rnd.choice(REGIOES), rnd.choice(VENDEDORES), produto, qtd, unit, round(qtd * unit, 2)])
        dia += timedelta(days=1)
    for row in ws.iter_rows(min_row=2, max_col=1):
        row[0].number_format = "DD/MM/YYYY"
    destino = PASTA / f"vendas_{ano}-{mes:02d}.xlsx"
    PASTA.mkdir(parents=True, exist_ok=True)
    wb.save(destino)
    return destino


if __name__ == "__main__":
    for mes, semente in [(9, 1), (10, 2), (11, 3)]:
        print(gerar_mes(2026, mes, semente))
