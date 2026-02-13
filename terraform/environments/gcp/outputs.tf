output "instance_id" {
  description = "GCE instance ID"
  value       = google_compute_instance.data_tools.instance_id
}

output "public_ip" {
  description = "Instance public IP"
  value       = google_compute_instance.data_tools.network_interface[0].access_config[0].nat_ip
}

output "airflow_url" {
  description = "Airflow URL (after stack is up)"
  value       = "http://${google_compute_instance.data_tools.network_interface[0].access_config[0].nat_ip}:8080"
}

output "metabase_url" {
  description = "Metabase URL (after stack is up)"
  value       = "http://${google_compute_instance.data_tools.network_interface[0].access_config[0].nat_ip}:3000"
}

output "ssh_command" {
  description = "SSH command (use gcloud compute ssh data-tools --zone=... if no external IP key)"
  value       = "gcloud compute ssh ${google_compute_instance.data_tools.name} --zone=${var.zone} --project=${var.project_id}"
}
