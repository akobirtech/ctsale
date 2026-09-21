#!/usr/bin/env bash
# Development serverlarini boshqarish (Windows + Git Bash).
#
# Nega alohida skript: `pkill` Windows'dagi node/python jarayonlarini
# o'ldirmaydi, shuning uchun har safar dublikat qolib, port band
# bo'lib qolardi. Bu yerda PowerShell orqali aniq o'ldiriladi.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kill_matching() {
  local name="$1" pattern="$2"
  powershell.exe -NoProfile -Command "
    Get-CimInstance Win32_Process -Filter \"Name='$name'\" |
      Where-Object { \$_.CommandLine -like '*$pattern*' } |
      ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }
  " >/dev/null 2>&1
}

stop_all() {
  kill_matching "python.exe" "runserver"
  kill_matching "node.exe" "server.js"
  sleep 2
}

wait_for() {
  local url="$1" name="$2"
  for _ in $(seq 1 30); do
    if curl -s --max-time 2 "$url" >/dev/null 2>&1; then
      echo "  $name tayyor"
      return 0
    fi
    sleep 1
  done
  echo "  $name ISHGA TUSHMADI"
  return 1
}

case "${1:-start}" in
  stop)
    stop_all
    echo "Serverlar to'xtatildi"
    ;;
  start | restart)
    stop_all
    cd "$ROOT/backend" || exit 1
    nohup ./venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000 --noreload \
      > logs/runserver.log 2>&1 &
    cd "$ROOT/frontend" || exit 1
    API_URL=http://127.0.0.1:8000 nohup node server.js > logs-ssr.log 2>&1 &
    wait_for "http://127.0.0.1:8000/api/v1/health/" "backend  :8000"
    wait_for "http://127.0.0.1:5173/uz" "frontend :5173"
    ;;
  status)
    curl -s --max-time 3 http://127.0.0.1:8000/api/v1/health/ >/dev/null 2>&1 \
      && echo "  backend  :8000  ishlayapti" || echo "  backend  :8000  to'xtagan"
    curl -s --max-time 3 http://127.0.0.1:5173/uz >/dev/null 2>&1 \
      && echo "  frontend :5173  ishlayapti" || echo "  frontend :5173  to'xtagan"
    ;;
  *)
    echo "Ishlatish: ./dev.sh [start|restart|stop|status]"
    exit 1
    ;;
esac
