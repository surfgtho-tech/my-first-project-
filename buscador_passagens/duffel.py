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
               adultos: int = 1, max_conexoes: int = 1,
               cabine: str = "economy") -> list[Oferta]:
        corpo = {
            "data": {
                "slices": [{
                    "origin": origem,
                    "destination": destino,
                    "departure_date": data_ida,
                }],
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
        return [self._converter(o, destino, data_ida) for o in ofertas_api]

    @staticmethod
    def _converter(oferta: dict, destino: str, data_ida: str) -> Oferta:
        trecho_api = oferta["slices"][0]
        trechos = [
            Trecho(
                origem=s["origin"]["iata_code"],
                destino=s["destination"]["iata_code"],
                partida=datetime.fromisoformat(s["departing_at"]),
                chegada=datetime.fromisoformat(s["arriving_at"]),
                companhia=s["marketing_carrier"]["name"],
                numero_voo=f'{s["marketing_carrier"]["iata_code"]}'
                           f'{s.get("marketing_carrier_flight_number", "")}',
            )
            for s in trecho_api["segments"]
        ]
        return Oferta(
            preco=Decimal(oferta["total_amount"]),
            moeda=oferta["total_currency"],
            companhia=oferta["owner"]["name"],
            destino=destino,
            data_ida=data_ida,
            trechos=trechos,
            duracao=_formatar_duracao(trecho_api.get("duration")),
        )
