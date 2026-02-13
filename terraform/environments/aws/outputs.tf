output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.data_tools.id
}

output "public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.data_tools.public_ip
}

output "airflow_url" {
  description = "Airflow URL (after stack is up)"
  value       = "http://${aws_instance.data_tools.public_ip}:8080"
}

output "metabase_url" {
  description = "Metabase URL (after stack is up)"
  value       = "http://${aws_instance.data_tools.public_ip}:3000"
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i ~/.ssh/your-key.pem ec2-user@${aws_instance.data_tools.public_ip}"
}
