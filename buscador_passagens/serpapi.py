"""Cliente do Google Flights via SerpApi (https://serpapi.com/google-flights-api).

Cadastro pessoal e gratuito (plano free com um número limitado de buscas por mês).
Os preços são os mesmos do Google Flights, que inclui tarifas direto das companhias.
"""
from datetime import datetime
from decimal import Decimal

import requests

from .modelos import Oferta, Trecho

URL_API = "https://serpapi.com/search.json"


class ErroSerpApi(Exception):
    pass


def _hora(texto: str) -> datetime:
    # formato do Google Flights: "2026-12-07 10:35"
    return datetime.strptime(texto, "%Y-%m-%d %H:%M")


def _duracao(minutos: int | None) -> str:
    if not minutos:
        return ""
    return f"{minutos // 60}h {minutos % 60}m"


class ClienteSerpApi:
    def __init__(self, chave: str, moeda: str = "EUR", timeout: int = 60):
        self.chave = chave
        self.moeda = moeda
        self.timeout = timeout

    def buscar(self, origem: str, destino: str, data_ida: str,
               data_volta: str | None = None, adultos: int = 1,
               max_conexoes: int = 1, cabine: str = "economy") -> list[Oferta]:
        # stops: 0 = qualquer, 1 = só direto, 2 = até 1 conexão, 3 = até 2 conexões
        paradas = {0: 1, 1: 2, 2: 3}.get(max_conexoes, 0)
        params = {
            "engine": "google_flights",
            "departure_id": origem,
            "arrival_id": destino,
            "outbound_date": data_ida,
            "type": 1 if data_volta else 2,   # 1 = ida e volta, 2 = só ida
            "currency": self.moeda,
            "hl": "en",
            "adults": adultos,
            "stops": paradas,
            "api_key": self.chave,
        }
        if data_volta:
            params["return_date"] = data_volta

        try:
            resposta = requests.get(URL_API, params=params, timeout=self.timeout)
        except requests.RequestException as erro:
            # não repassa a mensagem original: ela contém a URL com a chave
            raise ErroSerpApi(f"Sem conexão com a SerpApi ({type(erro).__name__})") from None
        dados = resposta.json() if resposta.content else {}
        if resposta.status_code >= 400 or "error" in dados:
            erro = dados.get("error", resposta.text[:300])
            if "hasn't returned any results" in str(erro):
                return []
            raise ErroSerpApi(f"Erro {resposta.status_code}: {erro}")

        voos = dados.get("best_flights", []) + dados.get("other_flights", [])
        return [self._converter(v, destino, data_ida, data_volta)
                for v in voos if v.get("price")]

    def _converter(self, voo: dict, destino: str, data_ida: str,
                   data_volta: str | None) -> Oferta:
        trechos = [
            Trecho(
                origem=s["departure_airport"]["id"],
                destino=s["arrival_airport"]["id"],
                partida=_hora(s["departure_airport"]["time"]),
                chegada=_hora(s["arrival_airport"]["time"]),
                companhia=s.get("airline", ""),
                numero_voo=s.get("flight_number", "").replace(" ", ""),
            )
            for s in voo["flights"]
        ]
        companhias = list(dict.fromkeys(t.companhia for t in trechos))
        return Oferta(
            preco=Decimal(str(voo["price"])),   # no ida e volta, já é o preço total
            moeda=self.moeda,
            companhia=" + ".join(companhias),
            destino=destino,
            data_ida=data_ida,
            trechos=trechos,
            duracao=_duracao(voo.get("total_duration")),
            data_volta=data_volta,
            bagagem_conhecida=False,
        )
