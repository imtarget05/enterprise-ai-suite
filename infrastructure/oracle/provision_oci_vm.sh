#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo " Oracle Cloud Always Free ARM64 (2 OCPU / 12GB RAM) Setup"
echo "=========================================================="

# 1. Update system packages
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw iptables-persistent fail2ban

# 2. Install Docker & Buildx
if ! command -v docker &> /dev/null; then
    echo "Installing Docker Engine..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker ubuntu
fi

# 3. Configure UFW Firewall (Lock down database and message bus ports)
echo "Configuring firewall rules..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw --force enable

# 4. Create 4GB Swapfile for memory safety headroom
if [ ! -f /swapfile ]; then
    echo "Creating 4GB swapfile..."
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo ">> OCI ARM64 VM Provisioning Complete. Ready for 'docker compose up'!"
