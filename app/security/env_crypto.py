from __future__ import annotations

import base64
import getpass
import os
from dataclasses import dataclass
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import dotenv_values


@dataclass
class EncryptedEnvPaths:
    plaintext_path: Path
    encrypted_path: Path
    salt_path: Path


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_env_file(paths: EncryptedEnvPaths, password: str) -> None:
    salt = os.urandom(16)
    key = derive_key(password, salt)
    fernet = Fernet(key)
    plaintext = paths.plaintext_path.read_bytes()
    ciphertext = fernet.encrypt(plaintext)
    paths.encrypted_path.write_bytes(ciphertext)
    paths.salt_path.write_bytes(salt)


def decrypt_env_to_memory(paths: EncryptedEnvPaths, password: str) -> dict[str, str]:
    salt = paths.salt_path.read_bytes()
    key = derive_key(password, salt)
    fernet = Fernet(key)
    plaintext = fernet.decrypt(paths.encrypted_path.read_bytes())
    values = dotenv_values(stream=plaintext.decode("utf-8"))
    return {key: value for key, value in values.items() if value is not None}


def load_env_into_process(paths: EncryptedEnvPaths, password: str) -> dict[str, str]:
    env_values = decrypt_env_to_memory(paths, password)
    os.environ.update(env_values)
    return env_values


def cli_encrypt() -> None:
    project_root = Path(__file__).resolve().parents[2]
    paths = EncryptedEnvPaths(
        plaintext_path=project_root / ".env",
        encrypted_path=project_root / ".env.enc",
        salt_path=project_root / ".env.salt",
    )
    password = getpass.getpass("Create master password: ")
    encrypt_env_file(paths, password)
    print("Encrypted .env -> .env.enc and wrote .env.salt")


def cli_decrypt() -> None:
    project_root = Path(__file__).resolve().parents[2]
    paths = EncryptedEnvPaths(
        plaintext_path=project_root / ".env",
        encrypted_path=project_root / ".env.enc",
        salt_path=project_root / ".env.salt",
    )
    password = getpass.getpass("Master password: ")
    env_values = decrypt_env_to_memory(paths, password)
    for key, value in env_values.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    action = os.environ.get("ENV_CRYPTO_ACTION", "encrypt")
    if action == "decrypt":
        cli_decrypt()
    else:
        cli_encrypt()
