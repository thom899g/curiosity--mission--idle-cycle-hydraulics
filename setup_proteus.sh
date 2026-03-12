#!/bin/bash
# PROJECT PROTEUS - AUTOMATED DEPLOYMENT SCRIPT
# This script sets up the entire Proteus infrastructure on a fresh Ubuntu 22.04 EC2 instance
# Run with: sudo bash setup_proteus.sh

set -e  # Exit on error
set -o pipefail

echo "🚀 PROJECT PROTEUS DEPLOYMENT INITIATED $(date)"
echo "==============================================="

# Configuration
REPO_URL="https://github.com/Proteus-Calculus/proteus-core.git"
INSTALL_DIR="/opt/proteus"
VENV_DIR="$INSTALL_DIR/venv"
LOG_DIR="/var/log/proteus"
SERVICE_USER="proteus"

# 1. System Dependencies
echo "[1/8] Installing system dependencies..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    nginx \
    certbot \
    python3-certbot-nginx \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl \
    jq \
    unzip \
    awscli \
    htop \
    net-tools

# 2. Create Service User
echo "[2/8] Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/bash -m -d "$INSTALL_DIR" "$SERVICE_USER"
fi

# 3. Directory Structure
echo "[3/8] Creating directory structure..."
mkdir -p "$INSTALL_DIR" "$LOG_DIR"
chown -R $SERVICE_USER:$SERVICE_USER "$INSTALL_DIR" "$LOG_DIR"

# 4. Clone Repository
echo "[4/8] Cloning repository..."
cd "$INSTALL_DIR"
sudo -u $SERVICE_USER git clone "$REPO_URL" . || echo "Repo already exists"

# 5. Python Virtual Environment
echo "[5/8] Setting up Python environment..."
sudo -u $SERVICE_USER python3.10 -m venv "$VENV_DIR"
sudo -u $SERVICE_USER "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel

# 6. Install Python Dependencies
echo "[6/8] Installing Python dependencies..."
sudo -u $SERVICE_USER "$VENV_DIR/bin/pip" install \
    pandas==2.0.3 \
    numpy==1.24.3 \
    web3==6.4.0 \
    firebase-admin==6.2.0 \
    ccxt==4.0.90 \
    scipy==1.10.1 \
    numba==0.57.0 \
    requests==2.31.0 \
    python-dotenv==1.0.0 \
    uvicorn==0.23.2 \
    fastapi==0.100.1 \
    stripe==7.3.0 \
    boto3==1.28.0 \
    pyarrow==12.0.1 \
    python-multipart==0.0.6

# 7. Configure Firewall
echo "[7/8] Configuring firewall..."
ufw allow 22  # SSH
ufw allow 80  # HTTP
ufw allow 443 # HTTPS
ufw --force enable

# 8. Setup Systemd Service
echo "[8/8] Configuring systemd service..."
cat > /etc/systemd/system/proteus.service << EOF
[Unit]
Description=Proteus Computation Engine
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=1
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONPATH=$INSTALL_DIR"
ExecStart=$VENV_DIR/bin/python -m proteus_core.main
StandardOutput=append:$LOG_DIR/proteus.log
StandardError=append:$LOG_DIR/proteus-error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable proteus.service

echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "NEXT STEPS:"
echo "1. Configure environment variables in $INSTALL_DIR/.env"
echo "2. Initialize Firebase: sudo -u $SERVICE_USER $VENV_DIR/bin/python -m proteus_core.firebase_init"
echo "3. Start service: sudo systemctl start proteus"
echo "4. Monitor logs: tail -f $LOG_DIR/proteus.log"
echo ""
echo "For SSL certificate: certbot --nginx -d your-domain.com"