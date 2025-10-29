# VPC and Networking Configuration

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${local.cluster_name}-vpc"
  cidr = var.vpc_cidr

  azs             = var.availability_zones
  private_subnets = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr, 4, k)]
  public_subnets  = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, k + 100)]
  database_subnets = [for k, v in var.availability_zones : cidrsubnet(var.vpc_cidr, 8, k + 200)]

  enable_nat_gateway     = true
  single_nat_gateway     = false  # High availability - one NAT per AZ
  one_nat_gateway_per_az = true
  enable_dns_hostnames   = true
  enable_dns_support     = true

  # VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true

  # Tags for EKS
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = "1"
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }

  tags = local.common_tags
}

# Security group for RDS
resource "aws_security_group" "postgres" {
  name_prefix = "${local.cluster_name}-postgres-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for PostgreSQL RDS"

  ingress {
    description     = "PostgreSQL from EKS"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-postgres-sg"
    }
  )
}

# Security group for Redis
resource "aws_security_group" "redis" {
  name_prefix = "${local.cluster_name}-redis-"
  vpc_id      = module.vpc.vpc_id
  description = "Security group for Redis ElastiCache"

  ingress {
    description     = "Redis from EKS"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [module.eks.cluster_security_group_id]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-redis-sg"
    }
  )
}

# DB Subnet Group
resource "aws_db_subnet_group" "postgres" {
  name       = "${local.cluster_name}-postgres"
  subnet_ids = module.vpc.database_subnets

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-postgres-subnet-group"
    }
  )
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "redis" {
  name       = "${local.cluster_name}-redis"
  subnet_ids = module.vpc.database_subnets

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-redis-subnet-group"
    }
  )
}
