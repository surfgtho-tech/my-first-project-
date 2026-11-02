# Buscador de Passagens ✈️

App de linha de comando em Python que procura a passagem mais barata
**em várias datas e destinos de uma vez**. Os preços vêm do **Google Flights**
pela [SerpApi](https://serpapi.com) (cadastro pessoal e grátis). Também funciona
com a API da [Duffel](https://duffel.com), mas o modo live dela exige cadastro de empresa.

Exemplo de uso: Dublin (DUB) → Manila, Filipinas (MNL – Ninoy Aquino International Airport).

## Como rodar

```bash
pip install -r requirements.txt

# 1) Sem conta (dados inventados, só para testar)
python -m buscador_passagens --simulado --data-inicio 2026-12-07 --data-fim 2026-12-10

# 2) Com preços reais (Google Flights)
cp .env.example .env      # e coloque sua SERPAPI_KEY no arquivo .env
python -m buscador_passagens --data-inicio 2026-12-07 --data-fim 2026-12-10

# 3) Ida e volta, só tarifas com mala, e-mail se custar até 900 EUR
python -m buscador_passagens --data-inicio 2026-12-07 --data-fim 2026-12-10 \
    --volta-inicio 2027-01-05 --volta-fim 2027-01-08 --com-bagagem \
    --alerta --preco-alvo 900
```

Opções úteis:

| Opção | Padrão | O que faz |
|---|---|---|
| `--origem` | `DUB` | Aeroporto de saída |
| `--destinos` | `MNL` | Um ou mais destinos |
| `--adultos` | `1` | Número de passageiros |
| `--max-conexoes` | `1` | Máximo de conexões (0 = só voo direto) |
| `--top` | `10` | Quantas ofertas mostrar |
| `--volta-inicio` / `--volta-fim` | — | Datas de volta (ativa ida e volta) |
| `--intervalo-volta` | `1` | Testa a volta a cada N dias (gasta menos buscas) |
| `--com-bagagem` | — | Só tarifas com mala despachada incluída |
| `--alerta` | — | Envia o resultado por e-mail |
| `--preco-alvo` | — | Com `--alerta`: só envia se o preço for menor ou igual |

## Alerta automático todo dia (GitHub Actions)

O arquivo `.github/workflows/alerta-passagens.yml` roda a busca duas vezes por
semana e manda e-mail quando acha um preço bom. Para ativar:

1. No GitHub: **Settings → Secrets and variables → Actions → New repository secret** e crie:
   `SERPAPI_KEY`, `ALERTA_EMAIL`, `BREVO_API_KEY`, `REMETENTE_EMAIL`.
2. A chave da Brevo fica em **brevo.com → SMTP & API → API Keys**; o
   `REMETENTE_EMAIL` é o e-mail que você confirmou na Brevo.
   (Alternativa: Gmail com `SMTP_USUARIO` + `SMTP_SENHA` = senha de app.)
3. Edite as datas e o `PRECO_ALVO` no topo do arquivo do workflow.
4. Teste na aba **Actions → Alerta de passagens → Run workflow**.

> **Atenção:** o plano grátis da SerpApi tem um limite de buscas por mês, e cada
> combinação de datas gasta 1 busca. Use `--intervalo-volta 2` para economizar.
> O Google Flights não informa se a mala está incluída: confira no site antes de comprar.

## Estrutura do código

```
buscador_passagens/
  __main__.py   # linha de comando (argumentos e impressão dos resultados)
  busca.py      # gera as datas, faz todas as buscas e ordena por preço
  serpapi.py    # busca no Google Flights (SerpApi)
  duffel.py     # conversa com a API da Duffel
  simulado.py   # cliente falso para testar sem API
  modelos.py    # classes Oferta e Trecho
tests/          # testes: python -m unittest discover -s tests
```

## Próximos passos (ideias para praticar)

- [ ] Salvar histórico de preços (SQLite) e alertar quando cair
- [ ] Converter moeda para BRL
- [ ] Interface web (Flask ou Streamlit)
