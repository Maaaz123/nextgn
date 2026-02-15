variable "endpoint" {
  description = "MinIO/S3 endpoint URL (e.g. http://localhost:9000)"
  type        = string
}

variable "access_key" {
  description = "MinIO/S3 access key"
  type        = string
  default     = "minioadmin"
  sensitive   = true
}

variable "secret_key" {
  description = "MinIO/S3 secret key"
  type        = string
  default     = "minioadmin"
  sensitive   = true
}

variable "bucket_prefix" {
  description = "Prefix for bucket names (e.g. datatools-)"
  type        = string
  default     = ""
}

variable "create_placeholder_objects" {
  description = "Create .keep placeholder objects in each bucket"
  type        = bool
  default     = true
}
