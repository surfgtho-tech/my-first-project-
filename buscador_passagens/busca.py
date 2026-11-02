"""Lógica principal: combina várias datas e destinos e acha o mais barato."""
from datetime import date, timedelta

from .modelos import Oferta


def gerar_datas(inicio: str, fim: str) -> list[str]:
    """Lista todas as datas entre início e fim (inclusive)."""
    d_inicio, d_fim = date.fromisoformat(inicio), date.fromisoformat(fim)
    if d_fim < d_inicio:
        raise ValueError("A data final deve ser igual ou depois da inicial.")
    dias = (d_fim - d_inicio).days
    return [(d_inicio + timedelta(days=i)).isoformat() for i in range(dias + 1)]


def buscar_flexivel(cliente, origem: str, destinos: list[str],
                    data_inicio: str, data_fim: str, adultos: int = 1,
                    max_conexoes: int = 1, ao_buscar=None) -> list[Oferta]:
    """Faz uma busca para cada combinação (data x destino) e junta tudo,
    ordenado do mais barato para o mais caro."""
    todas: list[Oferta] = []
    for data_ida in gerar_datas(data_inicio, data_fim):
        for destino in destinos:
            if ao_buscar:
                ao_buscar(origem, destino, data_ida)
            try:
                todas += cliente.buscar(origem, destino, data_ida,
                                        adultos=adultos,
                                        max_conexoes=max_conexoes)
            except Exception as erro:  # uma falha não derruba a busca inteira
                print(f"  ⚠️  Falha em {origem}→{destino} {data_ida}: {erro}")
    return sorted(todas, key=lambda o: o.preco)


def mais_barata_por_dia(ofertas: list[Oferta]) -> dict[str, Oferta]:
    """Para cada data, a oferta mais barata (ofertas já devem estar ordenadas)."""
    resultado: dict[str, Oferta] = {}
    for oferta in ofertas:
        resultado.setdefault(oferta.data_ida, oferta)
    return dict(sorted(resultado.items()))
