import os
import unittest
from unittest.mock import patch

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

from pydantic import BaseModel, ValidationError, field_validator

from app.dto.exception.errors import ValidationErrorResponse


class IntegerInput(BaseModel):
    value: int


class CustomInput(BaseModel):
    value: str

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        raise ValueError("custom validation message")


class ValidationErrorResponseTests(unittest.TestCase):
    def test_integer_parsing_error_uses_portuguese_message_without_translation(self) -> None:
        try:
            IntegerInput.model_validate({"value": "8a"})
        except ValidationError as exception:
            with patch(
                "app.dto.exception.errors.GoogleTranslator"
            ) as translator:
                response = ValidationErrorResponse.from_exception(exception)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.error_details[0].msg,
            "Informe um número inteiro válido.",
        )
        translator.assert_not_called()

    def test_translation_failure_returns_portuguese_fallback(self) -> None:
        try:
            CustomInput.model_validate({"value": "invalid"})
        except ValidationError as exception:
            with patch(
                "app.dto.exception.errors.GoogleTranslator",
                side_effect=RuntimeError("translation unavailable"),
            ):
                response = ValidationErrorResponse.from_exception(exception)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.error_details[0].msg, "Valor inválido.")


if __name__ == "__main__":
    unittest.main()
