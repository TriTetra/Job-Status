"""Architecture rules, enforced. Each test names the rule and lists violations.

  1. Configuration is read only in shared/config.py (no os.getenv / dotenv elsewhere).
  2. The LLM HTTP API is called only from shared/llm.py.
  3. Library code logs; it does not print. (CLIs, scripts and `__main__` blocks may print.)
  4. Nothing manipulates sys.path — the repo is an installed package.
  5. core.domain stays pure: it never imports the DB layer.
"""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
APP_DIRS = ["apps/api", "apps/cli", "core", "services", "plugins", "scripts"]
VENDORED = ("services/hiring-agent",)


def _py_files(dirs):
    for d in dirs:
        for path in (ROOT / d).rglob("*.py"):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(VENDORED) or "/migrations/versions/" in rel or "__pycache__" in rel:
                continue
            yield rel, path.read_text(encoding="utf-8-sig")


def _violations(dirs, pattern):
    rx = re.compile(pattern)
    return [
        f"{rel}:{n}: {line.strip()}"
        for rel, src in _py_files(dirs)
        for n, line in enumerate(src.splitlines(), 1)
        if rx.search(line) and not line.lstrip().startswith("#")
    ]


def test_config_only_read_in_shared_config():
    found = _violations(APP_DIRS, r"os\.getenv\(|os\.environ(\.get)?[\[(]|load_dotenv|from dotenv")
    assert not found, "read settings via shared.config.get_settings():\n" + "\n".join(found)


def test_llm_api_only_called_from_shared_llm():
    found = _violations(APP_DIRS, r"chat/completions|openrouter\.ai")
    assert not found, "use shared.llm.get_llm_client():\n" + "\n".join(found)


def test_no_sys_path_manipulation():
    found = _violations(APP_DIRS + ["shared", "tests/unit", "tests/integration", "tests/manual"], r"sys\.path\.(insert|append)")
    assert not found, "install the package (pip install -e .) instead:\n" + "\n".join(found)


def _prints_outside_main(src):
    tree = ast.parse(src)
    main_lines = set()
    for node in tree.body:
        if (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and getattr(node.test.left, "id", None) == "__name__"
        ):
            main_lines.update(range(node.lineno, node.end_lineno + 1))
    return [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "print"
        and node.lineno not in main_lines
    ]


def test_library_code_logs_instead_of_printing():
    library = ["apps/api", "core", "services", "plugins", "shared"]
    found = [
        f"{rel}:{line}"
        for rel, src in _py_files(library)
        if not rel.endswith("cli.py")
        for line in _prints_outside_main(src)
    ]
    assert not found, "use logger = logging.getLogger(__name__):\n" + "\n".join(found)


def test_core_domain_does_not_import_db_layer():
    found = _violations(["core/domain"], r"^\s*(from|import)\s+(core\.db|sqlalchemy)")
    assert not found, "core.domain must stay pure:\n" + "\n".join(found)
