import os
import unittest
from datetime import datetime

for key, value in {
    "AMBIENTE": "TEST",
    "CACHE_TTL": "3600",
    "APPSCRIPT_B2C": "https://example.test/b2c",
    "APPSCRIPT_DIVISAO_MERCADO": "https://example.test/market",
    "APPSCRIPT_EXPA": "https://example.test/expa",
    "TOKEN_EXPA": "test-token",
    "DOMINIOS_PERMITIDOS": "example.test",
}.items():
    os.environ.setdefault(key, value)

from app.cache import cache
from app.dto import CriarPreCadastroLead, LeadPreCadastroOutput
from app.utils.payload import montar_dto_persistencia


class LeadPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        cache.store.clear()
        options = {
            "produto": [{"id": 1, "text": "Voluntário Global"}],
            "aiesec_proxima": [{"id": 23, "text": "AIESEC em São Paulo"}],
            "origem": [{"id": 4, "text": "Instagram"}],
            "termo_privacidade": [{"id": 1, "text": "sim"}],
            "categoriaContato": [
                {"id": 8, "text": "home", "status": "active"},
                {"id": 9, "text": "work", "status": "active"},
            ],
        }
        cache.store["metadados_b2c"] = {
            "data": {
                "fields": [
                    {
                        "external_id": external_id,
                        "config": {"settings": {"options": field_options}},
                    }
                    for external_id, field_options in options.items()
                ]
            }
        }
        cache.store["metadados_escritorios"] = {
            "data": {
                "dados": [
                    {
                        "nome": "São Paulo",
                        "oGV": "AIESEC em São Paulo",
                        "oGT": "AIESEC em São Paulo",
                    }
                ]
            }
        }

    def test_contact_types_are_replaced_with_persistence_ids(self) -> None:
        lead = CriarPreCadastroLead(
            nome="Ana Maria",
            sobrenome="Silva Santos",
            dataNascimento=datetime(2000, 1, 2),
            telefone=[
                {"tipo": "home", "numero": "11912345678"},
                {"tipo": "work", "numero": "21912345678"},
            ],
            email=[
                {"tipo": "home", "email": "ana@example.com"},
                {"tipo": "work", "email": "ana.work@example.com"},
            ],
            produto={
                "id": 1,
                "id_expa": 7,
                "titulo": "Voluntário Global",
            },
            autorizacao=1,
            origem={"id": 4, "nome": "Instagram"},
            senha="StrongPass@123",
            comite={"id": 23, "nome": "AIESEC em São Paulo"},
        )
        lead_output = LeadPreCadastroOutput.model_validate(
            {
                **lead.model_dump(mode="json", exclude={"senha"}),
                "id": 98765,
            }
        )

        persisted = montar_dto_persistencia(lead, lead_output)
        payload = persisted.model_dump(mode="json")

        self.assertEqual(
            [contact["tipo"] for contact in payload["telefone"]],
            [8, 9],
        )
        self.assertEqual(
            [contact["tipo"] for contact in payload["email"]],
            [8, 9],
        )
        self.assertEqual(payload["telefone"][0]["numero"], "11912345678")
        self.assertEqual(payload["email"][0]["email"], "ana@example.com")


if __name__ == "__main__":
    unittest.main()
