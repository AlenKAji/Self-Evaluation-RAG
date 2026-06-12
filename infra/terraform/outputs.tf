output "app_url" {
  description = "Public URL of the RAG application"
  value       = "http://${aws_lb.main.dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for pushing Docker images"
  value       = aws_ecr_repository.rag.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name (for CLI commands)"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.rag.name
}

output "efs_id" {
  description = "EFS file system ID (for inspection/debugging)"
  value       = aws_efs_file_system.rag.id
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for ECS tasks"
  value       = aws_cloudwatch_log_group.rag.name
}
