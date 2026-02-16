provider "digitalocean" {
  token = var.do_token != "" ? var.do_token : null
}

data "local_file" "ssh_public_key" {
  filename = pathexpand(var.ssh_public_key_path)
}

resource "digitalocean_ssh_key" "deploy" {
  name       = "${var.project_name}-key"
  public_key = data.local_file.ssh_public_key.content
}

resource "digitalocean_firewall" "data_tools" {
  name = "${var.project_name}-fw"

  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = var.allowed_cidr
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "8080"
    source_addresses = var.allowed_cidr
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "3000"
    source_addresses = var.allowed_cidr
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "5432"
    source_addresses = var.allowed_cidr
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "9047"
    source_addresses = var.allowed_cidr
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "9000"
    source_addresses = var.allowed_cidr
  }
  inbound_rule {
    protocol         = "tcp"
    port_range       = "9001"
    source_addresses = var.allowed_cidr
  }

  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

resource "digitalocean_droplet" "data_tools" {
  name     = var.project_name
  region   = var.region
  size     = var.droplet_size
  image    = "ubuntu-22-04-x64"
  ssh_keys = [digitalocean_ssh_key.deploy.id]

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    repo_url          = var.repo_url
    repo_branch       = var.repo_branch
    postgres_password = var.postgres_password
    airflow_password  = var.airflow_password
  })

  lifecycle {
    ignore_changes = [user_data]
  }
}

resource "digitalocean_firewall_droplet_assignment" "data_tools" {
  firewall_id = digitalocean_firewall.data_tools.id
  droplet_ids = [digitalocean_droplet.data_tools.id]
}
