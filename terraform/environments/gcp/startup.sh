#!/bin/bash
set -e
export DEBIAN_FRONTEND=noninteractive

# Docker
apt-get update && apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update && apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin git

# Clone and run
if [ -n "${repo_url}" ]; then
  git clone -b "${repo_branch}" "${repo_url}" /opt/app 2>/dev/null || true
  if [ -d /opt/app ]; then
    cat > /opt/app/.env << ENVFILE
POSTGRES_PASSWORD=${postgres_password}
AIRFLOW_PASSWORD=${airflow_password}
ENVFILE
    cd /opt/app && docker compose up -d || true
  fi
fi
echo "VM ready."
