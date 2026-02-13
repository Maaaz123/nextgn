provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_compute_image" "ubuntu" {
  family  = "ubuntu-2204-lts"
  project = "ubuntu-os-cloud"
}

resource "google_compute_firewall" "data_tools" {
  name    = "${var.project_name}-fw"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "8080", "3000", "5432"]
  }
  source_ranges = [var.allowed_cidr]
}

resource "google_compute_instance" "data_tools" {
  name         = var.project_name
  machine_type = var.machine_type
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = data.google_compute_image.ubuntu.self_link
      size  = 30
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata_startup_script = templatefile("${path.module}/startup.sh", {
    repo_url          = var.repo_url
    repo_branch       = var.repo_branch
    postgres_password = var.postgres_password
    airflow_password  = var.airflow_password
  })

  tags = [var.project_name]
}
