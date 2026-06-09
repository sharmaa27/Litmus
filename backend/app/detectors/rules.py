"""AST-based detector. This is the primary engine.

It parses the code into a syntax tree, so it only ever fires on *real* calls
and assignments — never on text that merely appears inside a comment or a
string literal. That single property is the main reason it scores far better
than the regex baseline it is measured against.
"""
from __future__ import annotations

import ast

from .base import Finding

_SECRET_NAMES = (
    "password", "passwd", "pwd", "secret", "api_key", "apikey",
    "token", "access_key", "secret_key", "private_key", "auth_token",
)
_EXECUTE_METHODS = {"execute", "executemany", "executescript", "raw", "mogrify"}
_WEAK_HASHES = {"md5", "sha1"}


def _is_dynamic_string(node: ast.AST) -> bool:
    """True when the node builds a string at runtime from non-constant parts —
    the shape of an injectable query."""
    if isinstance(node, ast.JoinedStr):  # f-string
        return any(isinstance(v, ast.FormattedValue) for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr == "format"  # "...".format(x)
    return False


def _name_looks_secret(name: str) -> bool:
    low = name.lower()
    return any(s in low for s in _SECRET_NAMES)


class AstDetector:
    name = "ast"
    version = "ast-1.0"

    def analyze(self, code: str) -> list[Finding]:
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            line = exc.lineno or 1
            return [Finding("PARSE-ERROR", line, f"Could not parse: {exc.msg}")]

        out: list[Finding] = []
        for node in ast.walk(tree):
            self._sql(node, out)
            self._secret(node, out)
            self._eval(node, out)
            self._pickle(node, out)
            self._yaml(node, out)
            self._shell(node, out)
            self._hash(node, out)
        # Deterministic, de-duplicated ordering.
        return sorted(set(out), key=lambda f: (f.line, f.rule_id))

    # --- individual rules -------------------------------------------------

    def _sql(self, node: ast.AST, out: list[Finding]) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in _EXECUTE_METHODS and node.args:
                if _is_dynamic_string(node.args[0]):
                    out.append(Finding("PY-SQL-001", node.lineno,
                                       "Dynamic string passed to a query call."))

    def _secret(self, node: ast.AST, out: list[Finding]) -> None:
        targets = []
        value = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            return
        if not (isinstance(value, ast.Constant) and isinstance(value.value, str)):
            return
        if value.value == "":
            return
        for t in targets:
            name = t.id if isinstance(t, ast.Name) else (
                t.attr if isinstance(t, ast.Attribute) else None)
            if name and _name_looks_secret(name):
                out.append(Finding("PY-SECRET-001", node.lineno,
                                   f"'{name}' assigned a string literal."))

    def _eval(self, node: ast.AST, out: list[Finding]) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                out.append(Finding("PY-EVAL-001", node.lineno,
                                   f"{node.func.id}() executes arbitrary code."))

    def _pickle(self, node: ast.AST, out: list[Finding]) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "pickle"
                    and node.func.attr in {"load", "loads"}):
                out.append(Finding("PY-PICKLE-001", node.lineno,
                                   "pickle deserialization of untrusted data."))

    def _yaml(self, node: ast.AST, out: list[Finding]) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "yaml"
                    and node.func.attr == "load"):
                safe = any(k.arg == "Loader" for k in node.keywords)
                if not safe:
                    out.append(Finding("PY-YAML-001", node.lineno,
                                       "yaml.load without an explicit Loader."))

    def _shell(self, node: ast.AST, out: list[Finding]) -> None:
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            return
        attr = node.func.attr
        owner = node.func.value
        owner_name = owner.id if isinstance(owner, ast.Name) else None
        if owner_name == "os" and attr in {"system", "popen"}:
            out.append(Finding("PY-SHELL-001", node.lineno,
                               f"os.{attr} runs a shell command."))
        elif owner_name == "subprocess":
            if any(k.arg == "shell" and isinstance(k.value, ast.Constant)
                   and k.value.value is True for k in node.keywords):
                out.append(Finding("PY-SHELL-001", node.lineno,
                                   "subprocess called with shell=True."))

    def _hash(self, node: ast.AST, out: list[Finding]) -> None:
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if (isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "hashlib"
                    and node.func.attr in _WEAK_HASHES):
                out.append(Finding("PY-HASH-001", node.lineno,
                                   f"{node.func.attr} is a weak hash."))
