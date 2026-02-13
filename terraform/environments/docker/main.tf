provider "docker" {}

resource "docker_network" "data_tools" {
  name = "data_tools_network"
}

resource "docker_volume" "postgres_data" {
  name = "data_tools_postgres_data"
}
