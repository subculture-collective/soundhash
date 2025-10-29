# RDS PostgreSQL Database

resource "aws_db_parameter_group" "postgres" {
  name_prefix = "${local.cluster_name}-postgres-"
  family      = "postgres16"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "ddl"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  tags = local.common_tags
}

resource "aws_db_instance" "postgres" {
  identifier     = "${local.cluster_name}-postgres"
  engine         = "postgres"
  engine_version = "16.1"
  instance_class = var.db_instance_class

  # Storage
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage * 2  # Auto-scaling up to 2x
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = aws_kms_key.rds.arn

  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Network
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.postgres.id]
  publicly_accessible    = false

  # High availability
  multi_az = true

  # Backups
  backup_retention_period   = var.db_backup_retention_period
  backup_window             = "03:00-04:00"
  maintenance_window        = "mon:04:00-mon:05:00"
  copy_tags_to_snapshot     = true
  skip_final_snapshot       = false
  final_snapshot_identifier = "${local.cluster_name}-postgres-final"

  # Performance Insights
  performance_insights_enabled    = true
  performance_insights_kms_key_id = aws_kms_key.rds.arn
  performance_insights_retention_period = 7

  # Enhanced monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = 60
  monitoring_role_arn             = aws_iam_role.rds_monitoring.arn

  # Parameter group
  parameter_group_name = aws_db_parameter_group.postgres.name

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  # Deletion protection
  deletion_protection = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-postgres"
    }
  )
}

# KMS key for RDS encryption
resource "aws_kms_key" "rds" {
  description             = "KMS key for RDS encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-rds-kms"
    }
  )
}

resource "aws_kms_alias" "rds" {
  name          = "alias/${local.cluster_name}-rds"
  target_key_id = aws_kms_key.rds.key_id
}

# IAM role for RDS enhanced monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${local.cluster_name}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = aws_iam_role.rds_monitoring.name
}

# Read replica (optional, uncomment for production)
# resource "aws_db_instance" "postgres_replica" {
#   identifier             = "${local.cluster_name}-postgres-replica"
#   replicate_source_db    = aws_db_instance.postgres.identifier
#   instance_class         = var.db_instance_class
#   publicly_accessible    = false
#   skip_final_snapshot    = true
#   vpc_security_group_ids = [aws_security_group.postgres.id]
#   
#   tags = merge(
#     local.common_tags,
#     {
#       Name = "${local.cluster_name}-postgres-replica"
#     }
#   )
# }
