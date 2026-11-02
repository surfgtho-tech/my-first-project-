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

Opções úteis:

| Opção | Padrão | O que faz |
|---|---|---|
| `--origem` | `DUB` | Aeroporto de saída |
| `--destinos` | `BKK HKT` | Um ou mais destinos |
| `--adultos` | `1` | Número de passageiros |
| `--max-conexoes` | `1` | Máximo de conexões (0 = só voo direto) |
| `--top` | `10` | Quantas ofertas mostrar |

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

- [ ] Passagem de ida e volta (`--volta`)
- [ ] Salvar histórico de preços (SQLite) e alertar quando cair
- [ ] Converter moeda para BRL
- [ ] Interface web (Flask ou Streamlit)
