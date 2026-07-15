# deploy

`docker-compose.yml` (nginx, backend, postgres, certbot; `worker` llega en R2), configuración de nginx (TLS, cabeceras de seguridad, rate limiting; `X-Accel-Redirect` llega en R2 con las fotos) y scripts de operación.

## Primer despliegue en un dominio nuevo (TLS)

1. Copia `.env.example` a `.env` en la raíz del repo y rellena `BITACORA_DOMAIN`, `LETSENCRYPT_EMAIL` y el resto de variables.
2. Asegúrate de que el DNS del dominio ya apunta a este servidor y que los puertos 80/443 son alcanzables desde internet (Let's Encrypt valida el reto HTTP-01 contra ellos).
3. Ejecuta `deploy/scripts/init-letsencrypt.sh`. El script:
   - genera un certificado autofirmado temporal para que nginx pueda arrancar en 443,
   - levanta nginx,
   - pide el certificado real a Let's Encrypt por webroot,
   - recarga nginx con el certificado definitivo.

A partir de ahí, `docker compose up -d` (desde la raíz) es suficiente en despliegues/reinicios posteriores: el certificado vive en el volumen `letsencrypt` y el servicio `certbot` lo renueva automáticamente cada 12 h (`certbot renew`).

Ver [TASK-R1-003](../tasks/R1/TASK-R1-003.md) (RNF-R1-03/04).
