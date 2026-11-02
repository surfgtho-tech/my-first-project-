# Buscador de Passagens ✈️

App de linha de comando em Python que procura a passagem mais barata
**em várias datas e destinos de uma vez**. Usa a API da [Duffel](https://duffel.com),
que traz tarifas direto das companhias aéreas (NDC).

Exemplo de uso: Dublin (DUB) → Tailândia (Bangkok BKK / Phuket HKT), ida entre os dias 7 e 10.

## Como rodar

```bash
pip install -r requirements.txt

# 1) Sem conta (dados inventados, só para testar)
python -m buscador_passagens --simulado --data-inicio 2026-12-07 --data-fim 2026-12-10

# 2) Com a API da Duffel
cp .env.example .env      # e coloque seu token no arquivo .env
python -m buscador_passagens --data-inicio 2026-12-07 --data-fim 2026-12-10
```

# 3) Ida e volta, só tarifas com mala, e-mail se custar até 900 EUR
python -m buscador_passagens --data-inicio 2026-12-07 --data-fim 2026-12-10 \
    --volta-inicio 2027-01-05 --volta-fim 2027-01-08 --com-bagagem \
    --alerta --preco-alvo 900
```

Opções úteis:

| Opção | Padrão | O que faz |
|---|---|---|
| `--origem` | `DUB` | Aeroporto de saída |
| `--destinos` | `BKK HKT` | Um ou mais destinos |
| `--adultos` | `1` | Número de passageiros |
| `--max-conexoes` | `1` | Máximo de conexões (0 = só voo direto) |
| `--top` | `10` | Quantas ofertas mostrar |
| `--volta-inicio` / `--volta-fim` | — | Datas de volta (ativa ida e volta) |
| `--com-bagagem` | — | Só tarifas com mala despachada incluída |
| `--alerta` | — | Envia o resultado por e-mail |
| `--preco-alvo` | — | Com `--alerta`: só envia se o preço for menor ou igual |

## Alerta automático todo dia (GitHub Actions)

O arquivo `.github/workflows/alerta-passagens.yml` roda a busca uma vez por dia
e manda e-mail quando acha um preço bom. Para ativar:

1. No GitHub: **Settings → Secrets and variables → Actions → New repository secret** e crie:
   `DUFFEL_ACCESS_TOKEN`, `ALERTA_EMAIL`, `SMTP_USUARIO`, `SMTP_SENHA`.
2. `SMTP_SENHA` no Gmail é uma **senha de app** (Conta Google → Segurança →
   Senhas de app; precisa da verificação em 2 etapas ligada).
3. Edite as datas e o `PRECO_ALVO` no topo do arquivo do workflow.
4. Teste na aba **Actions → Alerta de passagens → Run workflow**.

> **Atenção:** com token de **teste** (`duffel_test_...`) a Duffel devolve só a
> companhia fictícia "Duffel Airways" — os preços não são reais. Para preços reais
> é preciso ativar o modo *live* na conta da Duffel.

## Estrutura do código

```
buscador_passagens/
  __main__.py   # linha de comando (argumentos e impressão dos resultados)
  busca.py      # gera as datas, faz todas as buscas e ordena por preço
  duffel.py     # conversa com a API da Duffel
  simulado.py   # cliente falso para testar sem API
  modelos.py    # classes Oferta e Trecho
tests/          # testes: python -m unittest discover -s tests
```

## Próximos passos (ideias para praticar)

- [ ] Salvar histórico de preços (SQLite) e alertar quando cair
- [ ] Converter moeda para BRL
- [ ] Interface web (Flask ou Streamlit)
