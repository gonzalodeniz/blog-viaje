# SPEC-R1 — Release 1 «Cimientos»

Versión 1.0 · 13 de julio de 2026 · Estado: **congelada**
Deriva de [SPEC-MASTER.md](SPEC-MASTER.md) v1.1. Cambios posteriores requieren nueva versión con changelog.

## 1. Objetivo de la release

Blog funcional privado: el propietario puede autenticarse, crear temas y viajes, escribir con un editor rico, subir fotos de forma simple y leer sus relatos. Todo desplegable con `docker compose up -d` tras nginx con TLS. El acceso es recuperable siempre desde la terminal del servidor.

**No incluye** (queda en R2/R3): pipeline avanzado de imágenes (variantes/WebP/SSIM), collage público, lightbox, visibilidad pública por foto, búsqueda full-text. En R1 la portada muestra un diseño limpio con el nombre del blog y el formulario de login (equivalente al caso "sin fotos públicas" de RF-R2-03). La subida de fotos en R1 es simple: original + una versión web razonable para incrustar; el pipeline completo llega en R2.

## 2. Requisitos funcionales

### 2.1 Autenticación y acceso

| ID | Requisito | Prioridad | WP |
|---|---|---|---|
| RF-R1-01 | El sistema exige autenticación con nombre de usuario y contraseña para acceder a cualquier contenido que no esté marcado como público. | M | WP-R1-2 |
| RF-R1-02 | Sesiones con cookies `HttpOnly`, `Secure`, `SameSite=Lax`; expiración deslizante por inactividad (por defecto 30 días con *remember me*, 24 h sin él, configurable) y expiración absoluta máxima de 90 días desde el login. | M | WP-R1-2 |
| RF-R1-03 | Bloqueo temporal por usuario: 5 fallos consecutivos en ventana de 15 min → bloqueo 15 min; backoff exponencial 15 → 30 → 60 min (máx. 60). El contador se reinicia con login correcto o al expirar la ventana. | M | WP-R1-2 |
| RF-R1-04 | Durante el bloqueo se informa del tiempo restante sin revelar si el usuario existe (mensaje genérico idéntico para usuario inexistente y contraseña errónea). | M | WP-R1-2 |
| RF-R1-05 | Registro de todos los intentos de login (éxito, fallo, bloqueo) con timestamp, usuario declarado, IP y user-agent; consultables desde el panel de administración. | M | WP-R1-2, WP-R1-5 |
| RF-R1-06 | Cierre de sesión manual y revocación de todas las sesiones activas de un usuario desde el panel de administración. | S | WP-R1-2, WP-R1-5 |
| RF-R1-07 | Roles `admin` (todo) y `lector` (solo lectura). El primer usuario creado es admin. | M | WP-R1-2 |
| RF-R1-20 | Cambio de contraseña propio (con contraseña actual). Con `must_change_password` activo, pantalla intermedia obligatoria antes de cualquier otra acción; el cambio revoca el resto de sesiones. | M | WP-R1-2 |

**Detalle del flujo de bloqueo (RF-R1-03/04):** ver SPEC-MASTER §8. El contador se evalúa sobre `login_attempts` por `username_claimed`; al 5.º fallo se inserta `account_locks` con `locked_until = now() + 15 min × 2^(consecutive_locks-1)` (tope 60). nginx aplica además rate limiting por IP en `/api/auth/login` (~10 req/min).

### 2.2 CLI de rescate

| ID | Requisito | Prioridad | WP |
|---|---|---|---|
| RF-R1-08 | CLI ejecutable solo desde la terminal del servidor (`docker compose exec backend bitacora-cli <cmd>`), nunca expuesta por HTTP. | M | WP-R1-3 |
| RF-R1-09 | `reset-password <usuario>`: contraseña temporal segura mostrada una única vez por stdout; fuerza cambio en el siguiente login. | M | WP-R1-3 |
| RF-R1-10 | `create-user <usuario> [--admin]`: alta o rehabilitación con contraseña interactiva; permite recuperar el control total del sistema. | M | WP-R1-3 |
| RF-R1-11 | `unlock <usuario>` levanta bloqueos; `list-users` muestra usuarios, rol, estado y último acceso. | M | WP-R1-3 |
| RF-R1-12 | Toda acción de la CLI se registra en `audit_log` con origen `cli`. | M | WP-R1-3 |

Comandos completos en SPEC-MASTER §10 (incluye `disable`/`enable`, `sessions-revoke`; `regenerate-derived` se implementa en R2).

### 2.3 Vista de lector

| ID | Requisito | Prioridad | WP |
|---|---|---|---|
| RF-R1-13 | Listado de viajes (portada, título, tema, fechas, extracto) ordenado cronológicamente. | M | WP-R1-4, WP-R1-6 |
| RF-R1-14 | La página de un viaje muestra el texto con todo su formato y todas las fotos. | M | WP-R1-4, WP-R1-6 |

### 2.4 Panel de administración y editor

| ID | Requisito | Prioridad | WP |
|---|---|---|---|
| RF-R1-15 | CRUD de viajes: título, tema, fechas del viaje, etiquetas, lugar, foto de portada, estado borrador/publicado, despublicar y borrar. | M | WP-R1-4, WP-R1-5 |
| RF-R1-16 | CRUD de temas (nombre, slug, descripción, color); organizan artículos y carpetas de fotos. | M | WP-R1-4, WP-R1-5 |
| RF-R1-17 | Editor rico (TipTap/ProseMirror): tipografías autoalojadas curadas, tamaños, colores de texto y resaltado, negrita/cursiva/subrayado/tachado, H2–H4, alineaciones (izquierda/centro/derecha/justificado), listas, citas, separadores, enlaces, deshacer/rehacer. | M | WP-R1-5 |
| RF-R1-18 | Contenido guardado como JSON ProseMirror y renderizado como HTML sanitizado en servidor con lista blanca de etiquetas/atributos/estilos. | M | WP-R1-4, WP-R1-5 |
| RF-R1-19 | Autoguardado de borradores cada pocos segundos y aviso al salir con cambios sin guardar. | S | WP-R1-5 |

## 3. Requisitos no funcionales

| ID | Requisito | WP |
|---|---|---|
| RNF-R1-01 | Seguridad OWASP Top 10 + ASVS L2; sin secretos en el repo; `pip-audit`/`npm audit`, `bandit`, `semgrep`, `trivy`, `gitleaks` en CI; hallazgos altos/críticos bloquean la release. | WP-R1-1 (transversal) |
| RNF-R1-02 | Argon2id (≥ 19 MiB, 2 iteraciones, paralelismo 1); comparaciones en tiempo constante; mínimo 12 caracteres; comprobación contra lista local de contraseñas filtradas. | WP-R1-2 |
| RNF-R1-03 | CSRF en todas las mutaciones; cabeceras desde nginx: CSP estricta sin `unsafe-inline`, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`. | WP-R1-1, WP-R1-2 |
| RNF-R1-04 | HTTP → HTTPS (TLS 1.2/1.3) en nginx con Let's Encrypt autorenovado; objetivo A en SSL Labs. | WP-R1-1 |
| RNF-R1-05 | Cobertura ≥ 80 % (líneas y ramas) en backend y frontend, bloqueante en CI; e2e Playwright para todos los flujos críticos. | WP-R1-1 (transversal) |
| RNF-R1-06 | Trazabilidad bidireccional verificada en CI (`tools/traceability.py`). | WP-R1-1 |
| RNF-R1-07 | `docker compose up -d` levanta todo; migraciones Alembic automáticas; imágenes versionadas, usuario no root, FS de solo lectura donde sea posible. | WP-R1-1 |
| RNF-R1-08 | Logs y auditoría sin contraseñas/tokens/cookies; retención de `login_attempts` ≥ 90 días con purga automática; `audit_log` permanente. | WP-R1-2 |

## 4. Criterios de aceptación (Gherkin)

```gherkin
# RF-R1-03 — Bloqueo temporal
Dado un usuario "gonzalo" con contraseña correcta "S3gura!Larga"
Cuando se envían 5 intentos con contraseña incorrecta en menos de 15 minutos
Entonces el 6.º intento devuelve "cuenta bloqueada temporalmente" aunque la contraseña sea correcta
Y tras 15 minutos el login con la contraseña correcta vuelve a funcionar
Y un segundo bloqueo consecutivo dura 30 minutos

# RF-R1-09 / RF-R1-20 — Reset por terminal con cambio forzado
Dado que se han perdido todas las contraseñas
Cuando el operador ejecuta "bitacora-cli reset-password gonzalo" en el servidor
Entonces la salida muestra una contraseña temporal una única vez
Y el siguiente login con ella obliga a establecer una nueva contraseña antes de cualquier otra acción

# RF-R1-01 — Privado por defecto
Dado un viaje publicado
Cuando un visitante sin sesión solicita el listado o el artículo por API o URL directa
Entonces recibe 401 y ningún contenido del viaje

# RF-R1-17/18 — Editor y sanitización
Dado un artículo escrito con colores, alineaciones y tipografías del conjunto curado
Cuando se guarda y se vuelve a abrir como lector
Entonces el formato se conserva exactamente
Y cualquier etiqueta/atributo/estilo fuera de la lista blanca se descarta en servidor
```

Flujos e2e obligatorios de R1: login correcto/incorrecto; bloqueo a los 5 fallos y desbloqueo por tiempo y por CLI; reset de contraseña por CLI con cambio forzado; crear tema y viaje; escribir texto con estilos, colores y alineaciones; leer el viaje autenticado; verificar 401 sin sesión.

## 5. Definition of Done de la release

- Todos los RF con prioridad M implementados y con tests trazados (`@pytest.mark.spec` / anotación Playwright).
- Todas las puertas de CI en verde: cobertura ≥ 80 %, e2e, seguridad, trazabilidad (`tools/traceability.py --check --release R1`).
- Despliegue verificado desde cero en un servidor limpio siguiendo SPEC-MASTER §13.
- Tag `v1.0.0` con changelog generado desde los IDs de tarea.
