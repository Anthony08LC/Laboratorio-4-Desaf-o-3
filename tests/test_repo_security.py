"""Verifica que las credenciales locales no quedan versionadas en Git."""

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None or not (ROOT / ".git").exists(),
    reason="Requiere git y un repositorio clonado",
)


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_env_file_is_ignored_by_git():
    result = _git("check-ignore", "-q", ".env")
    assert result.returncode == 0, ".env debe estar excluido por .gitignore"


def test_env_file_is_not_tracked_by_git():
    result = _git("ls-files", "--error-unmatch", ".env")
    assert result.returncode != 0, ".env no debe estar en el índice de Git"


def test_env_example_is_tracked_and_not_ignored():
    assert _git("check-ignore", "-q", ".env.example").returncode != 0
    assert _git("ls-files", "--error-unmatch", ".env.example").returncode == 0


def test_env_example_contains_no_secret_values():
    secret_keys = ("GEMINI_API_KEY", "ELEVENLABS_API_KEY")
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(secret_keys):
            assert stripped.split("=", 1)[1] == "", f"Valor no vacío: {stripped.split('=')[0]}"
