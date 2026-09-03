from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = (ROOT / "bot.py", ROOT / "admin_api" / "app.py")


def _local_import_roots(source: Path) -> set[str]:
    tree = ast.parse(source.read_text())
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


def _dockerignore_patterns() -> list[str]:
    text = (ROOT / ".dockerignore").read_text()
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _is_dockerignored(rel_posix: str, patterns: list[str]) -> bool:
    from fnmatch import fnmatch

    name = rel_posix.rsplit("/", 1)[-1]
    parts = rel_posix.split("/")
    for pattern in patterns:
        if fnmatch(rel_posix, pattern) or fnmatch(name, pattern):
            return True
        if pattern.rstrip("/") in parts:
            return True
    return False


def test_dockerfile_copies_the_application_tree():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "COPY . ." in dockerfile, (
        "Copy the app tree in Dockerfile (COPY . .) instead of listing files. "
        "A file list misses new modules and crash-loops the bot."
    )


def test_entrypoint_local_imports_are_shipped_in_the_image():
    patterns = _dockerignore_patterns()
    missing: list[str] = []
    ignored: list[str] = []
    for source in ENTRYPOINTS:
        for name in sorted(_local_import_roots(source)):
            file_path = ROOT / f"{name}.py"
            package_path = ROOT / name / "__init__.py"
            rel = f"{name}.py" if file_path.is_file() else f"{name}/__init__.py"
            if not file_path.is_file() and not package_path.is_file():
                missing.append(rel)
            elif _is_dockerignored(rel, patterns):
                ignored.append(rel)
    assert missing == [], f"entrypoint imports missing on disk: {missing}"
    assert ignored == [], (
        f"entrypoint imports are dockerignored and will not be in the image: {ignored}"
    )
