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


class ClienteSimulado:
    def buscar(self, origem: str, destino: str, data_ida: str,
               adultos: int = 1, max_conexoes: int = 1,
               cabine: str = "economy") -> list[Oferta]:
        # semente fixa: a mesma busca sempre gera os mesmos resultados
        rnd = random.Random(f"{origem}{destino}{data_ida}")
        dia = datetime.fromisoformat(data_ida)
        ofertas = []
        for nome, codigo, hub in _COMPANHIAS:
            partida = dia + timedelta(hours=rnd.randint(6, 22))
            chegada_hub = partida + timedelta(hours=rnd.randint(6, 8))
            saida_hub = chegada_hub + timedelta(hours=rnd.randint(2, 6))
            chegada = saida_hub + timedelta(hours=rnd.randint(6, 9))
            preco = Decimal(rnd.randint(480, 1100)) * adultos
            total = chegada - partida
            ofertas.append(Oferta(
                preco=preco, moeda="EUR", companhia=nome,
                destino=destino, data_ida=data_ida,
                duracao=f"{total.days * 24 + total.seconds // 3600}h "
                        f"{(total.seconds % 3600) // 60}m",
                trechos=[
                    Trecho(origem, hub, partida, chegada_hub, nome,
                           f"{codigo}{rnd.randint(1, 999)}"),
                    Trecho(hub, destino, saida_hub, chegada, nome,
                           f"{codigo}{rnd.randint(1, 999)}"),
                ],
            ))
        return ofertas
