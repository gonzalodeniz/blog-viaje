# TASK-R1-003 — TLS y cabeceras de seguridad en nginx

- **WP:** WP-R1-1
- **Requisitos:** RNF-R1-03, RNF-R1-04
- **Estado:** cerrada
- **Rama:** feature/TASK-R1-003

## Objetivo

nginx sirve siempre por HTTPS (TLS 1.2/1.3, certificado Let's Encrypt vía certbot con renovación automática), redirige HTTP→HTTPS, y añade en toda respuesta las cabeceras de seguridad exigidas (CSP estricta sin `unsafe-inline`, HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`). `/api/auth/*` queda con *rate limiting* por IP, listo para cuando WP-R1-2 implemente los endpoints de login.

## Contexto y decisiones

- **Bootstrap certbot (problema del huevo y la gallina):** nginx no puede arrancar con un `server { listen 443 ssl; }` si el certificado aún no existe, pero certbot necesita nginx sirviendo el reto HTTP-01 en el puerto 80 para emitirlo. Se resuelve con el patrón estándar de la comunidad (p. ej. wmnnd/nginx-certbot): `deploy/scripts/init-letsencrypt.sh` genera un certificado autofirmado temporal (1 día) en el volumen `letsencrypt`, arranca nginx con él, pide el certificado real a Let's Encrypt por webroot y recarga nginx. Es un paso manual de un solo uso por dominio nuevo — se documenta en `deploy/README.md`.
- **Plantillas nginx con `envsubst`:** la imagen base `nginx:1.27-alpine` ya trae el mecanismo oficial de `docker-entrypoint.d` que renderiza `/etc/nginx/templates/*.template` → `/etc/nginx/conf.d/*` sustituyendo únicamente variables de entorno definidas (no toca las variables internas de nginx como `$host` o `$remote_addr`, que no son variables de entorno). Se usa para inyectar `${BITACORA_DOMAIN}` sin añadir scripting propio.
- **No verificable de extremo a extremo en este entorno:** no hay un dominio público apuntando aquí, así que la emisión real contra Let's Encrypt no se puede probar. Se verificó la mecánica completa con un certificado autofirmado (`openssl req -x509`) sustituyendo al de Let's Encrypt: `nginx -t` en verde, nginx arranca y sirve en 443, `curl -k` confirma las cinco cabeceras y el TLS handshake, y `curl` a `http://localhost/algo` devuelve 301 a `https://`. La emisión real y la renovación automática de certbot quedan pendientes de probar en el primer despliegue con dominio real.
- **CSRF** (la otra mitad de RNF-R1-03) no se aborda aquí: no existe todavía ningún endpoint de mutación — llega con WP-R1-2.
- **Compresión (gzip/brotli) y `client_max_body_size`** mencionados en SPEC-MASTER §13 para nginx quedan fuera de alcance: no los exige RNF-R1-03/04 y no hay subida de ficheros que los necesite todavía (llega en R2).

## Definition of Done

- [x] Código con docstring/comentario `Implementa: RNF-R1-03, RNF-R1-04` en la plantilla nginx y en el script de bootstrap
- [x] Test de humo: `docker compose up -d` con certificado autofirmado de prueba → `curl -k https://localhost/healthz` devuelve 200 con las cabeceras esperadas; `curl http://localhost/` devuelve 301
- [x] Cobertura ≥ 80 % en el código tocado (no aplica: cambio de infraestructura sin código Python/TS; sin regresión en la cobertura existente)
- [x] Revisión de seguridad (TLS 1.2/1.3 únicamente, sin protocolos/cifrados débiles; CSP sin `unsafe-inline`; certificados y claves privadas fuera del repo, en el volumen `letsencrypt`; `.env.example` sin valores reales)
- [ ] `python tools/traceability.py --check --release R1` en verde — sigue en rojo (ver TASK-R1-002): quedan RF/RNF de otros WPs de R1 sin test. RNF-R1-03 y RNF-R1-04 no tienen test de spec propio porque son configuración de infraestructura verificada manualmente (ver nota de bootstrap); no se puede ejercitar TLS/HSTS reales desde pytest sin un dominio válido — se retomará con un test de integración cuando exista el entorno de staging.
- [x] Commits con prefijo `[TASK-R1-003]`

## Notas de implementación

- `deploy/nginx/templates/default.conf.template`: dos `server{}` — uno en 80 (reto ACME + redirección 301 a HTTPS) y otro en 443 (TLS, cabeceras de seguridad, `limit_req` en `/api/auth/`, proxy a backend, estáticos del frontend).
- `deploy/nginx/Dockerfile`: elimina el `default.conf` que trae la imagen base y copia la plantilla a `/etc/nginx/templates/` en vez de a `conf.d/` directamente, dejando que el `docker-entrypoint.d` oficial haga el `envsubst`.
- `deploy/docker-compose.yml`: nginx publica también el puerto 443 y monta `letsencrypt` (solo lectura) y `certbot-webroot` (solo lectura); nuevo servicio `certbot` con el bucle de renovación (`certbot renew` cada 12 h) montando los mismos volúmenes en lectura/escritura.
- `deploy/scripts/init-letsencrypt.sh`: bootstrap de un solo uso por dominio, documentado en `deploy/README.md`.
