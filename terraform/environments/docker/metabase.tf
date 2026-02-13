resource "docker_image" "metabase" {
  name = "metabase/metabase:latest"
}

resource "docker_container" "metabase" {
  name    = "data_tools_metabase"
  image   = docker_image.metabase.image_id
  restart = "unless-stopped"

  env = [
    "MB_DB_TYPE=postgres",
    "MB_DB_DBNAME=metabase",
    "MB_DB_PORT=5432",
    "MB_DB_USER=${var.postgres_user}",
    "MB_DB_PASS=${var.postgres_password}",
    "MB_DB_HOST=postgres"
  ]

  ports {
    internal = 3000
    external = var.metabase_port
  }

  depends_on = [docker_container.postgres]
  networks_advanced {
    name = docker_network.data_tools.name
  }
}
