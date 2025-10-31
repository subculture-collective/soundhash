# Regional Latency Monitoring and Alerting

# CloudWatch Synthetics Canaries for Regional Latency Monitoring

# IAM role for Canary execution
resource "aws_iam_role" "canary" {
  name = "${local.cluster_name}-canary-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "canary_basic" {
  role       = aws_iam_role.canary.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "canary_cloudwatch" {
  role       = aws_iam_role.canary.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchSyntheticsFullAccess"
}

# S3 bucket for Canary artifacts
resource "aws_s3_bucket" "canary_artifacts" {
  bucket = "${var.s3_bucket_name}-canary-artifacts"

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-canary-artifacts"
    }
  )
}

resource "aws_s3_bucket_lifecycle_configuration" "canary_artifacts" {
  bucket = aws_s3_bucket.canary_artifacts.id

  rule {
    id     = "delete-old-artifacts"
    status = "Enabled"

    expiration {
      days = 30
    }
  }
}

# Archive the canary code for deployment
data "archive_file" "latency_monitor" {
  type        = "zip"
  source_file = "${path.module}/canary/latencyMonitor.js"
  output_path = "${path.module}/canary/latency-monitor.zip"
}

# Canary for US East region
resource "aws_synthetics_canary" "us_east_latency" {
  name                 = "${local.cluster_name}-us-east-latency"
  artifact_s3_location = "s3://${aws_s3_bucket.canary_artifacts.id}/us-east/"
  execution_role_arn   = aws_iam_role.canary.arn
  handler              = "latencyMonitor.handler"
  zip_file             = data.archive_file.latency_monitor.output_path
  runtime_version      = "syn-nodejs-puppeteer-9.0"

  schedule {
    expression = "rate(5 minutes)"
  }

  run_config {
    timeout_in_seconds = 60
    memory_in_mb      = 960
    active_tracing    = true
    environment_variables = {
      REGION          = "us-east-1"
      API_ENDPOINT    = "https://api.${var.domain_name}"
      THRESHOLD_MS    = "500"
    }
  }

  success_retention_period = 2
  failure_retention_period = 14

  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-us-east-latency"
      Region = "us-east-1"
    }
  )
}

# Canary for EU West region
resource "aws_synthetics_canary" "eu_west_latency" {
  provider             = aws.eu_west
  name                 = "${local.cluster_name}-eu-west-latency"
  artifact_s3_location = "s3://${aws_s3_bucket.canary_artifacts.id}/eu-west/"
  execution_role_arn   = aws_iam_role.canary.arn
  handler              = "latencyMonitor.handler"
  zip_file             = data.archive_file.latency_monitor.output_path
  runtime_version      = "syn-nodejs-puppeteer-9.0"

  schedule {
    expression = "rate(5 minutes)"
  }

  run_config {
    timeout_in_seconds = 60
    memory_in_mb      = 960
    active_tracing    = true
    environment_variables = {
      REGION          = "eu-west-1"
      API_ENDPOINT    = "https://api.${var.domain_name}"
      THRESHOLD_MS    = "500"
    }
  }

  success_retention_period = 2
  failure_retention_period = 14

  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-eu-west-latency"
      Region = "eu-west-1"
    }
  )
}

# Canary for AP Southeast region
resource "aws_synthetics_canary" "ap_southeast_latency" {
  provider             = aws.ap_southeast
  name                 = "${local.cluster_name}-ap-southeast-latency"
  artifact_s3_location = "s3://${aws_s3_bucket.canary_artifacts.id}/ap-southeast/"
  execution_role_arn   = aws_iam_role.canary.arn
  handler              = "latencyMonitor.handler"
  zip_file             = data.archive_file.latency_monitor.output_path
  runtime_version      = "syn-nodejs-puppeteer-9.0"

  schedule {
    expression = "rate(5 minutes)"
  }

  run_config {
    timeout_in_seconds = 60
    memory_in_mb      = 960
    active_tracing    = true
    environment_variables = {
      REGION          = "ap-southeast-1"
      API_ENDPOINT    = "https://api.${var.domain_name}"
      THRESHOLD_MS    = "500"
    }
  }

  success_retention_period = 2
  failure_retention_period = 14

  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-ap-southeast-latency"
      Region = "ap-southeast-1"
    }
  )
}

# CloudWatch alarms for regional latency
resource "aws_cloudwatch_metric_alarm" "us_east_high_latency" {
  alarm_name          = "${local.cluster_name}-us-east-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "CloudWatchSynthetics"
  period              = "300"
  statistic           = "Average"
  threshold           = "500"
  alarm_description   = "High latency detected in US East region"
  treat_missing_data  = "notBreaching"

  dimensions = {
    CanaryName = aws_synthetics_canary.us_east_latency.name
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "eu_west_high_latency" {
  provider            = aws.eu_west
  alarm_name          = "${local.cluster_name}-eu-west-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "CloudWatchSynthetics"
  period              = "300"
  statistic           = "Average"
  threshold           = "500"
  alarm_description   = "High latency detected in EU West region"
  treat_missing_data  = "notBreaching"

  dimensions = {
    CanaryName = aws_synthetics_canary.eu_west_latency.name
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "ap_southeast_high_latency" {
  provider            = aws.ap_southeast
  alarm_name          = "${local.cluster_name}-ap-southeast-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "CloudWatchSynthetics"
  period              = "300"
  statistic           = "Average"
  threshold           = "500"
  alarm_description   = "High latency detected in AP Southeast region"
  treat_missing_data  = "notBreaching"

  dimensions = {
    CanaryName = aws_synthetics_canary.ap_southeast_latency.name
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = local.common_tags
}

# CloudWatch Dashboard for Regional Performance
resource "aws_cloudwatch_dashboard" "regional_performance" {
  dashboard_name = "${local.cluster_name}-regional-performance"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["CloudWatchSynthetics", "Duration", { stat = "Average", label = "US East Latency" }],
            ["...", { stat = "Average", label = "EU West Latency" }],
            ["...", { stat = "Average", label = "AP Southeast Latency" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Regional API Latency"
          yAxis = {
            left = {
              label = "Milliseconds"
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/Route53", "HealthCheckStatus", "HealthCheckId", aws_route53_health_check.us_east.id, { label = "US East Health" }],
            ["...", aws_route53_health_check.eu_west.id, { label = "EU West Health" }],
            ["...", aws_route53_health_check.ap_southeast.id, { label = "AP Southeast Health" }]
          ]
          period = 60
          stat   = "Minimum"
          region = var.aws_region
          title  = "Regional Health Status"
          yAxis = {
            left = {
              min = 0
              max = 1
            }
          }
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/CloudFront", "Requests", "DistributionId", aws_cloudfront_distribution.main.id, { stat = "Sum", label = "Total Requests" }],
            [".", "BytesDownloaded", ".", ".", { stat = "Sum", label = "Bytes Downloaded" }],
            [".", "4xxErrorRate", ".", ".", { stat = "Average", label = "4xx Error Rate" }],
            [".", "5xxErrorRate", ".", ".", { stat = "Average", label = "5xx Error Rate" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "CDN Performance"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", { stat = "Average", label = "Primary DB Connections" }],
            [".", "CPUUtilization", { stat = "Average", label = "Primary DB CPU" }],
            [".", "FreeableMemory", { stat = "Average", label = "Primary DB Memory" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Database Performance"
        }
      }
    ]
  })
}

# Custom metrics for edge latency tracking
resource "aws_cloudwatch_log_metric_filter" "edge_latency" {
  name           = "${local.cluster_name}-edge-latency"
  log_group_name = aws_cloudwatch_log_group.edge_fingerprint_cache.name
  pattern        = "[time, request_id, level, msg, latency]"

  metric_transformation {
    name      = "EdgeLatency"
    namespace = "${local.cluster_name}/EdgePerformance"
    value     = "$latency"
    unit      = "Milliseconds"
  }
}

# Outputs
output "canary_us_east_name" {
  description = "Canary name for US East region"
  value       = aws_synthetics_canary.us_east_latency.name
}

output "canary_eu_west_name" {
  description = "Canary name for EU West region"
  value       = aws_synthetics_canary.eu_west_latency.name
}

output "canary_ap_southeast_name" {
  description = "Canary name for AP Southeast region"
  value       = aws_synthetics_canary.ap_southeast_latency.name
}

output "regional_performance_dashboard" {
  description = "CloudWatch dashboard for regional performance"
  value       = aws_cloudwatch_dashboard.regional_performance.dashboard_name
}
