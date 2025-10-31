# Terraform variables for SoundHash infrastructure

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (production, staging, development)"
  type        = string
  default     = "production"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "soundhash"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# EKS Configuration
variable "eks_cluster_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.28"
}

variable "eks_node_groups" {
  description = "EKS node group configurations"
  type = map(object({
    desired_size   = number
    min_size       = number
    max_size       = number
    instance_types = list(string)
    capacity_type  = string
  }))
  default = {
    general = {
      desired_size   = 3
      min_size       = 2
      max_size       = 10
      instance_types = ["t3.xlarge"]
      capacity_type  = "ON_DEMAND"
    }
    spot = {
      desired_size   = 2
      min_size       = 0
      max_size       = 8
      instance_types = ["t3.large", "t3.xlarge"]
      capacity_type  = "SPOT"
    }
  }
}

# RDS Configuration
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.r6g.xlarge"
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "soundhash"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_backup_retention_period" {
  description = "Number of days to retain database backups"
  type        = number
  default     = 30
}

# ElastiCache Configuration
variable "redis_node_type" {
  description = "ElastiCache Redis node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "redis_num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

# S3 Configuration
variable "s3_bucket_name" {
  description = "S3 bucket name for storage"
  type        = string
  default     = "soundhash-storage-prod"
}

# Tags
variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "soundhash"
    ManagedBy   = "terraform"
    Environment = "production"
  }
}

# ==================== CDN & Edge Computing Configuration ====================

# CloudFront CDN
variable "cloudfront_price_class" {
  description = "CloudFront price class (PriceClass_All for global, PriceClass_200 for most regions, PriceClass_100 for US/EU)"
  type        = string
  default     = "PriceClass_All"
}

variable "cloudfront_aliases" {
  description = "CloudFront alternate domain names (CNAMEs)"
  type        = list(string)
  default     = []
}

variable "cloudfront_origin_verify_secret" {
  description = "Secret for verifying CloudFront origin requests"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cloudfront_geo_restriction_type" {
  description = "Type of geo restriction (none, whitelist, blacklist)"
  type        = string
  default     = "none"
}

variable "cloudfront_geo_restriction_locations" {
  description = "List of country codes for geo restriction"
  type        = list(string)
  default     = []
}

# ACM Certificate
variable "acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront (must be in us-east-1)"
  type        = string
  default     = ""
}

# WAF
variable "waf_web_acl_id" {
  description = "WAF Web ACL ID for CloudFront"
  type        = string
  default     = ""
}

# ==================== Multi-Region Configuration ====================

# Database Multi-Region
variable "enable_read_replicas" {
  description = "Enable RDS read replicas in multiple regions"
  type        = bool
  default     = false
}

variable "enable_global_database" {
  description = "Enable Aurora Global Database (recommended for multi-region)"
  type        = bool
  default     = false
}

variable "aurora_instance_class" {
  description = "Aurora instance class for global database"
  type        = string
  default     = "db.r6g.large"
}

variable "aurora_instance_count" {
  description = "Number of Aurora instances per cluster"
  type        = number
  default     = 2
}

variable "db_replica_instance_class" {
  description = "RDS read replica instance class"
  type        = string
  default     = "db.r6g.large"
}

# Application Load Balancers (Multi-Region)
variable "alb_domain_name" {
  description = "ALB domain name for US East region"
  type        = string
  default     = ""
}

variable "alb_zone_id" {
  description = "ALB hosted zone ID for US East region"
  type        = string
  default     = ""
}

variable "alb_domain_name_eu" {
  description = "ALB domain name for EU West region"
  type        = string
  default     = ""
}

variable "alb_zone_id_eu" {
  description = "ALB hosted zone ID for EU West region"
  type        = string
  default     = ""
}

variable "alb_domain_name_apac" {
  description = "ALB domain name for AP Southeast region"
  type        = string
  default     = ""
}

variable "alb_zone_id_apac" {
  description = "ALB hosted zone ID for AP Southeast region"
  type        = string
  default     = ""
}

# Route53 Geographic Routing
variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "soundhash.io"
}

variable "create_route53_zone" {
  description = "Create Route53 hosted zone"
  type        = bool
  default     = false
}

variable "enable_geolocation_routing" {
  description = "Enable geolocation-based routing"
  type        = bool
  default     = true
}

variable "enable_latency_routing" {
  description = "Enable latency-based routing (alternative to geolocation)"
  type        = bool
  default     = false
}

# Monitoring & Alerting
variable "sns_alert_topic_arn" {
  description = "SNS topic ARN for alerts"
  type        = string
  default     = ""
}
