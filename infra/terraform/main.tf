# ─────────────────────────────────────────────────────────────────
# Self-Evaluation RAG  –  AWS Infrastructure (Terraform)
#
# Resources created:
#   VPC + subnets + internet gateway
#   ECR repository (stores Docker image)
#   ECS Cluster + Fargate task definition
#   ALB (public HTTPS load balancer)
#   EFS (persistent volumes for data/index/logs)
#   Secrets Manager (admin password)
#   CloudWatch log groups
# ─────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment after creating the S3 bucket + DynamoDB table
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "rag/terraform.tfstate"
  #   region         = var.aws_region
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}

# ── Data sources ──────────────────────────────────────────────────
data "aws_availability_zones" "available" {}


# ── VPC ───────────────────────────────────────────────────────────
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "${var.project_name}-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(aws_vpc.main.cidr_block, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = { Name = "${var.project_name}-private-${count.index}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  tags = { Name = "${var.project_name}-public-rt" }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}


# ── Security Groups ───────────────────────────────────────────────
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "ALB – allow HTTP/HTTPS from internet"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "${var.project_name}-ecs-sg"
  description = "ECS tasks – allow ALB inbound only"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8501
    to_port         = 8501
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  ingress {
    from_port       = 11434
    to_port         = 11434
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "efs" {
  name        = "${var.project_name}-efs-sg"
  description = "EFS – allow NFS from ECS tasks"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# ── ECR Repository ────────────────────────────────────────────────
resource "aws_ecr_repository" "rag" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "rag" {
  repository = aws_ecr_repository.rag.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 5 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}


# ── EFS (Persistent Storage) ──────────────────────────────────────
resource "aws_efs_file_system" "rag" {
  creation_token   = "${var.project_name}-efs"
  performance_mode = "generalPurpose"
  throughput_mode  = "bursting"
  encrypted        = true
  tags             = { Name = "${var.project_name}-efs" }
}

resource "aws_efs_mount_target" "rag" {
  count           = 2
  file_system_id  = aws_efs_file_system.rag.id
  subnet_id       = aws_subnet.public[count.index].id
  security_groups = [aws_security_group.efs.id]
}

# Access points – one per logical volume
resource "aws_efs_access_point" "data" {
  file_system_id = aws_efs_file_system.rag.id
  posix_user     = { uid = 1000, gid = 1000 }
  root_directory {
    path = "/data"
    creation_info = { owner_uid = 1000, owner_gid = 1000, permissions = "755" }
  }
  tags = { Name = "rag-data" }
}

resource "aws_efs_access_point" "index" {
  file_system_id = aws_efs_file_system.rag.id
  posix_user     = { uid = 1000, gid = 1000 }
  root_directory {
    path = "/index"
    creation_info = { owner_uid = 1000, owner_gid = 1000, permissions = "755" }
  }
  tags = { Name = "rag-index" }
}

resource "aws_efs_access_point" "logs" {
  file_system_id = aws_efs_file_system.rag.id
  posix_user     = { uid = 1000, gid = 1000 }
  root_directory {
    path = "/logs"
    creation_info = { owner_uid = 1000, owner_gid = 1000, permissions = "755" }
  }
  tags = { Name = "rag-logs" }
}


# ── Secrets Manager ───────────────────────────────────────────────
resource "aws_secretsmanager_secret" "admin_password" {
  name                    = "${var.project_name}/admin-password"
  description             = "RAG app admin dashboard password"
  recovery_window_in_days = 0   # allow immediate delete for dev; increase in prod
}

resource "aws_secretsmanager_secret_version" "admin_password" {
  secret_id     = aws_secretsmanager_secret.admin_password.id
  secret_string = jsonencode({ ADMIN_PASSWORD = var.admin_password })
}


# ── IAM Roles ─────────────────────────────────────────────────────
resource "aws_iam_role" "ecs_task_execution" {
  name = "${var.project_name}-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_basic" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_exec_secrets" {
  name = "allow-secrets"
  role = aws_iam_role.ecs_task_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.admin_password.arn]
    }]
  })
}

resource "aws_iam_role" "ecs_task" {
  name = "${var.project_name}-task-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_efs" {
  name = "allow-efs"
  role = aws_iam_role.ecs_task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["elasticfilesystem:ClientMount", "elasticfilesystem:ClientWrite"]
      Resource = [aws_efs_file_system.rag.arn]
    }]
  })
}


# ── CloudWatch Log Group ──────────────────────────────────────────
resource "aws_cloudwatch_log_group" "rag" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 14
}


# ── ECS Cluster ───────────────────────────────────────────────────
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  configuration {
    execute_command_configuration {
      logging = "OVERRIDE"
      log_configuration {
        cloud_watch_log_group_name = aws_cloudwatch_log_group.rag.name
      }
    }
  }
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}


# ── ECS Task Definition ───────────────────────────────────────────
resource "aws_ecs_task_definition" "rag" {
  family                   = var.project_name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  # EFS volume mounts
  volume {
    name = "rag-data"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.rag.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.data.id
        iam             = "ENABLED"
      }
    }
  }
  volume {
    name = "rag-index"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.rag.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.index.id
        iam             = "ENABLED"
      }
    }
  }
  volume {
    name = "rag-logs"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.rag.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.logs.id
        iam             = "ENABLED"
      }
    }
  }

  container_definitions = jsonencode([
    # ── Container 1: Ollama LLM sidecar ─────────────────────────
    {
      name      = "ollama"
      image     = "ollama/ollama:latest"
      essential = true
      portMappings = [{ containerPort = 11434, protocol = "tcp" }]

      environment = [
        { name = "OLLAMA_KEEP_ALIVE", value = "24h" }
      ]

      # Pull model on startup via entryPoint override
      command = [
        "sh", "-c",
        "ollama serve & sleep 10 && ollama pull gemma3:1b && wait"
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.rag.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ollama"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:11434/ || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 5
        startPeriod = 120
      }
    },

    # ── Container 2: RAG Streamlit app ───────────────────────────
    {
      name      = "rag-app"
      image     = "${aws_ecr_repository.rag.repository_url}:latest"
      essential = true
      portMappings = [{ containerPort = 8501, protocol = "tcp" }]

      dependsOn = [{ containerName = "ollama", condition = "HEALTHY" }]

      environment = [
        { name = "OLLAMA_HOST", value = "http://localhost:11434" }
      ]

      secrets = [
        {
          name      = "ADMIN_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.admin_password.arn}:ADMIN_PASSWORD::"
        }
      ]

      mountPoints = [
        { sourceVolume = "rag-data",  containerPath = "/app/data",  readOnly = false },
        { sourceVolume = "rag-index", containerPath = "/app/index", readOnly = false },
        { sourceVolume = "rag-logs",  containerPath = "/app/logs",  readOnly = false }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.rag.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "rag-app"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8501/_stcore/health || exit 1"]
        interval    = 30
        timeout     = 10
        retries     = 3
        startPeriod = 60
      }
    }
  ])
}


# ── Application Load Balancer ─────────────────────────────────────
resource "aws_lb" "main" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
}

resource "aws_lb_target_group" "rag" {
  name        = "${var.project_name}-tg"
  port        = 8501
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    path                = "/_stcore/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.rag.arn
  }
}


# ── ECS Service ───────────────────────────────────────────────────
resource "aws_ecs_service" "rag" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.rag.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.rag.arn
    container_name   = "rag-app"
    container_port   = 8501
  }

  depends_on = [
    aws_lb_listener.http,
    aws_efs_mount_target.rag
  ]

  lifecycle {
    ignore_changes = [desired_count]
  }
}
