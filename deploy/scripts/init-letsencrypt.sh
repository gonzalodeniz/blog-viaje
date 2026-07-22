#!/usr/bin/env sh
# Implementa: RNF-R1-04.
#
# Bootstrap de TLS para un dominio nuevo (patrón estándar certbot+nginx:
# certificado autofirmado temporal -> nginx arranca en 443 -> certbot pide
# el certificado real por webroot -> recarga nginx). Ejecutar UNA sola vez
# por dominio, desde cualquier ruta, con .env ya relleno en la raíz del repo.
# Los despliegues siguientes solo necesitan "docker compose up -d": el
# certificado real ya vive en el volumen "letsencrypt" y certbot lo renueva.
set -eu

cd "$(dirname "$0")/../.."

if [ ! -f .env ]; then
    echo "Falta .env en la raíz del repo (copia .env.example y rellénalo)." >&2
    exit 1
fi

# shellcheck disable=SC1091
. ./.env

if [ -z "${BITACORA_DOMAIN:-}" ] || [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
    echo "Define BITACORA_DOMAIN y LETSENCRYPT_EMAIL en .env" >&2
    exit 1
fi

echo "== 1/4: certificado autofirmado temporal para ${BITACORA_DOMAIN} =="
docker compose run --rm --entrypoint sh certbot -c "
    mkdir -p /etc/letsencrypt/live/${BITACORA_DOMAIN} &&
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
        -keyout /etc/letsencrypt/live/${BITACORA_DOMAIN}/privkey.pem \
        -out /etc/letsencrypt/live/${BITACORA_DOMAIN}/fullchain.pem \
        -subj '/CN=localhost'
"

echo "== 2/4: arrancando nginx con el certificado temporal =="
docker compose up -d nginx

echo "== 3/4: solicitando el certificado real a Let's Encrypt =="
docker compose run --rm --entrypoint certbot certbot certonly \
    --webroot -w /var/www/certbot \
    -d "${BITACORA_DOMAIN}" \
    --email "${LETSENCRYPT_EMAIL}" --agree-tos --no-eff-email --force-renewal

echo "== 4/4: recargando nginx con el certificado real =="
docker compose exec nginx nginx -s reload

echo "Listo: https://${BITACORA_DOMAIN} debería servir con un certificado válido."
