"""Verifica que el pipeline de CI declara las puertas de calidad obligatorias.

No se puede ejercitar un run real de GitHub Actions desde pytest, así que
estas pruebas comprueban de forma estática que el workflow y la configuración
de cobertura declaran lo exigido por la spec (RNF-R1-01/05/06).

Implementa: RNF-R1-01, RNF-R1-05, RNF-R1-06.
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
BACKEND_PYPROJECT = (ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8")
FRONTEND_VITE_CONFIG = (ROOT / "frontend" / "vite.config.ts").read_text(encoding="utf-8")


@pytest.mark.spec("RNF-R1-01")
@pytest.mark.parametrize(
    "tool",
    ["bandit", "pip-audit", "semgrep", "npm audit", "trivy", "gitleaks"],
)
def test_ci_ejecuta_todas_las_herramientas_de_seguridad_obligatorias(tool: str) -> None:
    assert tool.lower() in WORKFLOW.lower()


@pytest.mark.spec("RNF-R1-05")
def test_ci_ejecuta_tests_con_cobertura_bloqueante_en_backend_y_frontend() -> None:
    assert "pytest" in WORKFLOW
    assert "--cov-fail-under=80" in BACKEND_PYPROJECT

    assert "vitest" in WORKFLOW.lower() or "npm test" in WORKFLOW.lower()
    assert "thresholds" in FRONTEND_VITE_CONFIG
    assert "lines: 80" in FRONTEND_VITE_CONFIG
    assert "branches: 80" in FRONTEND_VITE_CONFIG


@pytest.mark.spec("RNF-R1-06")
def test_ci_ejecuta_la_verificacion_de_trazabilidad() -> None:
    assert "traceability.py" in WORKFLOW
    assert "--check" in WORKFLOW
