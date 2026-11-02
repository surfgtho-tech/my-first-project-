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
    malas_despachadas: int = 0   # malas incluídas por passageiro


def _rota(trechos: list[Trecho]) -> str:
    if not trechos:
        return ""
    return " → ".join([trechos[0].origem] + [t.destino for t in trechos])


@dataclass
class Oferta:
    """Uma passagem completa à venda (só ida ou ida e volta), com preço total."""
    preco: Decimal
    moeda: str
    companhia: str              # companhia que vende a tarifa
    destino: str                # aeroporto final (BKK, HKT...)
    data_ida: str               # AAAA-MM-DD
    trechos: list[Trecho] = field(default_factory=list)          # voos da ida
    duracao: str = ""           # duração da ida, ex.: "17h 25m"
    data_volta: str | None = None
    trechos_volta: list[Trecho] = field(default_factory=list)    # voos da volta
    duracao_volta: str = ""
    bagagem_conhecida: bool = True   # False quando a fonte não informa bagagem

    @property
    def ida_e_volta(self) -> bool:
        return self.data_volta is not None

    @property
    def conexoes(self) -> int:
        return max(len(self.trechos) - 1, 0)

    @property
    def rota(self) -> str:
        return _rota(self.trechos)

    @property
    def rota_volta(self) -> str:
        return _rota(self.trechos_volta)

    @property
    def bagagem_incluida(self) -> bool:
        """True se TODOS os voos incluem pelo menos 1 mala despachada."""
        todos = self.trechos + self.trechos_volta
        return bool(todos) and all(t.malas_despachadas > 0 for t in todos)

    def resumo(self) -> str:
        """Uma linha de texto descrevendo a oferta."""
        if not self.bagagem_conhecida:
            bagagem = "bagagem: ver no site"
        else:
            bagagem = "com mala" if self.bagagem_incluida else "sem mala"
        texto = (f"{self.preco} {self.moeda} | {self.companhia} | "
                 f"ida {self.data_ida} {self.rota} ({self.duracao})")
        if self.ida_e_volta:
            texto += f" | volta {self.data_volta}"
            if self.trechos_volta:
                texto += f" {self.rota_volta} ({self.duracao_volta})"
        return f"{texto} | {bagagem}"
