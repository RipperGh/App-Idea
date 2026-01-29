from __future__ import annotations

import sys
from pathlib import Path

from PyQt6 import QtWidgets

from app.gui.main_window import MainWindow
from app.security.env_crypto import EncryptedEnvPaths, load_env_into_process


def bootstrap_env() -> None:
    """Decrypt encrypted .env secrets into memory only."""
    paths = EncryptedEnvPaths(
        plaintext_path=Path(".env"),
        encrypted_path=Path(".env.enc"),
        salt_path=Path(".env.salt"),
    )
    password, accepted = QtWidgets.QInputDialog.getText(
        None,
        "Unlock Secrets",
        "Master password:",
        QtWidgets.QLineEdit.EchoMode.Password,
    )
    if accepted and password:
        load_env_into_process(paths, password)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    bootstrap_env()
    window = MainWindow()
    window.show()
    window.start_workers()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
