"""Implementa: RNF-R1-03."""

import pytest

from app.core.csrf import csrf_token_matches, generate_csrf_token


@pytest.mark.spec("RNF-R1-03")
def test_csrf_token_matches_con_valores_iguales() -> None:
    token = generate_csrf_token()
    assert csrf_token_matches(token, token) is True


@pytest.mark.spec("RNF-R1-03")
@pytest.mark.parametrize(
    ("cookie", "header"),
    [
        (None, "algo"),
        ("algo", None),
        (None, None),
        ("", ""),
        ("abc", "xyz"),
    ],
)
def test_csrf_token_matches_falla_si_falta_o_difiere(cookie: str | None, header: str | None) -> None:
    assert csrf_token_matches(cookie, header) is False


@pytest.mark.spec("RNF-R1-03")
def test_generate_csrf_token_produce_valores_distintos() -> None:
    assert generate_csrf_token() != generate_csrf_token()
