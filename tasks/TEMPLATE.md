# TASK-Rn-nnn — <Título imperativo y concreto>

- **WP:** WP-Rn-x
- **Requisitos:** RF-Rn-xx, RNF-Rn-xx
- **Estado:** pendiente <!-- pendiente | en curso | cerrada -->
- **Rama:** feature/TASK-Rn-nnn

## Objetivo

Qué existe al terminar esta tarea que no existía antes, en una o dos frases.

## Contexto y decisiones

Notas de diseño relevantes, enlaces a secciones de la spec o ADRs.

## Definition of Done

- [ ] Código con docstring `Implementa: <IDs>` en los módulos/funciones que materializan requisitos
- [ ] Tests con `@pytest.mark.spec("...")` / anotación Playwright `{ type: "spec" }`
- [ ] Cobertura ≥ 80 % en el código tocado
- [ ] Revisión de seguridad (checklist OWASP aplicable al cambio)
- [ ] `python tools/traceability.py --check` en verde
- [ ] Commits con prefijo `[TASK-Rn-nnn]`
