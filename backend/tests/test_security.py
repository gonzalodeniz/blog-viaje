"""Implementa: RNF-R1-02."""

import pytest

from app.core.security import (
    hash_password,
    validate_password_policy,
    verify_dummy_password,
    verify_password,
)


@pytest.mark.spec("RNF-R1-02")
def test_hash_password_no_devuelve_el_texto_plano() -> None:
    password = "una-contraseña-larga-123"
    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$argon2id$")


@pytest.mark.spec("RNF-R1-02")
def test_verify_password_correcta_e_incorrecta() -> None:
    hashed = hash_password("una-contraseña-larga-123")

    assert verify_password("una-contraseña-larga-123", hashed) is True
    assert verify_password("otra-contraseña-distinta", hashed) is False


@pytest.mark.spec("RNF-R1-02")
def test_verify_dummy_password_no_lanza_excepcion() -> None:
    verify_dummy_password()


@pytest.mark.spec("RNF-R1-02")
def test_password_de_menos_de_12_caracteres_se_rechaza() -> None:
    with pytest.raises(ValueError):
        validate_password_policy("corta123")


@pytest.mark.spec("RNF-R1-02")
def test_password_de_12_o_mas_caracteres_se_acepta() -> None:
    validate_password_policy("doce-caracteres-o-mas")
