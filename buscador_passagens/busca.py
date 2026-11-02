"""Lógica principal: combina várias datas e destinos e acha o mais barato."""
from datetime import date, timedelta

from .modelos import Oferta


def gerar_datas(inicio: str, fim: str | None = None) -> list[str]:
    """Lista todas as datas entre início e fim (inclusive)."""
    d_inicio = date.fromisoformat(inicio)
    d_fim = date.fromisoformat(fim) if fim else d_inicio
    if d_fim < d_inicio:
        raise ValueError("A data final deve ser igual ou depois da inicial.")
    dias = (d_fim - d_inicio).days
    return [(d_inicio + timedelta(days=i)).isoformat() for i in range(dias + 1)]


def buscar_flexivel(cliente, origem: str, destinos: list[str],
                    data_inicio: str, data_fim: str,
                    volta_inicio: str | None = None, volta_fim: str | None = None,
                    adultos: int = 1, max_conexoes: int = 1,
                    so_com_bagagem: bool = False, ao_buscar=None) -> list[Oferta]:
    """Faz uma busca para cada combinação (ida x volta x destino) e junta tudo,
    ordenado do mais barato para o mais caro."""
    datas_volta: list[str | None] = gerar_datas(volta_inicio, volta_fim) if volta_inicio else [None]
    todas: list[Oferta] = []
    for data_ida in gerar_datas(data_inicio, data_fim):
        for data_volta in datas_volta:
            if data_volta and data_volta <= data_ida:
                continue  # volta precisa ser depois da ida
            for destino in destinos:
                if ao_buscar:
                    ao_buscar(origem, destino, data_ida, data_volta)
                try:
                    todas += cliente.buscar(origem, destino, data_ida, data_volta,
                                            adultos=adultos, max_conexoes=max_conexoes)
                except Exception as erro:  # uma falha não derruba a busca inteira
                    print(f"  ⚠️  Falha em {origem}→{destino} {data_ida}/{data_volta}: {erro}")
    if so_com_bagagem:
        todas = [o for o in todas if o.bagagem_incluida]
    return sorted(todas, key=lambda o: o.preco)


def mais_barata_por_dia(ofertas: list[Oferta]) -> dict[str, Oferta]:
    """Para cada combinação de datas, a oferta mais barata (ofertas já ordenadas)."""
    resultado: dict[str, Oferta] = {}
    for oferta in ofertas:
        chave = oferta.data_ida + (f" ↔ {oferta.data_volta}" if oferta.data_volta else "")
        resultado.setdefault(chave, oferta)
    return dict(sorted(resultado.items()))
