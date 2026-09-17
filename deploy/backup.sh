#!/usr/bin/env bash
# Backup data.db aplikasi (SQLite) dengan aman + rotasi.
#
# Pakai (dari root repo, saat aplikasi jalan via docker compose):
#   bash deploy/backup.sh                 # simpan ke ./backups/
#   BACKUP_DIR=/mnt/backup bash deploy/backup.sh
#
# Jadwalkan harian via cron (jam 02:00):
#   0 2 * * * cd /root/Catatan_Keuangan && bash deploy/backup.sh >> backups/backup.log 2>&1
set -euo pipefail

cd "$(dirname "$0")/.."
BACKUP_DIR="${BACKUP_DIR:-./backups}"
KEEP="${KEEP:-14}"                # simpan 14 backup terakhir
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/data-${STAMP}.db"
mkdir -p "$BACKUP_DIR"

# Salin file DB. WAL aktif -> gunakan .backup SQLite agar konsisten bila sqlite3 ada.
if command -v docker >/dev/null 2>&1 && docker compose ps app >/dev/null 2>&1; then
  docker compose cp app:/data/data.db "$OUT"          # dari container aplikasi
elif command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "${CATATAN_DB:-data.db}" ".backup '$OUT'"    # salinan konsisten
else
  cp "${CATATAN_DB:-data.db}" "$OUT"                   # fallback salin langsung
fi

echo "Backup: $OUT ($(du -h "$OUT" | cut -f1))"

# Rotasi: hapus yang tertua, sisakan $KEEP
ls -1t "${BACKUP_DIR}"/data-*.db 2>/dev/null | tail -n +$((KEEP + 1)) | xargs -r rm -f
echo "Backup tersimpan: $(ls -1 "${BACKUP_DIR}"/data-*.db 2>/dev/null | wc -l) berkas (maks ${KEEP})."
