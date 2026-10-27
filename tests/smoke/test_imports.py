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
    ("career_os", "career_os"),
    ("apps/api/app", "app"),
    ("apps/cli", "apps.cli"),
]
SKIP_PARTS = {"hiring-agent", "migrations", "__pycache__"}


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
    return subprocess.run(
        [sys.executable, "-c", f"import sys; sys.path[:0] = ['.', 'apps/api']; import {module}"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )


@pytest.mark.parametrize("module", ["app.main", "apps.cli.main"])
def test_entry_point_cold_import(module):
    result = _cold_import(module)
    assert result.returncode == 0, result.stderr[-2000:]


@pytest.mark.xfail(strict=True, reason="known bug: core.domain <-> core.db.models circular import on cold start")
def test_core_domain_cold_import():
    result = _cold_import("core.domain")
    assert result.returncode == 0, result.stderr[-2000:]
