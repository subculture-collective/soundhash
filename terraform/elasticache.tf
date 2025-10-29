# ElastiCache Redis Cluster

resource "aws_elasticache_parameter_group" "redis" {
  name_prefix = "${local.cluster_name}-redis-"
  family      = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  tags = local.common_tags
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${local.cluster_name}-redis"
  engine               = "redis"
  engine_version       = "7.1"
  node_type            = var.redis_node_type
  num_cache_nodes      = var.redis_num_cache_nodes
  parameter_group_name = aws_elasticache_parameter_group.redis.name
  port                 = 6379

  # Network
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids = [aws_security_group.redis.id]

  # Snapshot and maintenance
  snapshot_retention_limit = 5
  snapshot_window          = "03:00-05:00"
  maintenance_window       = "mon:05:00-mon:07:00"
  
  # Notifications (optional)
  # notification_topic_arn = aws_sns_topic.redis_notifications.arn

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-redis"
    }
  )
}

# For production with replication, use Replication Group instead:
# resource "aws_elasticache_replication_group" "redis" {
#   replication_group_id       = "${local.cluster_name}-redis"
#   replication_group_description = "Redis cluster for SoundHash"
#   engine                     = "redis"
#   engine_version             = "7.1"
#   node_type                  = var.redis_node_type
#   num_cache_clusters         = 3
#   parameter_group_name       = aws_elasticache_parameter_group.redis.name
#   port                       = 6379
#   
#   # Automatic failover
#   automatic_failover_enabled = true
#   multi_az_enabled           = true
#   
#   # Network
#   subnet_group_name          = aws_elasticache_subnet_group.redis.name
#   security_group_ids         = [aws_security_group.redis.id]
#   
#   # Encryption
#   at_rest_encryption_enabled = true
#   transit_encryption_enabled = true
#   auth_token_enabled         = true
#   
#   # Snapshot and maintenance
#   snapshot_retention_limit   = 5
#   snapshot_window            = "03:00-05:00"
#   maintenance_window         = "mon:05:00-mon:07:00"
#   
#   # Auto minor version upgrade
#   auto_minor_version_upgrade = true
#   
#   tags = merge(
#     local.common_tags,
#     {
#       Name = "${local.cluster_name}-redis"
#     }
#   )
# }
