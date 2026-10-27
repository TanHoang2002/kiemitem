#!/usr/bin/env bash
# D4LF (Diablo IV Loot Filter v10.0.7) launcher cho may 171 (Nobara KDE Wayland; game Diablo IV qua Heroic/Proton)
# Cach dung:
#   ./run_171.sh              (chay GUI hien thi len man hinh desktop)
#   ./run_171.sh --console    (chay console mode)
#   ./run_171.sh --daemon     (chay nen ghi log ra ~/d4lf_171.log)
#   ./run_171.sh --stop       (dung bot d4lf)
set -uo pipefail
cd "$(dirname "$0")"
U="$(id -u)"
export PATH="$HOME/.local/bin:$PATH"
export DISPLAY="${DISPLAY:-:0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$U}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
XAUTH_FILE="$(ls "$XDG_RUNTIME_DIR"/xauth_* 2>/dev/null | head -1)"
[ -n "$XAUTH_FILE" ] && export XAUTHORITY="$XAUTH_FILE"
export BOTFILLITEM_YDOTOOL=1
export YDOTOOL_SOCKET="${YDOTOOL_SOCKET:-$XDG_RUNTIME_DIR/.ydotool_socket}"
export QT_QPA_PLATFORM=xcb

if [ "${1:-}" = "--stop" ]; then
  echo "[d4lf] Dang dung tien trinh D4LF..."
  pkill -f "/home/gege/d4lf.*src.main" || true
  pkill -f "relay\.py" || true
  echo "[d4lf] Da dung!"
  exit 0
fi

# 1) ydotoold — daemon uinput cho chuot ao tren Wayland
pgrep -x ydotoold >/dev/null 2>&1 || {
  echo "[run] khoi dong ydotoold"
  nohup ydotoold >"$HOME/ydotoold_171.log" 2>&1 &
  sleep 1
}

# 2) pipe relay — relay named pipe \\.\pipe\d4lf sang TCP 27015 qua Proton Wine
GAME_WINEPREFIX="/games/gege-home/BattleNetLocal/4092036803/pfx"
GAME_WINE="/games/gege-home/.steam/debian-installation/steamapps/common/Proton 11.0/files/bin/wine"
pgrep -f "relay\.py" >/dev/null 2>&1 || {
  echo "[run] khoi dong pipe relay (Proton prefix -> TCP 27015)"
  nohup env WINEPREFIX="$GAME_WINEPREFIX" YDOTOOL_SOCKET="$YDOTOOL_SOCKET" \
    "$GAME_WINE" "$PWD/.linuxtools/winpython/python.exe" "$PWD/.linuxtools/winpython/relay.py" \
    >"$HOME/relay_171.log" 2>&1 &
  sleep 2
}

# 3) D4LF Bot
echo "[run] Khoi dong D4LF v10.0.7 (DISPLAY=$DISPLAY, ydotool=ON)"
if [ "${1:-}" = "--daemon" ]; then
  shift || true
  nohup ~/.local/bin/uv run python -m src.main >>"$HOME/d4lf_171.log" 2>&1 &
  echo "[run] D4LF dang chay nen! Xem log tai: ~/d4lf_171.log"
elif [ "${1:-}" = "--console" ]; then
  shift || true
  exec ~/.local/bin/uv run python -m src.main --consoleonly
else
  exec ~/.local/bin/uv run python -m src.main
fi
