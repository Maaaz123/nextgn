output "public_ip" {
  description = "VM public IP"
  value       = azurerm_public_ip.pip.ip_address
}

output "airflow_url" {
  description = "Airflow URL (after stack is up)"
  value       = "http://${azurerm_public_ip.pip.ip_address}:8080"
}

output "metabase_url" {
  description = "Metabase URL (after stack is up)"
  value       = "http://${azurerm_public_ip.pip.ip_address}:3000"
}

output "ssh_command" {
  description = "SSH command"
  value       = "ssh ${var.admin_username}@${azurerm_public_ip.pip.ip_address}"
}
