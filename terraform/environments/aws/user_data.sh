#!/bin/bash
set -e
yum update -y
yum install -y docker git
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user
mkdir -p /usr/local/lib/docker/cli-plugins
curl -sSL "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

# Clone repo and run stack (if repo_url set)
if [ -n "${repo_url}" ]; then
  sudo -u ec2-user git clone -b "${repo_branch}" "${repo_url}" /home/ec2-user/app 2>/dev/null || true
  if [ -d /home/ec2-user/app ]; then
    cat > /home/ec2-user/app/.env << ENVFILE
POSTGRES_PASSWORD=${postgres_password}
AIRFLOW_PASSWORD=${airflow_password}
ENVFILE
    chown ec2-user:ec2-user /home/ec2-user/app/.env
    sudo -u ec2-user bash -c 'cd /home/ec2-user/app && docker compose up -d' || true
  fi
fi
echo "VM ready. Airflow: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080"
