variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix used for all resource names"
  type        = string
  default     = "self-eval-rag"
}

variable "admin_password" {
  description = "Admin dashboard password (stored in Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "task_cpu" {
  description = "Fargate task CPU units (1 vCPU = 1024). Ollama + Streamlit needs at least 2048."
  type        = number
  default     = 4096   # 4 vCPU
}

variable "task_memory" {
  description = "Fargate task memory in MiB. Embedding model + Gemma needs ~8GB minimum."
  type        = number
  default     = 16384  # 16 GB
}
