# Route53 Geographic Load Balancing and Health Checks

# Primary hosted zone
resource "aws_route53_zone" "main" {
  count = var.create_route53_zone ? 1 : 0
  name  = var.domain_name

  tags = merge(
    local.common_tags,
    {
      Name = "${local.cluster_name}-zone"
    }
  )
}

# Health check for US East (Primary)
resource "aws_route53_health_check" "us_east" {
  fqdn              = var.alb_domain_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  measure_latency   = true

  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-health-us-east-1"
      Region = "us-east-1"
    }
  )
}

# Health check for EU West
resource "aws_route53_health_check" "eu_west" {
  fqdn              = var.alb_domain_name_eu
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  measure_latency   = true

  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-health-eu-west-1"
      Region = "eu-west-1"
    }
  )
}

# Health check for AP Southeast
resource "aws_route53_health_check" "ap_southeast" {
  fqdn              = var.alb_domain_name_apac
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  failure_threshold = "3"
  request_interval  = "30"
  measure_latency   = true

  tags = merge(
    local.common_tags,
    {
      Name   = "${local.cluster_name}-health-ap-southeast-1"
      Region = "ap-southeast-1"
    }
  )
}

# CloudWatch alarms for health checks
resource "aws_cloudwatch_metric_alarm" "health_check_us_east" {
  alarm_name          = "${local.cluster_name}-health-us-east-1"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Health check failed for US East region"
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = aws_route53_health_check.us_east.id
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "health_check_eu_west" {
  alarm_name          = "${local.cluster_name}-health-eu-west-1"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Health check failed for EU West region"
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = aws_route53_health_check.eu_west.id
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "health_check_ap_southeast" {
  alarm_name          = "${local.cluster_name}-health-ap-southeast-1"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HealthCheckStatus"
  namespace           = "AWS/Route53"
  period              = "60"
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Health check failed for AP Southeast region"
  treat_missing_data  = "breaching"

  dimensions = {
    HealthCheckId = aws_route53_health_check.ap_southeast.id
  }

  alarm_actions = [var.sns_alert_topic_arn]

  tags = local.common_tags
}

# API endpoint with geolocation routing
# Primary record set pointing to CloudFront
resource "aws_route53_record" "api_cloudfront" {
  count   = var.create_route53_zone ? 1 : 0
  zone_id = aws_route53_zone.main[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.main.domain_name
    zone_id                = aws_cloudfront_distribution.main.hosted_zone_id
    evaluate_target_health = true
  }
}

# Geolocation routing - North America (primary)
resource "aws_route53_record" "api_us_east" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "US-East-Primary"
  health_check_id = aws_route53_health_check.us_east.id

  geolocation_routing_policy {
    continent = "NA"
  }

  alias {
    name                   = var.alb_domain_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Geolocation routing - South America (primary)
resource "aws_route53_record" "api_us_east_sa" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "US-East-SA"
  health_check_id = aws_route53_health_check.us_east.id

  geolocation_routing_policy {
    continent = "SA"
  }

  alias {
    name                   = var.alb_domain_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Geolocation routing - Europe
resource "aws_route53_record" "api_eu_west" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "EU-West-Primary"
  health_check_id = aws_route53_health_check.eu_west.id

  geolocation_routing_policy {
    continent = "EU"
  }

  alias {
    name                   = var.alb_domain_name_eu
    zone_id                = var.alb_zone_id_eu
    evaluate_target_health = true
  }
}

# Geolocation routing - Africa
resource "aws_route53_record" "api_eu_west_af" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "EU-West-AF"
  health_check_id = aws_route53_health_check.eu_west.id

  geolocation_routing_policy {
    continent = "AF"
  }

  alias {
    name                   = var.alb_domain_name_eu
    zone_id                = var.alb_zone_id_eu
    evaluate_target_health = true
  }
}

# Geolocation routing - Asia Pacific
resource "aws_route53_record" "api_ap_southeast" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "AP-Southeast-Primary"
  health_check_id = aws_route53_health_check.ap_southeast.id

  geolocation_routing_policy {
    continent = "AS"
  }

  alias {
    name                   = var.alb_domain_name_apac
    zone_id                = var.alb_zone_id_apac
    evaluate_target_health = true
  }
}

# Geolocation routing - Oceania
resource "aws_route53_record" "api_ap_southeast_oc" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "AP-Southeast-OC"
  health_check_id = aws_route53_health_check.ap_southeast.id

  geolocation_routing_policy {
    continent = "OC"
  }

  alias {
    name                   = var.alb_domain_name_apac
    zone_id                = var.alb_zone_id_apac
    evaluate_target_health = true
  }
}

# Default geolocation routing (fallback)
resource "aws_route53_record" "api_default" {
  count           = var.create_route53_zone && var.enable_geolocation_routing ? 1 : 0
  zone_id         = aws_route53_zone.main[0].zone_id
  name            = "api.${var.domain_name}"
  type            = "A"
  set_identifier  = "Default"
  health_check_id = aws_route53_health_check.us_east.id

  geolocation_routing_policy {
    # Use empty block for default geolocation (matches all locations not explicitly matched)
  }

  alias {
    name                   = var.alb_domain_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

# Latency-based routing (alternative to geolocation)
resource "aws_route53_record" "api_latency_us_east" {
  count          = var.create_route53_zone && var.enable_latency_routing ? 1 : 0
  zone_id        = aws_route53_zone.main[0].zone_id
  name           = "api.${var.domain_name}"
  type           = "A"
  set_identifier = "US-East-Latency"

  latency_routing_policy {
    region = "us-east-1"
  }

  alias {
    name                   = var.alb_domain_name
    zone_id                = var.alb_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api_latency_eu_west" {
  count          = var.create_route53_zone && var.enable_latency_routing ? 1 : 0
  zone_id        = aws_route53_zone.main[0].zone_id
  name           = "api.${var.domain_name}"
  type           = "A"
  set_identifier = "EU-West-Latency"

  latency_routing_policy {
    region = "eu-west-1"
  }

  alias {
    name                   = var.alb_domain_name_eu
    zone_id                = var.alb_zone_id_eu
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "api_latency_ap_southeast" {
  count          = var.create_route53_zone && var.enable_latency_routing ? 1 : 0
  zone_id        = aws_route53_zone.main[0].zone_id
  name           = "api.${var.domain_name}"
  type           = "A"
  set_identifier = "AP-Southeast-Latency"

  latency_routing_policy {
    region = "ap-southeast-1"
  }

  alias {
    name                   = var.alb_domain_name_apac
    zone_id                = var.alb_zone_id_apac
    evaluate_target_health = true
  }
}

# Outputs
output "route53_zone_id" {
  description = "Route53 hosted zone ID"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].zone_id : null
}

output "route53_name_servers" {
  description = "Route53 zone name servers"
  value       = var.create_route53_zone ? aws_route53_zone.main[0].name_servers : null
}

output "health_check_us_east_id" {
  description = "Health check ID for US East"
  value       = aws_route53_health_check.us_east.id
}

output "health_check_eu_west_id" {
  description = "Health check ID for EU West"
  value       = aws_route53_health_check.eu_west.id
}

output "health_check_ap_southeast_id" {
  description = "Health check ID for AP Southeast"
  value       = aws_route53_health_check.ap_southeast.id
}
