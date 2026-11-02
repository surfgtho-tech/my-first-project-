"""Estruturas de dados usadas no app (independentes da API)."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class Trecho:
    """Um voo individual (ex.: DUB -> DOH)."""
    origem: str
    destino: str
    partida: datetime
    chegada: datetime
    companhia: str
    numero_voo: str


@dataclass
class Oferta:
    """Uma passagem completa à venda, com preço total."""
    preco: Decimal
    moeda: str
    companhia: str              # companhia que vende a tarifa
    destino: str                # aeroporto final (BKK, HKT...)
    data_ida: str               # AAAA-MM-DD
    trechos: list[Trecho] = field(default_factory=list)
    duracao: str = ""           # ex.: "17h 25m"

    @property
    def conexoes(self) -> int:
        return max(len(self.trechos) - 1, 0)

    @property
    def rota(self) -> str:
        if not self.trechos:
            return ""
        aeroportos = [self.trechos[0].origem] + [t.destino for t in self.trechos]
        return " → ".join(aeroportos)
