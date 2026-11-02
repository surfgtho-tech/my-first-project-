"""Cliente falso que gera ofertas de exemplo — para testar sem conta na API.

Os preços são INVENTADOS. Use apenas para ver o app funcionando.
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal

from .modelos import Oferta, Trecho

# (companhia, código, aeroporto de conexão)
_COMPANHIAS = [
    ("Qatar Airways", "QR", "DOH"),
    ("Emirates", "EK", "DXB"),
    ("Etihad Airways", "EY", "AUH"),
    ("Turkish Airlines", "TK", "IST"),
    ("Finnair", "AY", "HEL"),
]


def _viagem(rnd, origem, destino, hub, dia, nome, codigo, malas):
    partida = dia + timedelta(hours=rnd.randint(6, 22))
    chegada_hub = partida + timedelta(hours=rnd.randint(6, 8))
    saida_hub = chegada_hub + timedelta(hours=rnd.randint(2, 6))
    chegada = saida_hub + timedelta(hours=rnd.randint(6, 9))
    total = chegada - partida
    duracao = f"{total.days * 24 + total.seconds // 3600}h {(total.seconds % 3600) // 60}m"
    trechos = [
        Trecho(origem, hub, partida, chegada_hub, nome, f"{codigo}{rnd.randint(1, 999)}", malas),
        Trecho(hub, destino, saida_hub, chegada, nome, f"{codigo}{rnd.randint(1, 999)}", malas),
    ]
    return trechos, duracao


class ClienteSimulado:
    def buscar(self, origem: str, destino: str, data_ida: str,
               data_volta: str | None = None, adultos: int = 1,
               max_conexoes: int = 1, cabine: str = "economy") -> list[Oferta]:
        # semente fixa: a mesma busca sempre gera os mesmos resultados
        rnd = random.Random(f"{origem}{destino}{data_ida}{data_volta}")
        ofertas = []
        for nome, codigo, hub in _COMPANHIAS:
            malas = rnd.choice([0, 1])
            trechos, duracao = _viagem(rnd, origem, destino, hub,
                                       datetime.fromisoformat(data_ida), nome, codigo, malas)
            preco = rnd.randint(480, 1100) + (40 if malas else 0)
            oferta = Oferta(Decimal(preco * adultos), "EUR", nome, destino, data_ida,
                            trechos, duracao)
            if data_volta:
                volta, dur_volta = _viagem(rnd, destino, origem, hub,
                                           datetime.fromisoformat(data_volta), nome, codigo, malas)
                oferta.data_volta, oferta.trechos_volta, oferta.duracao_volta = \
                    data_volta, volta, dur_volta
                oferta.preco = Decimal((preco + rnd.randint(300, 700)) * adultos)
            ofertas.append(oferta)
        return ofertas
