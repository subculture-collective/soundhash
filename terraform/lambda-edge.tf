# Lambda@Edge for Fingerprint Caching and Low-Latency Processing

# IAM role for Lambda@Edge
resource "aws_iam_role" "lambda_edge" {
  name = "${local.cluster_name}-lambda-edge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "edgelambda.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM policy for Lambda@Edge
resource "aws_iam_role_policy" "lambda_edge" {
  name = "${local.cluster_name}-lambda-edge-policy"
  role = aws_iam_role.lambda_edge.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "elasticache:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda function for fingerprint caching
resource "aws_lambda_function" "edge_fingerprint_cache" {
  filename         = data.archive_file.edge_fingerprint_cache.output_path
  function_name    = "${local.cluster_name}-edge-fingerprint-cache"
  role            = aws_iam_role.lambda_edge.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.edge_fingerprint_cache.output_base64sha256
  runtime         = "nodejs20.x"
  timeout         = 5
  memory_size     = 128
  publish         = true

  environment {
    variables = {
      CACHE_TTL_SECONDS = "1800"
      ENVIRONMENT       = var.environment
    }
  }

  tags = local.common_tags
}

# Archive Lambda@Edge code
data "archive_file" "edge_fingerprint_cache" {
  type        = "zip"
  source_file = "${path.module}/lambda-edge/fingerprint-cache.js"
  output_path = "${path.module}/lambda-edge/fingerprint-cache.zip"
}

# Lambda function for low-latency matching
resource "aws_lambda_function" "edge_low_latency_match" {
  filename         = data.archive_file.edge_low_latency_match.output_path
  function_name    = "${local.cluster_name}-edge-low-latency-match"
  role            = aws_iam_role.lambda_edge.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.edge_low_latency_match.output_base64sha256
  runtime         = "nodejs20.x"
  timeout         = 5
  memory_size     = 256
  publish         = true

  environment {
    variables = {
      SIMILARITY_THRESHOLD = "0.70"
      MAX_RESULTS         = "10"
      ENVIRONMENT         = var.environment
    }
  }

  tags = local.common_tags
}

data "archive_file" "edge_low_latency_match" {
  type        = "zip"
  source_file = "${path.module}/lambda-edge/low-latency-match.js"
  output_path = "${path.module}/lambda-edge/low-latency-match.zip"
}

# CloudWatch log groups for Lambda@Edge (created in us-east-1 and replicated to edge locations)
resource "aws_cloudwatch_log_group" "edge_fingerprint_cache" {
  name              = "/aws/lambda/us-east-1.${aws_lambda_function.edge_fingerprint_cache.function_name}"
  retention_in_days = 7

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "edge_low_latency_match" {
  name              = "/aws/lambda/us-east-1.${aws_lambda_function.edge_low_latency_match.function_name}"
  retention_in_days = 7

  tags = local.common_tags
}

# Outputs
output "edge_fingerprint_cache_arn" {
  description = "Lambda@Edge function ARN for fingerprint caching"
  value       = aws_lambda_function.edge_fingerprint_cache.qualified_arn
}

output "edge_low_latency_match_arn" {
  description = "Lambda@Edge function ARN for low-latency matching"
  value       = aws_lambda_function.edge_low_latency_match.qualified_arn
}
