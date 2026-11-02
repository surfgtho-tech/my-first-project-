"""Interface de linha de comando.

Exemplo:
    python -m buscador_passagens --origem DUB --destinos BKK HKT \
        --data-inicio 2026-12-07 --data-fim 2026-12-10
"""
import argparse
import os
import sys

from .busca import buscar_flexivel, mais_barata_por_dia


def carregar_env(caminho: str = ".env") -> None:
    """Lê variáveis do arquivo .env (formato CHAVE=valor), se existir."""
    if not os.path.exists(caminho):
        return
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                chave, valor = linha.split("=", 1)
                os.environ.setdefault(chave.strip(), valor.strip().strip('"\''))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Busca a passagem mais barata em várias datas.")
    p.add_argument("--origem", default="DUB", help="Aeroporto de origem (padrão: DUB)")
    p.add_argument("--destinos", nargs="+", default=["BKK", "HKT"],
                   help="Um ou mais aeroportos de destino (padrão: BKK HKT)")
    p.add_argument("--data-inicio", required=True, help="Primeira data de ida (AAAA-MM-DD)")
    p.add_argument("--data-fim", required=True, help="Última data de ida (AAAA-MM-DD)")
    p.add_argument("--adultos", type=int, default=1)
    p.add_argument("--max-conexoes", type=int, default=1)
    p.add_argument("--top", type=int, default=10, help="Quantas ofertas mostrar")
    p.add_argument("--simulado", action="store_true",
                   help="Usa dados falsos (não precisa de conta na API)")
    args = p.parse_args(argv)

    carregar_env()
    token = os.environ.get("DUFFEL_ACCESS_TOKEN")

    if args.simulado:
        from .simulado import ClienteSimulado
        cliente = ClienteSimulado()
        print("🧪 MODO SIMULADO — os preços abaixo são inventados.\n")
    elif token:
        from .duffel import ClienteDuffel
        cliente = ClienteDuffel(token)
        if token.startswith("duffel_test"):
            print("🧪 Token de TESTE da Duffel — os resultados não são preços reais.\n")
    else:
        print("Nenhum DUFFEL_ACCESS_TOKEN encontrado.\n"
              "Crie um arquivo .env (veja .env.example) ou rode com --simulado.")
        return 1

    destinos = [d.upper() for d in args.destinos]
    ofertas = buscar_flexivel(
        cliente, args.origem.upper(), destinos, args.data_inicio, args.data_fim,
        adultos=args.adultos, max_conexoes=args.max_conexoes,
        ao_buscar=lambda o, d, data: print(f"🔎 Buscando {o} → {d} em {data}..."),
    )

    if not ofertas:
        print("\nNenhuma oferta encontrada.")
        return 0

    print(f"\n📅 Mais barata por dia de ida:")
    for data, o in mais_barata_por_dia(ofertas).items():
        print(f"  {data}: {o.preco:>8} {o.moeda}  {o.companhia} ({o.rota})")

    print(f"\n🏆 Top {args.top} ofertas (total para {args.adultos} adulto(s)):")
    for i, o in enumerate(ofertas[:args.top], 1):
        partida = o.trechos[0].partida.strftime("%d/%m %H:%M") if o.trechos else ""
        print(f"{i:>2}. {o.preco:>8} {o.moeda} | {o.companhia:<20} | {o.data_ida} "
              f"sai {partida} | {o.rota} | {o.duracao} | {o.conexoes} conexão(ões)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
