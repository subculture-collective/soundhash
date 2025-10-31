# Multi-Region RDS Configuration for Global Performance

# Aurora Global Database (recommended for multi-region)
# Uncomment to use Aurora instead of standard RDS

# Primary cluster in us-east-1
resource "aws_rds_global_cluster" "soundhash" {
  count                     = var.enable_global_database ? 1 : 0
  global_cluster_identifier = "${local.cluster_name}-global"
  engine                    = "aurora-postgresql"
  engine_version           = "16.1"
  database_name            = var.db_name
  storage_encrypted        = true
  
  lifecycle {
    ignore_changes = [engine_version]
  }
}

resource "aws_rds_cluster" "primary" {
  count                       = var.enable_global_database ? 1 : 0
  cluster_identifier          = "${local.cluster_name}-primary"
  engine                      = "aurora-postgresql"
  engine_version             = "16.1"
  engine_mode                = "provisioned"
  database_name              = var.db_name
  master_username            = var.db_username
  master_password            = var.db_password
  backup_retention_period    = 35
  preferred_backup_window    = "03:00-04:00"
  preferred_maintenance_window = "mon:04:00-mon:05:00"
  
  global_cluster_identifier  = aws_rds_global_cluster.soundhash[0].id
  
  vpc_security_group_ids     = [aws_security_group.postgres.id]
  db_subnet_group_name       = aws_db_subnet_group.main.name
  
  # Enable encryption
  storage_encrypted          = true
  kms_key_id                = aws_kms_key.rds.arn
  
  # Performance Insights
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Deletion protection
  deletion_protection        = var.environment == "production" ? true : false
  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${local.cluster_name}-final-snapshot" : null
  
  lifecycle {
    ignore_changes = [final_snapshot_identifier]
  }
  
  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-primary-cluster"
      Region = "us-east-1"
    }
  )
}

resource "aws_rds_cluster_instance" "primary" {
  count                = var.enable_global_database ? var.aurora_instance_count : 0
  identifier           = "${local.cluster_name}-primary-${count.index}"
  cluster_identifier   = aws_rds_cluster.primary[0].id
  instance_class       = var.aurora_instance_class
  engine               = aws_rds_cluster.primary[0].engine
  engine_version       = aws_rds_cluster.primary[0].engine_version
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-primary-instance-${count.index}"
    }
  )
}

# Read Replicas for Standard RDS (if not using Aurora Global)

# EU-WEST-1 Read Replica
resource "aws_db_instance" "replica_eu_west" {
  count                  = var.enable_read_replicas && !var.enable_global_database ? 1 : 0
  identifier             = "${local.cluster_name}-replica-eu-west-1"
  replicate_source_db    = aws_db_instance.postgres.identifier
  instance_class         = var.db_replica_instance_class
  
  # Storage
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_allocated_storage * 2
  storage_type          = "gp3"
  storage_encrypted     = true
  
  # Monitoring
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Backup
  backup_retention_period = 7
  skip_final_snapshot    = true
  
  # Multi-AZ for high availability
  multi_az = true
  
  # Auto minor version upgrade
  auto_minor_version_upgrade = true
  
  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-replica-eu-west-1"
      Region = "eu-west-1"
      Role   = "read-replica"
    }
  )
  
  provider = aws.eu_west
}

# APAC (Singapore) Read Replica
resource "aws_db_instance" "replica_ap_southeast" {
  count                  = var.enable_read_replicas && !var.enable_global_database ? 1 : 0
  identifier             = "${local.cluster_name}-replica-ap-southeast-1"
  replicate_source_db    = aws_db_instance.postgres.identifier
  instance_class         = var.db_replica_instance_class
  
  # Storage
  allocated_storage      = var.db_allocated_storage
  max_allocated_storage  = var.db_allocated_storage * 2
  storage_type          = "gp3"
  storage_encrypted     = true
  
  # Monitoring
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  enabled_cloudwatch_logs_exports = ["postgresql"]
  
  # Backup
  backup_retention_period = 7
  skip_final_snapshot    = true
  
  # Multi-AZ for high availability
  multi_az = true
  
  # Auto minor version upgrade
  auto_minor_version_upgrade = true
  
  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-replica-ap-southeast-1"
      Region = "ap-southeast-1"
      Role   = "read-replica"
    }
  )
  
  provider = aws.ap_southeast
}

# Secondary Aurora clusters for Global Database (EU-WEST-1)
resource "aws_rds_cluster" "secondary_eu" {
  count                       = var.enable_global_database ? 1 : 0
  provider                    = aws.eu_west
  cluster_identifier          = "${local.cluster_name}-secondary-eu"
  engine                      = "aurora-postgresql"
  engine_version             = "16.1"
  
  global_cluster_identifier  = aws_rds_global_cluster.soundhash[0].id
  
  # Note: Create dedicated security group for EU region or use primary region's
  # vpc_security_group_ids     = [aws_security_group.postgres_eu.id]
  # db_subnet_group_name       = aws_db_subnet_group.eu.name
  # For now, commenting out to avoid errors. Define these resources in vpc.tf for multi-region setup
  
  # Replication
  replication_source_identifier = aws_rds_cluster.primary[0].arn
  
  # Enable encryption
  storage_encrypted          = true
  kms_key_id                = aws_kms_key.rds_eu.arn
  
  skip_final_snapshot       = var.environment != "production"
  
  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-secondary-eu"
      Region = "eu-west-1"
    }
  )
  
  depends_on = [aws_rds_cluster_instance.primary]
}

resource "aws_rds_cluster_instance" "secondary_eu" {
  count                = var.enable_global_database ? var.aurora_instance_count : 0
  provider             = aws.eu_west
  identifier           = "${local.cluster_name}-secondary-eu-${count.index}"
  cluster_identifier   = aws_rds_cluster.secondary_eu[0].id
  instance_class       = var.aurora_instance_class
  engine               = aws_rds_cluster.secondary_eu[0].engine
  engine_version       = aws_rds_cluster.secondary_eu[0].engine_version
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-secondary-eu-instance-${count.index}"
    }
  )
}

# Secondary Aurora clusters for Global Database (AP-SOUTHEAST-1)
resource "aws_rds_cluster" "secondary_apac" {
  count                       = var.enable_global_database ? 1 : 0
  provider                    = aws.ap_southeast
  cluster_identifier          = "${local.cluster_name}-secondary-apac"
  engine                      = "aurora-postgresql"
  engine_version             = "16.1"
  
  global_cluster_identifier  = aws_rds_global_cluster.soundhash[0].id
  
  # Note: Create dedicated security group for APAC region or use primary region's
  # vpc_security_group_ids     = [aws_security_group.postgres_apac.id]
  # db_subnet_group_name       = aws_db_subnet_group.apac.name
  # For now, commenting out to avoid errors. Define these resources in vpc.tf for multi-region setup
  
  # Replication
  replication_source_identifier = aws_rds_cluster.primary[0].arn
  
  # Enable encryption
  storage_encrypted          = true
  kms_key_id                = aws_kms_key.rds_apac.arn
  
  skip_final_snapshot       = var.environment != "production"
  
  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-secondary-apac"
      Region = "ap-southeast-1"
    }
  )
  
  depends_on = [aws_rds_cluster_instance.primary]
}

resource "aws_rds_cluster_instance" "secondary_apac" {
  count                = var.enable_global_database ? var.aurora_instance_count : 0
  provider             = aws.ap_southeast
  identifier           = "${local.cluster_name}-secondary-apac-${count.index}"
  cluster_identifier   = aws_rds_cluster.secondary_apac[0].id
  instance_class       = var.aurora_instance_class
  engine               = aws_rds_cluster.secondary_apac[0].engine
  engine_version       = aws_rds_cluster.secondary_apac[0].engine_version
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_monitoring.arn
  
  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-secondary-apac-instance-${count.index}"
    }
  )
}

# IAM role for RDS monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${local.cluster_name}-rds-monitoring-role"

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
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Outputs
output "primary_cluster_endpoint" {
  description = "Primary Aurora cluster endpoint"
  value       = var.enable_global_database ? aws_rds_cluster.primary[0].endpoint : null
}

output "primary_cluster_reader_endpoint" {
  description = "Primary Aurora cluster reader endpoint"
  value       = var.enable_global_database ? aws_rds_cluster.primary[0].reader_endpoint : null
}

output "secondary_eu_cluster_endpoint" {
  description = "Secondary EU Aurora cluster endpoint"
  value       = var.enable_global_database ? aws_rds_cluster.secondary_eu[0].endpoint : null
}

output "secondary_apac_cluster_endpoint" {
  description = "Secondary APAC Aurora cluster endpoint"
  value       = var.enable_global_database ? aws_rds_cluster.secondary_apac[0].endpoint : null
}

output "read_replica_eu_endpoint" {
  description = "EU West read replica endpoint"
  value       = var.enable_read_replicas && !var.enable_global_database ? aws_db_instance.replica_eu_west[0].endpoint : null
}

output "read_replica_apac_endpoint" {
  description = "APAC Southeast read replica endpoint"
  value       = var.enable_read_replicas && !var.enable_global_database ? aws_db_instance.replica_ap_southeast[0].endpoint : null
}
