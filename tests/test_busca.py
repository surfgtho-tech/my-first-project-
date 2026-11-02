import unittest
from unittest.mock import patch

from buscador_passagens.busca import buscar_flexivel, gerar_datas, mais_barata_por_dia
from buscador_passagens.alerta import ConfigEmailFaltando, enviar_email, montar_email
from buscador_passagens.duffel import ClienteDuffel, _formatar_duracao
from buscador_passagens.serpapi import ClienteSerpApi
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
                 "marketing_carrier_flight_number": "18",
                 "passengers": [{"baggages": [{"type": "checked", "quantity": 1}]}]},
                {"origin": {"iata_code": "DOH"}, "destination": {"iata_code": "BKK"},
                 "departing_at": "2026-12-07T21:00:00", "arriving_at": "2026-12-08T07:05:00",
                 "marketing_carrier": {"name": "Qatar Airways", "iata_code": "QR"},
                 "marketing_carrier_flight_number": "832",
                 "passengers": [{"baggages": [{"type": "carry_on", "quantity": 1}]}]},
            ]}],
        }
        o = ClienteDuffel._converter(oferta_api, "BKK", "2026-12-07")
        self.assertEqual(str(o.preco), "612.40")
        self.assertEqual(o.rota, "DUB → DOH → BKK")
        self.assertEqual(o.conexoes, 1)
        self.assertEqual(o.trechos[1].numero_voo, "QR832")
        self.assertEqual(o.trechos[0].malas_despachadas, 1)
        self.assertFalse(o.bagagem_incluida)  # 2º voo não tem mala despachada


    def test_ida_e_volta(self):
        ofertas = buscar_flexivel(ClienteSimulado(), "DUB", ["BKK"],
                                  "2026-12-07", "2026-12-08",
                                  volta_inicio="2026-12-08", volta_fim="2026-12-09")
        # combinações válidas: 07↔08, 07↔09, 08↔09 (volta igual à ida é ignorada)
        self.assertEqual(set(mais_barata_por_dia(ofertas)),
                         {"2026-12-07 ↔ 2026-12-08", "2026-12-07 ↔ 2026-12-09",
                          "2026-12-08 ↔ 2026-12-09"})
        self.assertTrue(all(o.trechos_volta for o in ofertas))

    def test_filtro_bagagem(self):
        ofertas = buscar_flexivel(ClienteSimulado(), "DUB", ["BKK"],
                                  "2026-12-07", "2026-12-10", so_com_bagagem=True)
        self.assertTrue(ofertas)
        self.assertTrue(all(o.bagagem_incluida for o in ofertas))

    def test_email(self):
        ofertas = buscar_flexivel(ClienteSimulado(), "DUB", ["BKK"], "2026-12-07", "2026-12-07")
        assunto, corpo = montar_email(ofertas, "DUB → BKK")
        self.assertIn(str(ofertas[0].preco), assunto)
        self.assertIn("1. ", corpo)

    def test_intervalo_volta(self):
        self.assertEqual(gerar_datas("2027-01-05", "2027-01-15", 2),
                         ["2027-01-05", "2027-01-07", "2027-01-09",
                          "2027-01-11", "2027-01-13", "2027-01-15"])
        self.assertEqual(gerar_datas("2027-01-05", "2027-01-08", 2),
                         ["2027-01-05", "2027-01-07", "2027-01-08"])


class TestSerpApi(unittest.TestCase):
    @patch("buscador_passagens.serpapi.requests.get")
    def test_converter(self, get):
        get.return_value.status_code = 200
        get.return_value.content = b"x"
        get.return_value.json.return_value = {
            "best_flights": [{"price": 912, "total_duration": 1090, "flights": [
                {"departure_airport": {"id": "DUB", "time": "2026-12-08 10:15"},
                 "arrival_airport": {"id": "DOH", "time": "2026-12-08 19:40"},
                 "airline": "Qatar Airways", "flight_number": "QR 18"},
                {"departure_airport": {"id": "DOH", "time": "2026-12-08 21:10"},
                 "arrival_airport": {"id": "MNL", "time": "2026-12-09 11:25"},
                 "airline": "Qatar Airways", "flight_number": "QR 934"},
            ]}],
            "other_flights": [],
        }
        ofertas = ClienteSerpApi("chave").buscar("DUB", "MNL", "2026-12-08", "2027-01-07")
        params = get.call_args.kwargs["params"]
        self.assertEqual(params["type"], 1)
        self.assertEqual(params["return_date"], "2027-01-07")
        o = ofertas[0]
        self.assertEqual(str(o.preco), "912")
        self.assertEqual(o.rota, "DUB → DOH → MNL")
        self.assertEqual(o.duracao, "18h 10m")
        self.assertEqual(o.trechos[1].numero_voo, "QR934")
        self.assertIn("ver no site", o.resumo())


class TestEnvioEmail(unittest.TestCase):
    @patch.dict("os.environ", {"ALERTA_EMAIL": "a@x.com, b@x.com",
                               "BREVO_API_KEY": "chave", "REMETENTE_EMAIL": "eu@x.com"}, clear=True)
    @patch("buscador_passagens.alerta.requests.post")
    def test_brevo(self, post):
        post.return_value.status_code = 201
        self.assertEqual(enviar_email("assunto", "corpo"), ["a@x.com", "b@x.com"])
        corpo = post.call_args.kwargs["json"]
        self.assertEqual(corpo["to"], [{"email": "a@x.com"}, {"email": "b@x.com"}])
        self.assertEqual(corpo["sender"]["email"], "eu@x.com")
        self.assertEqual(post.call_args.kwargs["headers"]["api-key"], "chave")

    @patch.dict("os.environ", {"ALERTA_EMAIL": "a@x.com"}, clear=True)
    def test_sem_configuracao(self):
        with self.assertRaises(ConfigEmailFaltando):
            enviar_email("assunto", "corpo")


if __name__ == "__main__":
    unittest.main()
