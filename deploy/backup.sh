#!/usr/bin/env bash
#
# CT Sale — kunlik zaxira nusxa.
#
# Cron: 0 3 * * * /usr/local/bin/ctsale-backup >> /var/log/ctsale-backup.log 2>&1
#
# Baza `pg_dump -Fc` (siqilgan, tanlab tiklash mumkin) bilan,
# media esa tar.gz bilan zaxiralanadi. Media bazada emas, shuning
# uchun ikkalasi ham kerak.

set -euo pipefail

APP_DIR="${CTSALE_APP_DIR:-/opt/ctsale/app}"
BACKUP_DIR="${CTSALE_BACKUP_DIR:-/opt/ctsale/backups}"
DB_NAME="${CTSALE_DB_NAME:-ctsale}"
DB_USER="${CTSALE_DB_USER:-ctsale}"
RETENTION_DAYS="${CTSALE_RETENTION_DAYS:-14}"

DATE="$(date +%F)"
mkdir -p "$BACKUP_DIR"

echo "[$(date -Is)] Zaxira boshlandi"

# --- Baza ---
DB_FILE="$BACKUP_DIR/db_$DATE.dump"
pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$DB_FILE"
echo "  baza  : $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"

# --- Media ---
MEDIA_FILE="$BACKUP_DIR/media_$DATE.tar.gz"
tar -czf "$MEDIA_FILE" -C "$APP_DIR/backend" media
echo "  media : $MEDIA_FILE ($(du -h "$MEDIA_FILE" | cut -f1))"

# --- Eskilarini tozalash ---
REMOVED=$(find "$BACKUP_DIR" -name "db_*.dump" -o -name "media_*.tar.gz" \
    | xargs -r ls -1 2>/dev/null | wc -l)
find "$BACKUP_DIR" \( -name "db_*.dump" -o -name "media_*.tar.gz" \) \
    -mtime +"$RETENTION_DAYS" -delete
echo "  saqlanadi: $RETENTION_DAYS kun ($REMOVED fayl mavjud edi)"

# --- Masofaviy nusxa (ixtiyoriy) ---
# Zaxira faqat o'sha serverda tursa, server yo'qolganda u ham yo'qoladi.
if [ -n "${CTSALE_S3_BUCKET:-}" ]; then
    aws s3 cp "$DB_FILE" "s3://$CTSALE_S3_BUCKET/db/"
    aws s3 cp "$MEDIA_FILE" "s3://$CTSALE_S3_BUCKET/media/"
    echo "  s3    : yuklandi"
fi

echo "[$(date -Is)] Zaxira tugadi"
