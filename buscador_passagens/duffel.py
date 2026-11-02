"""Cliente da API da Duffel (https://duffel.com/docs/api)."""
import re
from datetime import datetime
from decimal import Decimal

import requests

from .modelos import Oferta, Trecho

URL_API = "https://api.duffel.com/air/offer_requests"


class ErroDuffel(Exception):
    pass


def _formatar_duracao(iso: str | None) -> str:
    """Converte 'PT17H25M' ou 'P1DT2H' em '17h 25m' / '26h 0m'."""
    if not iso:
        return ""
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?", iso)
    if not m:
        return iso
    dias, horas, minutos = (int(x or 0) for x in m.groups())
    return f"{dias * 24 + horas}h {minutos}m"


def _malas_despachadas(segmento: dict) -> int:
    """Malas despachadas incluídas para o 1º passageiro neste voo."""
    passageiros = segmento.get("passengers") or []
    if not passageiros:
        return 0
    return sum(b.get("quantity", 0) for b in passageiros[0].get("baggages", [])
               if b.get("type") == "checked")


def _converter_trechos(slice_api: dict) -> list[Trecho]:
    return [
        Trecho(
            origem=s["origin"]["iata_code"],
            destino=s["destination"]["iata_code"],
            partida=datetime.fromisoformat(s["departing_at"]),
            chegada=datetime.fromisoformat(s["arriving_at"]),
            companhia=s["marketing_carrier"]["name"],
            numero_voo=f'{s["marketing_carrier"]["iata_code"]}'
                       f'{s.get("marketing_carrier_flight_number", "")}',
            malas_despachadas=_malas_despachadas(s),
        )
        for s in slice_api["segments"]
    ]


class ClienteDuffel:
    def __init__(self, token: str, timeout: int = 60):
        self.timeout = timeout
        self.sessao = requests.Session()
        self.sessao.headers.update({
            "Authorization": f"Bearer {token}",
            "Duffel-Version": "v2",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def buscar(self, origem: str, destino: str, data_ida: str,
               data_volta: str | None = None, adultos: int = 1,
               max_conexoes: int = 1, cabine: str = "economy") -> list[Oferta]:
        slices = [{"origin": origem, "destination": destino,
                   "departure_date": data_ida}]
        if data_volta:
            slices.append({"origin": destino, "destination": origem,
                           "departure_date": data_volta})
        corpo = {
            "data": {
                "slices": slices,
                "passengers": [{"type": "adult"} for _ in range(adultos)],
                "cabin_class": cabine,
                "max_connections": max_conexoes,
            }
        }
        resposta = self.sessao.post(
            URL_API, params={"return_offers": "true"},
            json=corpo, timeout=self.timeout,
        )
        if resposta.status_code >= 400:
            raise ErroDuffel(f"Erro {resposta.status_code}: {resposta.text[:300]}")

        ofertas_api = resposta.json()["data"].get("offers", [])
        return [self._converter(o, destino, data_ida, data_volta) for o in ofertas_api]

    @staticmethod
    def _converter(oferta: dict, destino: str, data_ida: str,
                   data_volta: str | None = None) -> Oferta:
        slices = oferta["slices"]
        resultado = Oferta(
            preco=Decimal(oferta["total_amount"]),
            moeda=oferta["total_currency"],
            companhia=oferta["owner"]["name"],
            destino=destino,
            data_ida=data_ida,
            trechos=_converter_trechos(slices[0]),
            duracao=_formatar_duracao(slices[0].get("duration")),
        )
        if data_volta and len(slices) > 1:
            resultado.data_volta = data_volta
            resultado.trechos_volta = _converter_trechos(slices[1])
            resultado.duracao_volta = _formatar_duracao(slices[1].get("duration"))
        return resultado
