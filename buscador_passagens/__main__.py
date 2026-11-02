"""Interface de linha de comando.

Exemplos:
    # só ida, datas flexíveis
    python -m buscador_passagens --data-inicio 2026-12-07 --data-fim 2026-12-10

    # ida e volta + alerta por e-mail se o preço ficar abaixo de 900
    python -m buscador_passagens --data-inicio 2026-12-07 --data-fim 2026-12-10 \
        --volta-inicio 2027-01-05 --volta-fim 2027-01-08 --alerta --preco-alvo 900
"""
import argparse
import os
import sys
from decimal import Decimal

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
    p.add_argument("--destinos", nargs="+", default=["MNL"],
                   help="Um ou mais aeroportos de destino (padrão: MNL - Manila)")
    p.add_argument("--data-inicio", required=True, help="Primeira data de ida (AAAA-MM-DD)")
    p.add_argument("--data-fim", help="Última data de ida (padrão: igual à primeira)")
    p.add_argument("--volta-inicio", help="Primeira data de volta (ativa ida e volta)")
    p.add_argument("--volta-fim", help="Última data de volta (padrão: igual à primeira)")
    p.add_argument("--adultos", type=int, default=1)
    p.add_argument("--max-conexoes", type=int, default=1)
    p.add_argument("--com-bagagem", action="store_true",
                   help="Mostra só tarifas com mala despachada incluída")
    p.add_argument("--top", type=int, default=10, help="Quantas ofertas mostrar")
    p.add_argument("--alerta", action="store_true", help="Envia o resultado por e-mail")
    p.add_argument("--preco-alvo", type=Decimal,
                   help="Com --alerta: só envia se o melhor preço for menor ou igual a este")
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

    origem = args.origem.upper()
    destinos = [d.upper() for d in args.destinos]
    ofertas = buscar_flexivel(
        cliente, origem, destinos, args.data_inicio, args.data_fim or args.data_inicio,
        volta_inicio=args.volta_inicio, volta_fim=args.volta_fim,
        adultos=args.adultos, max_conexoes=args.max_conexoes,
        so_com_bagagem=args.com_bagagem,
        ao_buscar=lambda o, d, ida, volta: print(
            f"🔎 Buscando {o} → {d} ida {ida}" + (f", volta {volta}" if volta else "") + "..."),
    )

    if not ofertas:
        print("\nNenhuma oferta encontrada.")
        return 0

    print("\n📅 Mais barata por data:")
    for datas, o in mais_barata_por_dia(ofertas).items():
        print(f"  {datas}: {o.preco:>8} {o.moeda}  {o.companhia} ({o.rota})")

    print(f"\n🏆 Top {args.top} ofertas (total para {args.adultos} adulto(s)):")
    for i, o in enumerate(ofertas[:args.top], 1):
        print(f"{i:>2}. {o.resumo()}")

    if args.alerta:
        melhor = ofertas[0]
        if args.preco_alvo is not None and melhor.preco > args.preco_alvo:
            print(f"\n📭 Melhor preço {melhor.preco} acima do alvo {args.preco_alvo} — sem e-mail.")
            return 0
        from .alerta import ConfigEmailFaltando, ErroEnvioEmail, enviar_email, montar_email
        tipo = "ida e volta" if args.volta_inicio else "só ida"
        titulo = f"{origem} → {'/'.join(destinos)} ({tipo})"
        if args.simulado:
            titulo = "[SIMULADO] " + titulo
        assunto, corpo = montar_email(ofertas, titulo)
        try:
            destinatarios = enviar_email(assunto, corpo)
        except ConfigEmailFaltando as erro:
            print(f"\n❌ {erro} (veja .env.example)")
            return 1
        except ErroEnvioEmail as erro:
            print(f"\n❌ Falha ao enviar e-mail: {erro}")
            return 1
        print(f"\n📧 Alerta enviado para {len(destinatarios)} destinatário(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
