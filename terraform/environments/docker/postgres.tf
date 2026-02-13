resource "docker_image" "postgres" {
  name = "postgres:15-alpine"
}

resource "docker_container" "postgres" {
  name  = "data_tools_postgres"
  image = docker_image.postgres.image_id

  env = [
    "POSTGRES_USER=${var.postgres_user}",
    "POSTGRES_PASSWORD=${var.postgres_password}",
    "POSTGRES_MULTIPLE_DATABASES=warehouse,airflow,metabase"
  ]

  ports {
    internal = 5432
    external = var.postgres_port
  }

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  volumes {
    host_path      = "${local.project_root}/scripts/infra/init-dbs.sh"
    container_path = "/docker-entrypoint-initdb.d/init-dbs.sh"
  }

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U ${var.postgres_user}"]
    interval     = "5s"
    timeout      = "5s"
    retries      = 5
    start_period = "10s"
  }

  networks_advanced {
    name = docker_network.data_tools.name
  }
}
