#!/usr/bin/env bash
# Setup satu-jalan di VM (Oracle Always Free / VPS Ubuntu).
# Pakai:  sudo bash deploy/setup.sh <domain-anda>
#   contoh: sudo bash deploy/setup.sh namaku.duckdns.org
set -euo pipefail

DOMAIN="${1:-${DOMAIN:-}}"
if [ -z "$DOMAIN" ]; then
  echo "Pakai: sudo bash deploy/setup.sh <domain>   (mis. namaku.duckdns.org)" >&2
  exit 1
fi

# Jalankan dari root repo (skrip ada di deploy/)
cd "$(dirname "$0")/.."

# 1) Docker (+ compose plugin) bila belum ada
if ! command -v docker >/dev/null 2>&1; then
  echo "==> Memasang Docker..."
  curl -fsSL https://get.docker.com | sh
fi

# 2) Berkas .env (dibuat sekali; token dibuat otomatis)
if [ ! -f .env ]; then
  cp .env.example .env
  if command -v python3 >/dev/null 2>&1; then
    TOKEN="$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')"
  else
    TOKEN="$(openssl rand -base64 32 | tr -d '/+=' | cut -c1-40)"
  fi
  sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" .env
  sed -i "s|^CATATAN_TOKEN=.*|CATATAN_TOKEN=${TOKEN}|" .env
  echo "==> .env dibuat. DOMAIN=${DOMAIN}"
  echo "==> CATATAN_TOKEN=${TOKEN}"
  echo "    (simpan token ini — dipakai aplikasi saat pertama membuka)"
else
  echo "==> .env sudah ada, tidak diubah."
fi

# 3) Buka port 80/443 di firewall OS (best-effort; Oracle Console tetap wajib)
if command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  ufw allow 80/tcp || true; ufw allow 443/tcp || true
fi
if command -v iptables >/dev/null 2>&1; then
  iptables -C INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 80 -j ACCEPT || true
  iptables -C INPUT -p tcp --dport 443 -j ACCEPT 2>/dev/null || iptables -I INPUT -p tcp --dport 443 -j ACCEPT || true
  command -v netfilter-persistent >/dev/null 2>&1 && netfilter-persistent save || true
fi

# 4) Jalankan
echo "==> Membangun & menjalankan aplikasi..."
docker compose up -d --build

echo ""
echo "Selesai. Buka:  https://${DOMAIN}"
echo "PENTING: buka juga port 80 & 443 di firewall cloud-mu"
echo "         (GCP: VPC > Firewall / tag http-server & https-server;"
echo "          Oracle: VCN > Security List / NSG),"
echo "         dan pastikan ${DOMAIN} (DuckDNS) mengarah ke IP publik VM ini."
