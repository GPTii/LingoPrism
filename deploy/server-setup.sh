#!/bin/sh
# One-time setup of a fresh Ubuntu 24.04 VPS (run as root: sudo sh deploy/server-setup.sh).
# Docker, 2 GB swap, firewall (22/80/443 only), fail2ban, automatic security updates, daily DB backup.
set -eu

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get -y upgrade
apt-get install -y ca-certificates curl ufw fail2ban unattended-upgrades openssl

# Docker Engine + compose plugin
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi
usermod -aG docker "${SUDO_USER:-azureuser}" || true
# containers' logs must not fill the disk
cat > /etc/docker/daemon.json <<'EOF'
{ "log-driver": "json-file", "log-opts": { "max-size": "20m", "max-file": "3" } }
EOF
systemctl restart docker

# 2 GB swap: headroom for image builds on a 4 GB machine
if [ ! -f /swapfile ]; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  echo 'vm.swappiness=10' > /etc/sysctl.d/99-swap.conf && sysctl -p /etc/sysctl.d/99-swap.conf
fi

# firewall: SSH + web only (Postgres/Redis are never published by docker-compose.prod.yml)
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# SSH: keys only; fail2ban bans IPs that keep failing
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl reload ssh || true
systemctl enable --now fail2ban

dpkg-reconfigure -f noninteractive unattended-upgrades

echo "Done. Log out and back in so '${SUDO_USER:-azureuser}' can use docker without sudo."
