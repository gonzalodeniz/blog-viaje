"""Implementa: RNF-R1-03 (CSRF).

Patrón de cookie de doble envío: el login emite un token en una cookie
legible por JavaScript (no `HttpOnly`); las mutaciones que dependen de la
cookie de sesión deben repetir ese mismo valor en la cabecera
`X-CSRF-Token`. Un atacante que fuerce una petición cross-site no puede leer
la cookie del sitio ajeno, así que no puede reproducir el valor esperado.
"""

import hmac
import secrets

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "x-csrf-token"


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_token_matches(cookie_value: str | None, header_value: str | None) -> bool:
    if not cookie_value or not header_value:
        return False
    return hmac.compare_digest(cookie_value, header_value)
