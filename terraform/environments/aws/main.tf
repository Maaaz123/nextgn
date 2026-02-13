provider "aws" {
  region = var.aws_region
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

data "local_file" "ssh_public_key" {
  filename = pathexpand(var.ssh_public_key_path)
}

resource "aws_key_pair" "deploy" {
  key_name   = "${var.project_name}-key"
  public_key = data.local_file.ssh_public_key.content
}

resource "aws_security_group" "data_tools" {
  name        = "${var.project_name}-sg"
  description = "SSH, Airflow, Metabase, Postgres"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
    description = "SSH"
  }
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
    description = "Airflow"
  }
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
    description = "Metabase"
  }
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr]
    description = "Postgres"
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

locals {
  user_data = var.repo_url != "" ? templatefile("${path.module}/user_data.sh", {
    repo_url         = var.repo_url
    repo_branch      = var.repo_branch
    postgres_password = var.postgres_password
    airflow_password  = var.airflow_password
  }) : templatefile("${path.module}/user_data_manual.sh", {})
}

resource "aws_instance" "data_tools" {
  ami                    = data.aws_ami.amazon_linux_2.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.deploy.key_name
  vpc_security_group_ids = [aws_security_group.data_tools.id]
  user_data              = local.user_data

  tags = {
    Name = var.project_name
  }

  lifecycle {
    ignore_changes = [user_data]
  }
}
