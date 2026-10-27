"""Every backend module must import — guards against dead references when
code is deleted or moved. No DB/network: engines are created lazily."""

import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]

# (source dir, import prefix)
PACKAGES = [
    ("core", "core"),
    ("services", "services"),
    ("plugins", "plugins"),
    ("apps/api/app", "apps.api.app"),
    ("apps/cli", "apps.cli"),
]
SKIP_PARTS = {"migrations", "__pycache__"}


def _module_names():
    names = set()
    for src, prefix in PACKAGES:
        for path in (ROOT / src).rglob("*.py"):
            rel = path.relative_to(ROOT / src).with_suffix("")
            if SKIP_PARTS & set(rel.parts):
                continue
            parts = [p for p in rel.parts if p != "__init__"]
            names.add(".".join([prefix, *parts]))
    return sorted(names)


@pytest.fixture(autouse=True)
def _encryption_key(monkeypatch):
    if not os.environ.get("TOKEN_ENCRYPTION_KEY"):
        from cryptography.fernet import Fernet

        monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())


@pytest.mark.parametrize("module", _module_names())
def test_module_imports(module):
    importlib.import_module(module)


def _cold_import(module):
    # Run from a neutral directory: the import must work through the installed
    # package (`pip install -e .`), not because the repo root happens to be cwd.
    return subprocess.run(
        [sys.executable, "-c", f"import {module}"],
        cwd=ROOT / "tests", capture_output=True, text=True, timeout=120,
    )


# Entry points, plus modules whose import order used to matter
# (core.domain <-> core.db.models was circular).
@pytest.mark.parametrize("module", [
    "apps.api.app.main",
    "apps.cli.main",
    "core.domain",
    "core.db.models",
    "services.job_intelligence.application.scoring_service",
])
def test_cold_import(module):
    result = _cold_import(module)
    assert result.returncode == 0, result.stderr[-2000:]
