#!/usr/bin/env python3
"""Genera docs/TRACEABILITY.md y valida la trazabilidad bidireccional (SPEC-MASTER §3.3).

Implementa: RNF-R1-06.

Uso:
    python tools/traceability.py                  # solo genera la matriz
    python tools/traceability.py --check          # además valida (exit 1 si hay huecos)
    python tools/traceability.py --check --release R1

Validaciones en modo --check (para la release indicada, o todas las que tengan
SPEC congelada si no se indica ninguna):
  1. Todo RF/RNF tiene al menos un test asociado (marker pytest o anotación Playwright).
  2. Toda TASK con Estado: cerrada tiene al menos un commit [TASK-...].
  3. Todo commit [TASK-...] apunta a una TASK que existe en tasks/.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "TRACEABILITY.md"

REQ_RE = re.compile(r"\bRN?F-R\d+-\d{2}\b")
WP_RE = re.compile(r"\bWP-R\d+-\d+\b")
TASK_RE = re.compile(r"\bTASK-R\d+-\d{3}\b")
COMMIT_TASK_RE = re.compile(r"^\[(TASK-R\d+-\d{3})\]")
# @pytest.mark.spec("RF-R1-03") · annotations.push({ type: "spec", description: "RF-R1-03" })
TEST_SPEC_RE = re.compile(
    r"""(?:pytest\.mark\.spec\(\s*["'](RN?F-R\d+-\d{2})["']\s*\)"""
    r"""|type:\s*["']spec["']\s*,\s*description:\s*["'](RN?F-R\d+-\d{2})["'])"""
)
DOCSTRING_IMPL_RE = re.compile(r"Implementa:\s*([^\n\"']+)")

CODE_DIRS = ("backend", "frontend", "tools")
TEST_DIRS = ("backend", "frontend", "tests")
CODE_EXTS = {".py", ".ts", ".tsx"}


@dataclass
class Task:
    task_id: str
    wp: set[str] = field(default_factory=set)
    reqs: set[str] = field(default_factory=set)
    estado: str = "pendiente"


def release_of(item_id: str) -> str:
    return item_id.split("-")[-2]


def parse_specs() -> dict[str, set[str]]:
    """Devuelve release → conjunto de RF/RNF definidos en su SPEC congelada o borrador."""
    reqs: dict[str, set[str]] = defaultdict(set)
    for spec in sorted((ROOT / "specs").glob("SPEC-R*.md")):
        release = spec.stem.split("-")[1]
        for req in REQ_RE.findall(spec.read_text(encoding="utf-8")):
            if release_of(req) == release:
                reqs[release].add(req)
    return reqs


def parse_plans() -> dict[str, set[str]]:
    """Devuelve WP → RF/RNF que desarrolla, leyendo la sección de cada WP en plan/."""
    wp_reqs: dict[str, set[str]] = defaultdict(set)
    for plan in sorted((ROOT / "plan").glob("PLAN-R*.md")):
        text = plan.read_text(encoding="utf-8")
        # Filas de tabla '| WP-R1-2 | ... |': los requisitos se atribuyen solo
        # al primer WP de la línea (el propio); los demás son dependencias.
        for line in text.splitlines():
            wps = WP_RE.findall(line)
            if wps:
                wp_reqs[wps[0]].update(REQ_RE.findall(line))
    return wp_reqs


def parse_tasks() -> dict[str, Task]:
    tasks: dict[str, Task] = {}
    for path in sorted((ROOT / "tasks").rglob("TASK-R*.md")):
        text = path.read_text(encoding="utf-8")
        task = Task(task_id=path.stem)
        task.wp = set(WP_RE.findall(text))
        task.reqs = set(REQ_RE.findall(text))
        m = re.search(r"\*\*Estado:\*\*\s*(\w+)", text)
        if m:
            task.estado = m.group(1).lower()
        tasks[task.task_id] = task
    return tasks


def parse_commits() -> dict[str, list[str]]:
    """Devuelve TASK → lista de hashes cortos; incluye commits sin tarea bajo '?'."""
    out = subprocess.run(
        ["git", "log", "--pretty=%h\t%s"], cwd=ROOT, capture_output=True, text=True
    )
    commits: dict[str, list[str]] = defaultdict(list)
    for line in out.stdout.splitlines():
        sha, _, subject = line.partition("\t")
        m = COMMIT_TASK_RE.match(subject)
        if m:
            commits[m.group(1)].append(sha)
        elif not re.match(r"^(\[SDD\]|Merge|Revert|fixup!|squash!)", subject):
            commits["?"].append(f"{sha} {subject[:60]}")
    return commits


def scan_files(dirs: tuple[str, ...], pattern: re.Pattern) -> dict[str, set[str]]:
    """Devuelve RF/RNF → conjunto de rutas relativas donde aparece el patrón."""
    hits: dict[str, set[str]] = defaultdict(set)
    for d in dirs:
        base = ROOT / d
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if path.suffix not in CODE_EXTS or "node_modules" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for m in pattern.finditer(text):
                groups = [g for g in m.groups() if g]
                payload = groups[0] if groups else m.group(0)
                for req in REQ_RE.findall(payload):
                    hits[req].add(str(path.relative_to(ROOT)))
    return hits


def build_matrix() -> str:
    reqs = parse_specs()
    wp_reqs = parse_plans()
    tasks = parse_tasks()
    commits = parse_commits()
    tests = scan_files(TEST_DIRS, TEST_SPEC_RE)
    code = scan_files(CODE_DIRS, DOCSTRING_IMPL_RE)

    req_wps: dict[str, set[str]] = defaultdict(set)
    for wp, rs in wp_reqs.items():
        for r in rs:
            req_wps[r].add(wp)
    req_tasks: dict[str, set[str]] = defaultdict(set)
    for task in tasks.values():
        for r in task.reqs:
            req_tasks[r].add(task.task_id)

    lines = [
        "# Matriz de trazabilidad",
        "",
        "**Generado por `tools/traceability.py` — no editar a mano.**",
        "",
    ]
    for release in sorted(reqs):
        lines += [f"## {release}", "", "| Requisito | WP | Tareas | Commits | Código | Tests |", "|---|---|---|---|---|---|"]
        for req in sorted(reqs[release]):
            row = [
                req,
                ", ".join(sorted(req_wps.get(req, []))) or "—",
                ", ".join(sorted(req_tasks.get(req, []))) or "—",
                ", ".join(sha for t in sorted(req_tasks.get(req, [])) for sha in commits.get(t, [])) or "—",
                ", ".join(sorted(code.get(req, []))) or "—",
                ", ".join(sorted(tests.get(req, []))) or "—",
            ]
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")
    if commits.get("?"):
        lines += ["## Commits sin tarea", ""] + [f"- `{c}`" for c in commits["?"]] + [""]
    return "\n".join(lines)


def check(release: str | None) -> list[str]:
    reqs = parse_specs()
    tasks = parse_tasks()
    commits = parse_commits()
    tests = scan_files(TEST_DIRS, TEST_SPEC_RE)
    errors: list[str] = []

    releases = [release] if release else sorted(reqs)
    for rel in releases:
        for req in sorted(reqs.get(rel, [])):
            if req not in tests:
                errors.append(f"{req}: sin ningún test asociado (marker/anotación 'spec')")
    for task in tasks.values():
        if release and release_of(task.task_id) != release:
            continue
        if task.estado == "cerrada" and task.task_id not in commits:
            errors.append(f"{task.task_id}: cerrada sin commits '[{task.task_id}]'")
        if not task.reqs:
            errors.append(f"{task.task_id}: no referencia ningún RF/RNF")
    for task_id in commits:
        if task_id != "?" and task_id not in tasks:
            errors.append(f"commits '[{task_id}]' sin fichero de tarea en tasks/")
    for c in commits.get("?", []):
        errors.append(f"commit sin tarea ni prefijo [SDD]: {c}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="valida y falla si hay huecos")
    parser.add_argument("--release", help="limita la validación a una release (p. ej. R1)")
    args = parser.parse_args()

    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(build_matrix(), encoding="utf-8")
    print(f"Matriz generada en {OUTPUT.relative_to(ROOT)}")

    if args.check:
        errors = check(args.release)
        if errors:
            print(f"\nTrazabilidad incompleta ({len(errors)} errores):", file=sys.stderr)
            for e in errors:
                print(f"  - {e}", file=sys.stderr)
            return 1
        print("Trazabilidad completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
