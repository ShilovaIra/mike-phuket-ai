from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _local_modules_imported_by_bot() -> set[str]:
    tree = ast.parse((ROOT / "bot.py").read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
    return {
        name
        for name in names
        if (ROOT / f"{name}.py").is_file() or (ROOT / name / "__init__.py").is_file()
    }


def test_dockerfile_copies_local_modules_imported_by_bot():
    dockerfile = (ROOT / "Dockerfile").read_text()
    missing = sorted(
        name for name in _local_modules_imported_by_bot() if name not in dockerfile
    )
    assert missing == [], f"Dockerfile does not copy bot imports: {missing}"
