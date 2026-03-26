#!/usr/bin/env bash
# Smart Saw — kurulum ve yönetim aracı
# Kullanım: sudo bash setup-autostart.sh
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="smart-saw"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_DIR="${PROJECT_DIR}/venv"
RUN_USER="${SUDO_USER:-$(whoami)}"

# --- Renkler ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# --- Yardımcılar ---
info()    { echo -e "${CYAN}►${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}!${NC} $1"; }
fail()    { echo -e "${RED}✗${NC} $1"; }

header() {
    echo
    echo -e "${BOLD}━━━ $1 ━━━${NC}"
    echo
}

status_line() {
    local label="$1" value="$2" color="${3:-$NC}"
    printf "  %-24s ${color}%s${NC}\n" "$label" "$value"
}

# --- Durum kontrolleri ---
check_venv()    { [ -d "${VENV_DIR}/bin" ]; }
check_deps()    { check_venv && "${VENV_DIR}/bin/python" -c "import pymodbus, PySide6" 2>/dev/null; }
check_unit()    { [ -f "${SERVICE_FILE}" ]; }
check_enabled() { systemctl is-enabled "${SERVICE_NAME}" &>/dev/null; }
check_running() { systemctl is-active  "${SERVICE_NAME}" &>/dev/null; }

status_tag() {
    if $1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${DIM}–${NC}"
    fi
}

# --- Durum ekranı ---
show_status() {
    header "Smart Saw Durum"
    status_line "Proje dizini"   "${PROJECT_DIR}"
    status_line "Kullanıcı"      "${RUN_USER}"
    echo
    status_line "Virtualenv"     "$(check_venv    && echo 'mevcut' || echo 'yok')" "$(check_venv    && echo "$GREEN" || echo "$DIM")"
    status_line "Bağımlılıklar"  "$(check_deps    && echo 'yüklü'  || echo 'eksik')" "$(check_deps    && echo "$GREEN" || echo "$YELLOW")"
    status_line "Systemd unit"   "$(check_unit    && echo 'yazıldı' || echo 'yok')" "$(check_unit    && echo "$GREEN" || echo "$DIM")"
    status_line "Açılış servisi" "$(check_enabled && echo 'aktif'  || echo 'pasif')" "$(check_enabled && echo "$GREEN" || echo "$DIM")"
    status_line "Çalışma durumu" "$(check_running && echo 'çalışıyor' || echo 'durdu')" "$(check_running && echo "$GREEN" || echo "$DIM")"
    echo
}

# --- İşlemler ---
do_venv() {
    header "Virtualenv Oluştur"
    if check_venv; then
        warn "Virtualenv zaten mevcut: ${VENV_DIR}"
        read -rp "  Sıfırdan oluşturulsun mu? [e/H] " ans
        [[ "${ans,,}" == "e" ]] || return 0
        info "Eski venv siliniyor..."
        rm -rf "${VENV_DIR}"
    fi
    info "Virtualenv oluşturuluyor..."
    python3 -m venv "${VENV_DIR}"
    success "Virtualenv hazır: ${VENV_DIR}"
}

do_deps() {
    header "Bağımlılıkları Yükle"
    if ! check_venv; then
        fail "Önce virtualenv oluşturulmalı."
        return 1
    fi
    info "pip güncelleniyor..."
    "${VENV_DIR}/bin/pip" install --quiet --upgrade pip
    info "requirements.txt yükleniyor..."
    "${VENV_DIR}/bin/pip" install -r "${PROJECT_DIR}/requirements.txt"
    success "Bağımlılıklar yüklendi."
}

do_install_service() {
    header "Systemd Servisi Kur"
    info "Servis dosyası yazılıyor: ${SERVICE_FILE}"
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Smart Band Saw Control System
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${PROJECT_DIR}
EnvironmentFile=${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/python ${PROJECT_DIR}/run.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

Environment=DISPLAY=:0
Environment=QT_QPA_PLATFORM=xcb

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    success "Servis dosyası yazıldı ve daemon yenilendi."
}

do_enable() {
    header "Açılış Servisini Etkinleştir"
    if ! check_unit; then
        fail "Önce servis kurulmalı."
        return 1
    fi
    systemctl enable "${SERVICE_NAME}.service"
    success "Servis açılışta otomatik başlayacak."
}

do_disable() {
    header "Açılış Servisini Devre Dışı Bırak"
    if ! check_unit; then
        fail "Servis dosyası bulunamadı."
        return 1
    fi
    systemctl disable "${SERVICE_NAME}.service"
    success "Servis açılışta başlamayacak."
}

do_start() {
    header "Servisi Başlat"
    if ! check_unit; then
        fail "Önce servis kurulmalı."
        return 1
    fi
    systemctl start "${SERVICE_NAME}.service"
    sleep 1
    if check_running; then
        success "Servis çalışıyor."
    else
        fail "Servis başlatılamadı. Loglar:"
        journalctl -u "${SERVICE_NAME}" -n 10 --no-pager
    fi
}

do_stop() {
    header "Servisi Durdur"
    if check_running; then
        systemctl stop "${SERVICE_NAME}.service"
        success "Servis durduruldu."
    else
        warn "Servis zaten çalışmıyor."
    fi
}

do_logs() {
    header "Servis Logları (son 30 satır)"
    journalctl -u "${SERVICE_NAME}" -n 30 --no-pager
    echo
    info "Canlı takip: journalctl -u ${SERVICE_NAME} -f"
}

do_uninstall() {
    header "Servisi Kaldır"
    if check_running; then
        info "Servis durduruluyor..."
        systemctl stop "${SERVICE_NAME}.service"
    fi
    if check_enabled; then
        info "Servis devre dışı bırakılıyor..."
        systemctl disable "${SERVICE_NAME}.service"
    fi
    if check_unit; then
        info "Servis dosyası siliniyor..."
        rm -f "${SERVICE_FILE}"
        systemctl daemon-reload
    fi
    success "Servis tamamen kaldırıldı."
}

do_full_setup() {
    header "Tam Kurulum"
    info "Tüm adımlar sırayla çalıştırılacak."
    echo
    do_venv
    do_deps
    do_install_service
    do_enable
    echo
    success "Tam kurulum tamamlandı. Servis bir sonraki açılışta başlayacak."
}

# --- Menü ---
show_menu() {
    echo -e "${BOLD}  Kurulum${NC}"
    echo "    1)  Virtualenv oluştur"
    echo "    2)  Bağımlılıkları yükle"
    echo "    3)  Systemd servisi kur"
    echo "    4)  Açılış servisini etkinleştir"
    echo "    5)  Tam kurulum (1→2→3→4)"
    echo
    echo -e "${BOLD}  Kontrol${NC}"
    echo "    6)  Servisi başlat"
    echo "    7)  Servisi durdur"
    echo "    8)  Logları göster"
    echo
    echo -e "${BOLD}  Kaldır${NC}"
    echo "    9)  Açılış servisini devre dışı bırak"
    echo "   10)  Servisi tamamen kaldır"
    echo
    echo "    0)  Çıkış"
    echo
}

# --- Ana döngü ---
main() {
    while true; do
        show_status
        show_menu
        read -rp "  Seçim: " choice
        case "${choice}" in
            1)  do_venv ;;
            2)  do_deps ;;
            3)  do_install_service ;;
            4)  do_enable ;;
            5)  do_full_setup ;;
            6)  do_start ;;
            7)  do_stop ;;
            8)  do_logs ;;
            9)  do_disable ;;
            10) do_uninstall ;;
            0)  echo; exit 0 ;;
            *)  warn "Geçersiz seçim." ;;
        esac
        echo
        read -rp "  Devam etmek için Enter'a basın..." _
    done
}

main
