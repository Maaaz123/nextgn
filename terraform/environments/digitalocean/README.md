# DigitalOcean deployment

Creates a Droplet (Ubuntu 22.04), installs Docker and Compose, optionally clones your repo and runs `docker compose up -d`.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- DigitalOcean API token: [Create one](https://cloud.digitalocean.com/account/api/tokens)
- SSH key for Droplet access

## Usage

1. Set your API token:
   ```bash
   export DIGITALOCEAN_TOKEN=your-token
   ```
   Or copy and edit tfvars:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Set do_token and other variables
   ```

2. From the **repo root**:
   ```bash
   terraform -chdir=terraform/environments/digitalocean init
   terraform -chdir=terraform/environments/digitalocean apply
   ```

3. Use the output URLs (Airflow, Metabase, Dremio). If `repo_url` was set and the repo is public, the stack will start via cloud-init; wait 2–3 minutes. If the repo is private, SSH in and run:
   ```bash
   ssh root@<public_ip>
   git clone <your-repo> /opt/app && cd /opt/app && cp .env.example .env && docker compose up -d
   ```

## Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `do_token` | DigitalOcean API token (or `DIGITALOCEAN_TOKEN`) | — |
| `region` | Region slug (e.g. nyc1, sfo3, sgp1) | nyc1 |
| `droplet_size` | Size slug (e.g. s-2vcpu-4gb) | s-2vcpu-4gb |
| `repo_url` | Git URL to clone and run compose | "" |
| `repo_branch` | Branch to clone | main |
| `ssh_public_key_path` | Path to SSH public key | ~/.ssh/id_rsa.pub |
| `allowed_cidr` | CIDRs for firewall | ["0.0.0.0/0"] |

## Firewall

Opens: SSH (22), Airflow (8080), Metabase (3000), Postgres (5432), Dremio (9047), MinIO (9000, 9001).
