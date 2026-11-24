# Robô de Relatório de Vendas

Robô de automação web (RPA) que entra num portal, baixa a planilha de vendas do mês, calcula os indicadores e envia um resumo com o relatório em anexo. Ele foi pensado para rodar sozinho (cron, agendador do Windows, chamado por outro sistema), então cada tipo de falha termina com um código de saída diferente e o robô nunca finge que deu certo.

O repositório traz um **portal de demonstração** com dados fictícios, então dá para rodar o fluxo completo sem acesso a nenhum sistema real.

## O que ele faz

1. Abre o navegador (Chromium via Playwright) e faz login no portal
2. Escolhe o mês e baixa a planilha `.xlsx`
3. Confere a planilha (arquivo existe, tem as colunas certas e tem vendas)
4. Calcula faturamento, pedidos, ticket médio, faturamento por região, top 3 vendedores, produtos e melhor dia
5. Gera um relatório HTML
6. Envia o resumo e o relatório pelo canal configurado: console, Telegram ou webhook

Falhas temporárias no portal são tentadas de novo (`TENTATIVAS`, com espera crescente entre elas).

## Códigos de saída

| Código | Significado |
|---:|---|
| 0 | Relatório gerado e enviado |
| 1 | Erro inesperado |
| 2 | O navegador não abriu ou o fluxo no portal falhou (login recusado, página fora do ar) |
| 3 | A planilha baixada é inválida ou está vazia |
| 4 | O relatório foi gerado, mas o envio falhou |

Quem chama o robô (um script, o cron, um sistema em PHP) consegue saber exatamente o que aconteceu e não envia relatório vazio quando o robô falha.

## Como rodar

Requer Python 3.10 ou superior.

```bash
pip install -r requirements.txt
python -m playwright install chromium   # baixa o Chromium do Playwright

python -m robo --demo                   # sobe o portal de demonstração e roda o robô
python -m robo --demo --mes 2026-10     # outro mês
python -m pytest -q                     # testes
```

Com `--demo`, o portal de demonstração roda em `http://127.0.0.1:8765` (usuário `demo`, senha `demo123`). A saída fica na pasta `saida/`.

### Configuração

Copie `.env.example` para `.env` e ajuste. Para enviar pelo Telegram:

```
NOTIFICADOR=telegram
TELEGRAM_TOKEN=token-do-seu-bot
TELEGRAM_CHAT_ID=id-do-chat
```

### Rodando num servidor Linux

O robô usa o Chromium baixado pelo Playwright, e não o Chromium do snap. O do snap costuma falhar quando o robô roda pelo cron ou como serviço (`cannot run snap applications`). Se preferir usar um Chrome já instalado, defina `NAVEGADOR_PATH=/usr/bin/google-chrome`.

Exemplo de agendamento no cron, todo dia 1º às 7h, guardando o log:

```
0 7 1 * * cd /opt/robo && .venv/bin/python -m robo >> robo.log 2>&1
```

## Estrutura

```
├── robo/
│   ├── __main__.py      # orquestra as etapas e define os códigos de saída
│   ├── config.py        # configuração por variáveis de ambiente / .env
│   ├── navegador.py     # login e download com Playwright, com novas tentativas
│   ├── relatorio.py     # leitura da planilha, indicadores e HTML
│   ├── notificador.py   # envio por console, Telegram ou webhook
│   └── servidor_demo.py # servidor local do portal de demonstração
├── portal_demo/         # portal fictício (login + exportação da planilha)
├── tests/               # testes do relatório e do fluxo completo no portal de demonstração
└── gerar_planilhas_demo.py
```

## Tecnologias

Python, Playwright, openpyxl, pytest e GitHub Actions.
