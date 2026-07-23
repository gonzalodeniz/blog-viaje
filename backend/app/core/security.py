"""Implementa: RNF-R1-02.

Hashing de contraseñas con Argon2id y política mínima de contraseña. La
comprobación contra una lista local de contraseñas filtradas queda para la
tarea que fije contraseñas nuevas de verdad (CLI create-user / cambio de
contraseña, RF-R1-10 / RF-R1-20).
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

MIN_PASSWORD_LENGTH = 12

# RNF-R1-02: Argon2id, memoria >= 19 MiB, 2 iteraciones, paralelismo 1.
_hasher = PasswordHasher(time_cost=2, memory_cost=19 * 1024, parallelism=1)

# Hash señuelo precalculado: permite ejecutar una verificación Argon2id de
# duración equivalente cuando el usuario no existe, para no filtrar por
# timing si una cuenta existe o no (RF-R1-04).
_DUMMY_HASH = _hasher.hash("contraseña-señuelo-para-comparación-de-tiempo")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    return True


def verify_dummy_password() -> None:
    """Ejecuta una verificación contra el hash señuelo (ver _DUMMY_HASH)."""
    verify_password("cualquier-contraseña", _DUMMY_HASH)


def validate_password_policy(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"La contraseña debe tener al menos {MIN_PASSWORD_LENGTH} caracteres")
