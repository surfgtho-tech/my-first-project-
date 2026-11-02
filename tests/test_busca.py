import unittest

from buscador_passagens.busca import buscar_flexivel, gerar_datas, mais_barata_por_dia
from buscador_passagens.duffel import ClienteDuffel, _formatar_duracao
from buscador_passagens.simulado import ClienteSimulado


class TestBusca(unittest.TestCase):
    def test_gerar_datas(self):
        self.assertEqual(gerar_datas("2026-12-07", "2026-12-10"),
                         ["2026-12-07", "2026-12-08", "2026-12-09", "2026-12-10"])

    def test_data_invertida(self):
        with self.assertRaises(ValueError):
            gerar_datas("2026-12-10", "2026-12-07")

    def test_ordena_por_preco(self):
        ofertas = buscar_flexivel(ClienteSimulado(), "DUB", ["BKK", "HKT"],
                                  "2026-12-07", "2026-12-10")
        precos = [o.preco for o in ofertas]
        self.assertEqual(precos, sorted(precos))
        self.assertEqual(len(mais_barata_por_dia(ofertas)), 4)

    def test_duracao(self):
        self.assertEqual(_formatar_duracao("PT17H25M"), "17h 25m")
        self.assertEqual(_formatar_duracao("P1DT2H"), "26h 0m")

    def test_converter_resposta_duffel(self):
        oferta_api = {
            "total_amount": "612.40", "total_currency": "EUR",
            "owner": {"name": "Qatar Airways"},
            "slices": [{"duration": "PT18H5M", "segments": [
                {"origin": {"iata_code": "DUB"}, "destination": {"iata_code": "DOH"},
                 "departing_at": "2026-12-07T10:00:00", "arriving_at": "2026-12-07T19:00:00",
                 "marketing_carrier": {"name": "Qatar Airways", "iata_code": "QR"},
                 "marketing_carrier_flight_number": "18"},
                {"origin": {"iata_code": "DOH"}, "destination": {"iata_code": "BKK"},
                 "departing_at": "2026-12-07T21:00:00", "arriving_at": "2026-12-08T07:05:00",
                 "marketing_carrier": {"name": "Qatar Airways", "iata_code": "QR"},
                 "marketing_carrier_flight_number": "832"},
            ]}],
        }
        o = ClienteDuffel._converter(oferta_api, "BKK", "2026-12-07")
        self.assertEqual(str(o.preco), "612.40")
        self.assertEqual(o.rota, "DUB → DOH → BKK")
        self.assertEqual(o.conexoes, 1)
        self.assertEqual(o.trechos[1].numero_voo, "QR832")


if __name__ == "__main__":
    unittest.main()
