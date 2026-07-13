# SPEC-R3 — Release 3 «Descubrimiento»

Versión 0.1 · 13 de julio de 2026 · Estado: **borrador** (se congela al iniciar la release)
Deriva de [SPEC-MASTER.md](SPEC-MASTER.md) v1.1.

## 1. Objetivo de la release

Encontrar cualquier viaje en segundos desde cualquier dispositivo: búsqueda full-text en español, filtros, archivo cronológico, PWA y pulido de rendimiento, accesibilidad y operación (backups, observabilidad).

## 2. Requisitos funcionales

| ID | Requisito | Prioridad |
|---|---|---|
| RF-R3-01 | Búsqueda global desde cualquier página: texto completo (título, cuerpo, tema, etiquetas, lugares) con tolerancia a acentos y erratas; resultados con miniatura y extracto resaltado. | M |
| RF-R3-02 | Filtros combinables por tema, año y etiqueta; archivo cronológico agrupado por año. | M |
| RF-R3-03 | Navegación entre viajes relacionados (mismo tema) al final de cada artículo. | S |
| RF-R3-04 | Mapa interactivo opcional con los viajes geolocalizados. | C |

Implementación de búsqueda prevista: PostgreSQL `tsvector` (configuración `spanish`) + `unaccent` + `pg_trgm` sobre `trips.search_vector` (SPEC-MASTER §7.1/§7.3).

## 3. Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF-R3-01 | Accesibilidad WCAG 2.1 AA: teclado completo (incluido lightbox), alt obligatorio, contraste verificado. |
| RNF-R3-02 | Búsqueda < 300 ms (p95) con 500 artículos y 20 000 fotos. |
| RNF-R3-03 | Backups diarios automatizados (`pg_dump` + volumen media con restic/rsync, retención 7d/4s/12m); restauración documentada y ensayada por test. |
| RNF-R3-04 | Observabilidad: `/healthz`, `/readyz`, logs JSON estructurados, métricas básicas (cola de imágenes, logins fallidos), integrable con Checkmk. |

## 4. Referencias de diseño

- Criterios Gherkin: SPEC-MASTER §12 (RF-R3-01).
- Operación y backups: SPEC-MASTER §13.
- PWA: la web es responsive e instalable como PWA (SPEC-MASTER §2.2).
