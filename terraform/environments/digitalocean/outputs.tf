output "droplet_id" {
  description = "DigitalOcean Droplet ID"
  value       = digitalocean_droplet.data_tools.id
}

output "public_ip" {
  description = "Droplet public IP"
  value       = digitalocean_droplet.data_tools.ipv4_address
}

output "airflow_url" {
  description = "Airflow URL (after stack is up)"
  value       = "http://${digitalocean_droplet.data_tools.ipv4_address}:8080"
}

output "metabase_url" {
  description = "Metabase URL (after stack is up)"
  value       = "http://${digitalocean_droplet.data_tools.ipv4_address}:3000"
}

output "dremio_url" {
  description = "Dremio URL (after stack is up)"
  value       = "http://${digitalocean_droplet.data_tools.ipv4_address}:9047"
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh root@${digitalocean_droplet.data_tools.ipv4_address}"
}
