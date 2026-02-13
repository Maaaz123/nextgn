resource "docker_image" "airflow" {
  name = "data-tools-airflow:latest"

  build {
    context    = local.project_root
    dockerfile = "Dockerfile.airflow"
  }
}

# One-off Airflow DB init (Terraform waits for this before starting webserver/scheduler)
resource "null_resource" "airflow_init" {
  triggers = {
    postgres_id = docker_container.postgres.id
    image_id    = docker_image.airflow.image_id
  }

  provisioner "local-exec" {
    command = <<-EOT
      docker run --rm \
        --network ${docker_network.data_tools.name} \
        -e AIRFLOW__CORE__EXECUTOR=LocalExecutor \
        -e AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${local.postgres_conn} \
        -e AIRFLOW__CORE__LOAD_EXAMPLES=false \
        -e AIRFLOW__CORE__FERNET_KEY= \
        ${docker_image.airflow.name} \
        bash -c "airflow db init && airflow users create --username ${var.airflow_username} --password ${var.airflow_password} --firstname Admin --lastname User --role Admin --email admin@localhost || true"
    EOT
    interpreter = ["bash", "-c"]
  }

  depends_on = [docker_container.postgres]
}

resource "docker_container" "airflow_webserver" {
  name    = "data_tools_airflow_webserver"
  image   = docker_image.airflow.image_id
  restart = "unless-stopped"

  command = ["webserver"]

  env = [
    "AIRFLOW__CORE__EXECUTOR=LocalExecutor",
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${local.postgres_conn}",
    "AIRFLOW__CORE__LOAD_EXAMPLES=false",
    "AIRFLOW__CORE__FERNET_KEY=",
    "AIRFLOW__WEBSERVER__EXPOSE_CONFIG=true",
    "_AIRFLOW_WWW_USER_USERNAME=${var.airflow_username}",
    "_AIRFLOW_WWW_USER_PASSWORD=${var.airflow_password}"
  ]

  ports {
    internal = 8080
    external = var.airflow_port
  }

  volumes {
    host_path      = "${local.project_root}/dbt"
    container_path = "/opt/airflow/dbt"
  }
  volumes {
    host_path      = "${local.project_root}/airflow/dags"
    container_path = "/opt/airflow/dags"
  }
  volumes {
    host_path      = "${local.project_root}/airflow/logs"
    container_path = "/opt/airflow/logs"
  }

  depends_on = [null_resource.airflow_init]
  networks_advanced {
    name = docker_network.data_tools.name
  }
}

resource "docker_container" "airflow_scheduler" {
  name    = "data_tools_airflow_scheduler"
  image   = docker_image.airflow.image_id
  restart = "unless-stopped"

  command = ["scheduler"]

  env = [
    "AIRFLOW__CORE__EXECUTOR=LocalExecutor",
    "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=${local.postgres_conn}",
    "AIRFLOW__CORE__LOAD_EXAMPLES=false",
    "AIRFLOW__CORE__FERNET_KEY="
  ]

  volumes {
    host_path      = "${local.project_root}/dbt"
    container_path = "/opt/airflow/dbt"
  }
  volumes {
    host_path      = "${local.project_root}/airflow/dags"
    container_path = "/opt/airflow/dags"
  }
  volumes {
    host_path      = "${local.project_root}/airflow/logs"
    container_path = "/opt/airflow/logs"
  }

  depends_on = [null_resource.airflow_init]
  networks_advanced {
    name = docker_network.data_tools.name
  }
}
