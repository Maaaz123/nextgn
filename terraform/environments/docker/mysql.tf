# Optional MySQL container for mysql_to_postgres DAG. Enable with enable_mysql = true.

resource "docker_image" "mysql" {
  count = var.enable_mysql ? 1 : 0
  name  = "mysql:8.0"
}

resource "docker_container" "mysql" {
  count = var.enable_mysql ? 1 : 0

  name    = "data_tools_mysql"
  image   = docker_image.mysql[0].image_id
  restart = "unless-stopped"

  env = [
    "MYSQL_ROOT_PASSWORD=mysql",
    "MYSQL_DATABASE=mydb",
    "MYSQL_USER=mysql",
    "MYSQL_PASSWORD=mysql"
  ]

  ports {
    internal = 3306
    external = 3306
  }

  healthcheck {
    test         = ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-pmysql"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 5
    start_period = "10s"
  }

  networks_advanced {
    name = docker_network.data_tools.name
  }
}
