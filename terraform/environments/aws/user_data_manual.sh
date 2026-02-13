#!/bin/bash
set -e
# Install Docker only; you SSH in and run docker compose yourself (e.g. after copying repo)
yum update -y
yum install -y docker git
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user
mkdir -p /usr/local/lib/docker/cli-plugins
curl -sSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
echo "Docker and Docker Compose installed. SSH in, copy your repo, then: docker compose up -d"
