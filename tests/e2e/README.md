# tests/e2e

Suite Playwright contra el `docker compose` completo. Cada test anota los requisitos que cubre:

```ts
test.info().annotations.push({ type: "spec", description: "RF-R1-03" });
```

Flujos obligatorios por release: SPEC-MASTER §11.
