"""Shared pytest setup.

Layout:
  tests/unit/         pure functions, no I/O — always run
  tests/smoke/        import / wiring checks, no DB or network — always run
  tests/integration/  live DB, network or LLM — auto-marked `integration`,
                      skipped by default, run with `pytest -m integration`
  tests/manual/       standalone verification scripts (python tests/manual/x.py),
                      never collected by pytest
"""

from pathlib import Path

import pytest

_INTEGRATION_DIR = Path(__file__).parent / "integration"

collect_ignore = ["manual"]


def pytest_collection_modifyitems(items):
    for item in items:
        if _INTEGRATION_DIR in Path(item.fspath).parents:
            item.add_marker(pytest.mark.integration)
