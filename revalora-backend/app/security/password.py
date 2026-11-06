"""Hash y verificación de contraseñas (Argon2 mediante pwdlib)."""

from pwdlib import PasswordHash

_hasher = PasswordHash.recommended()


def hashear_password(password: str) -> str:
    return _hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)
