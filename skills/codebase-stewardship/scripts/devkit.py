#!/usr/bin/env python3
"""devkit - zero-dependency helpers for a modular-monolith Python codebase.

Subcommands
  scaffold <src_file>   Create/extend a unit-test file with one failing stub per
                        public function/method x standard case.
  audit <src_dir>       List public functions/methods that have no test (by name).
  boundaries            Check modular-monolith import rules and module cycles.

Conventions assumed (override with flags):
  source root   app/           tests root   tests/unit/   (mirrors the source tree)
  modules       app/modules/<module>/     util   app/util/     core   app/core/

Test naming that scaffold writes and audit recognises:
  function        test_<function>__<case>
  method          test_<class_snake>__<method>__<case>
  constructor     test_<class_snake>__init__<case>

Limits (be honest about what this proves): audit and scaffold work by NAME only.
They prove a test exists, not that it is any good. See references/testing-guide.md.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

CASES_CALLABLE = [
    ("happy_path", "typical valid input gives the expected result"),
    ("boundary", "empty / minimum / maximum / off-by-one / unicode inputs"),
    ("invalid_input", "wrong type or value gives the documented error"),
    ("failure_path", "a dependency fails or raises: documented behaviour"),
]


# --------------------------------------------------------------------------- helpers
def snake(name: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def _decorator_names(node) -> set[str]:
    out = set()
    for d in node.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        if isinstance(target, ast.Name):
            out.add(target.id)
        elif isinstance(target, ast.Attribute):
            out.add(target.attr)
    return out


def _is_protocol_or_abc(cls: ast.ClassDef) -> bool:
    for b in cls.bases:
        n = b.id if isinstance(b, ast.Name) else getattr(b, "attr", "")
        if n in {"Protocol", "ABC"}:
            return True
    return False


def _params(fn) -> list[str]:
    names = [a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs]
    return [n for n in names if n not in {"self", "cls"}]


def public_targets(path: Path):
    """Yield (class_name|None, name, is_async, params) for public callables.

    Protocol/ABC classes and abstract methods are skipped: they are covered by
    contract tests against every implementation, not by unit tests.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    fn_types = (ast.FunctionDef, ast.AsyncFunctionDef)
    for node in tree.body:
        if isinstance(node, fn_types) and not node.name.startswith("_"):
            out.append((None, node.name, isinstance(node, ast.AsyncFunctionDef), _params(node)))
        elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            if _is_protocol_or_abc(node):
                continue
            for sub in node.body:
                if not isinstance(sub, fn_types):
                    continue
                if "abstractmethod" in _decorator_names(sub):
                    continue
                is_init = sub.name == "__init__"
                if sub.name.startswith("_") and not (is_init and _params(sub)):
                    continue
                out.append((node.name, sub.name, isinstance(sub, ast.AsyncFunctionDef), _params(sub)))
    return out


def label_for(cls: str | None, name: str) -> str:
    base = "init" if name == "__init__" else name
    return f"{snake(cls)}__{base}" if cls else base


STUB_MARK = "TODO: write this test"


def existing_keys(test_path: Path, include_stubs: bool = True) -> set[tuple[str, ...]]:
    """Name-prefix keys of test functions already present in a test file.

    include_stubs=False ignores untouched scaffold stubs (they still contain the
    TODO marker), so audit does not count a placeholder as a real test.
    """
    keys: set[tuple[str, ...]] = set()
    if not test_path.exists():
        return keys
    text = test_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            if not include_stubs and STUB_MARK in (ast.get_source_segment(text, node) or ""):
                continue
            parts = node.name[5:].split("__")
            for i in range(1, len(parts) + 1):
                keys.add(tuple(parts[:i]))
    return keys


def is_covered(keys, cls, name) -> bool:
    label = label_for(cls, name)
    return tuple(label.split("__")) in keys


def test_path_for(src_file: Path, src_root: Path, tests_root: Path) -> Path:
    rel = src_file.resolve().relative_to(src_root.resolve())
    return tests_root / rel.parent / f"test_{rel.stem}.py"


def dotted(src_file: Path, src_root: Path) -> str:
    rel = src_file.resolve().relative_to(src_root.resolve().parent)
    return ".".join(rel.with_suffix("").parts)


def iter_source_files(src_dir: Path):
    for p in sorted(src_dir.rglob("*.py")):
        if p.name == "__init__.py" or "__pycache__" in p.parts:
            continue
        yield p


# --------------------------------------------------------------------------- scaffold
def render_stub(cls, name, is_async, params) -> str:
    label = label_for(cls, name)
    target = f"{cls}.{name}" if cls else name
    sig = ", ".join(params)
    chunks = []
    for case, hint in CASES_CALLABLE:
        fn = f"test_{label}__{case}"
        head = "@pytest.mark.asyncio\nasync def" if is_async else "def"
        arrange = f"build {cls} with fakes" if cls else "build inputs"
        chunks.append(
            f'{head} {fn}():\n'
            f'    """{target}({sig}): {hint}."""\n'
            f"    # Arrange: {arrange}\n"
            f"    # Act:     call {target}\n"
            f"    # Assert:   check the RESULT (not how it was computed)\n"
            f'    pytest.fail("TODO: write this test, or delete it and say why in the PR")\n'
        )
    return "\n\n".join(chunks)


def cmd_scaffold(a) -> int:
    src = Path(a.src_file)
    src_root, tests_root = Path(a.src_root), Path(a.tests_root)
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        return 2
    try:
        tpath = test_path_for(src, src_root, tests_root)
        mod = dotted(src, src_root)
    except ValueError:
        print(f"error: {src} is not under source root {src_root}", file=sys.stderr)
        return 2
    targets = public_targets(src)
    if not targets:
        print(f"{src}: no public functions/methods to test (nothing written)")
        return 0
    keys = existing_keys(tpath)
    missing = [t for t in targets if not is_covered(keys, t[0], t[1])]
    if not missing:
        print(f"{tpath}: every public callable already has a test (nothing written)")
        return 0
    body = "\n\n".join(render_stub(*t) for t in missing)
    if a.dry_run:
        print(f"[dry-run] would write {len(missing)} callable(s) x {len(CASES_CALLABLE)} cases to {tpath}")
        return 0
    tpath.parent.mkdir(parents=True, exist_ok=True)
    if tpath.exists():
        with tpath.open("a", encoding="utf-8") as f:
            f.write("\n\n" + body + "\n")
        verb = "appended to"
    else:
        names = sorted({t[0] or t[1] for t in targets})
        header = (
            f'"""Unit tests for {mod}.\n\n'
            "Generated by devkit.py. Every stub FAILS on purpose until you fill it in:\n"
            "a green placeholder would be a false signal.\n"
            '"""\n'
            "import pytest\n\n"
            f"from {mod} import {', '.join(names)}  # noqa: F401\n\n\n"
        )
        tpath.write_text(header + body + "\n", encoding="utf-8")
        verb = "created"
    print(f"{verb} {tpath}: {len(missing)} callable(s), {len(missing) * len(CASES_CALLABLE)} stub(s)")
    return 0


# --------------------------------------------------------------------------- audit
def cmd_audit(a) -> int:
    src_root, tests_root = Path(a.src_dir), Path(a.tests_root)
    total = missing_total = 0
    problems = []
    for f in iter_source_files(src_root):
        targets = public_targets(f)
        if not targets:
            continue
        tpath = test_path_for(f, src_root, tests_root)
        keys = existing_keys(tpath, include_stubs=False)
        miss = [t for t in targets if not is_covered(keys, t[0], t[1])]
        total += len(targets)
        missing_total += len(miss)
        if miss:
            problems.append((f, tpath, miss, tpath.exists()))
    for f, tpath, miss, exists in problems:
        state = "" if exists else "  (test file missing)"
        print(f"{f}{state}")
        for cls, name, *_ in miss:
            print(f"    - {cls + '.' if cls else ''}{name}")
    pct = 100.0 * (total - missing_total) / total if total else 100.0
    print(f"\n{total - missing_total}/{total} public callables have a filled-in test by name ({pct:.0f}%).")
    print("Name match only: this does not prove the tests are meaningful.")
    return 1 if missing_total else 0


# --------------------------------------------------------------------------- boundaries
def _file_package(path: Path, root: Path) -> list[str]:
    rel = path.resolve().relative_to(root.resolve())
    return list(rel.parent.parts)


def _init_binds(pkg_dir: Path, name: str) -> bool:
    """True if pkg_dir/__init__.py itself binds `name` (re-export, def, class, assignment).

    Python resolves `from pkg import name` to that attribute first, so it is a symbol
    import of the public API, not an import of the submodule `pkg.name`.
    """
    init = pkg_dir / "__init__.py"
    if not init.is_file():
        return False
    for node in ast.parse(init.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ImportFrom) or isinstance(node, ast.Import):
            if any((al.asname or al.name.split(".")[0]) == name for al in node.names):
                return True
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return True
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return True
    return False


def _import_targets(path: Path, root: Path) -> list[list[str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    pkg = _file_package(path, root)
    out: list[list[str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(al.name.split(".") for al in node.names)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module.split(".") if node.module else []
            if node.level:
                cut = len(pkg) - (node.level - 1)
                if cut < 0:
                    continue
                base = pkg[:cut] + mod
            else:
                base = mod
            out.append(base)
            for al in node.names:
                # `from app.modules import billing` names a submodule only if it exists on
                # disk; `from app.modules.billing import search` names a symbol, not a path.
                cand = root.joinpath(*base, al.name)
                if (cand.is_dir() or cand.with_suffix(".py").is_file()) and not _init_binds(
                    root.joinpath(*base), al.name
                ):
                    out.append(base + [al.name])
    return out


def cmd_boundaries(a) -> int:
    root = Path(a.root)
    pkg, mods, util, core = a.pkg, a.modules, a.util, a.core
    pkg_dir = root / pkg
    if not pkg_dir.exists():
        print(f"error: {pkg_dir} not found", file=sys.stderr)
        return 2
    violations: list[str] = []
    edges: dict[str, set[str]] = {}

    for f in sorted(pkg_dir.rglob("*.py")):
        if "__pycache__" in f.parts:
            continue
        rel = f.resolve().relative_to(pkg_dir.resolve()).parts  # inside package
        area = rel[0] if rel else ""
        owner = rel[1] if area == mods and len(rel) > 2 else None
        for tgt in _import_targets(f, root):
            if not tgt or tgt[0] != pkg or len(tgt) < 2:
                continue
            t_area = tgt[1]
            where = f"{f.relative_to(root)}"
            if area in {util, core} and t_area == mods:
                violations.append(f"{where}: '{area}' must not import modules ({'.'.join(tgt)})")
            if area == util and t_area == core:
                violations.append(f"{where}: util must not import core ({'.'.join(tgt)})")
            if owner and t_area == mods and len(tgt) >= 3:
                other = tgt[2]
                if other != owner:
                    edges.setdefault(owner, set()).add(other)
                    if len(tgt) > 3:
                        violations.append(
                            f"{where}: module '{owner}' imports private path "
                            f"'{'.'.join(tgt)}'; import only '{pkg}.{mods}.{other}' (its public API)"
                        )

    # cycle detection between modules
    state: dict[str, int] = {}
    stack: list[str] = []

    def dfs(n: str):
        state[n] = 1
        stack.append(n)
        for m in sorted(edges.get(n, ())):
            if state.get(m, 0) == 0:
                dfs(m)
            elif state.get(m) == 1:
                cyc = stack[stack.index(m):] + [m]
                violations.append("module cycle: " + " -> ".join(cyc))
        stack.pop()
        state[n] = 2

    for n in sorted(edges):
        if state.get(n, 0) == 0:
            dfs(n)

    seen = set()
    uniq = [v for v in violations if not (v in seen or seen.add(v))]
    for v in uniq:
        print("VIOLATION:", v)
    print(f"\n{len(uniq)} boundary violation(s).")
    return 1 if uniq else 0


# --------------------------------------------------------------------------- cli
def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="devkit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scaffold", help="write failing test stubs for a source file")
    s.add_argument("src_file")
    s.add_argument("--src-root", default="app")
    s.add_argument("--tests-root", default="tests/unit")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_scaffold)

    s = sub.add_parser("audit", help="list public callables without tests")
    s.add_argument("src_dir", nargs="?", default="app")
    s.add_argument("--tests-root", default="tests/unit")
    s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("boundaries", help="check modular-monolith import rules")
    s.add_argument("--root", default=".")
    s.add_argument("--pkg", default="app")
    s.add_argument("--modules", default="modules")
    s.add_argument("--util", default="util")
    s.add_argument("--core", default="core")
    s.set_defaults(fn=cmd_boundaries)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
