#!/usr/bin/env bash
# Remove Freenove tower-cooler install artifacts created by setup.py / the app.
# Leaves APT packages installed (libpio, luma.oled, build tools, etc.).

set -euo pipefail

INSTALL_ROOT='/opt/freenove/tower-cooler'
SERVICES=(task_led.service task_fan.service task_oled.service)
SHORTCUT_NAMES=(FNK0113 FNK0108)

if [[ "$(id -u)" -eq 0 ]]; then
  REAL_USER="${SUDO_USER:-}"
  if [[ -z "$REAL_USER" || "$REAL_USER" == 'root' ]]; then
    echo 'Run as your normal user (the script will sudo where needed), e.g.: ./uninstall.sh' >&2
    exit 1
  fi
  HOME_DIR="$(getent passwd "$REAL_USER" | cut -d: -f6)"
else
  REAL_USER="$(id -un)"
  HOME_DIR="${HOME}"
fi

echo "Uninstalling Freenove tower cooler for user ${REAL_USER}..."

remove_services() {
  local svc
  for svc in "${SERVICES[@]}"; do
    if [[ -f "/etc/systemd/system/${svc}" ]] || systemctl list-unit-files --no-legend "$svc" 2>/dev/null | grep -q .; then
      echo "Stopping/disabling ${svc}"
      sudo systemctl stop "$svc" 2>/dev/null || true
      sudo systemctl disable "$svc" 2>/dev/null || true
      sudo rm -f "/etc/systemd/system/${svc}"
    fi
  done
  sudo systemctl daemon-reload 2>/dev/null || true
}

remove_shortcuts() {
  local name desk apps
  desk="${HOME_DIR}/Desktop"
  apps="${HOME_DIR}/.local/share/applications"
  for name in "${SHORTCUT_NAMES[@]}"; do
    for path in "${desk}/${name}.desktop" "${apps}/${name}.desktop"; do
      if [[ -e "$path" ]]; then
        echo "Removing ${path}"
        rm -f "$path"
      fi
    done
  done
}

remove_install_root() {
  if [[ -e "$INSTALL_ROOT" ]]; then
    echo "Removing ${INSTALL_ROOT}"
    sudo rm -rf "$INSTALL_ROOT"
  else
    echo "No ${INSTALL_ROOT} present; skipping"
  fi
}

remove_services
remove_shortcuts
remove_install_root

echo 'Done. APT packages were left installed.'
echo 'Parent /opt/freenove (for other products) was left in place if present.'
echo 'Repo checkout (including native/ sources) was not deleted.'
