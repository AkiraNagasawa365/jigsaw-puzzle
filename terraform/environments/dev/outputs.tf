output "s3_bucket_name" {
  description = "Name of the S3 bucket for images"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "puzzles_table_name" {
  description = "Name of the Puzzles DynamoDB table"
  value       = module.dynamodb.puzzles_table_name
}

output "pieces_table_name" {
  description = "Name of the Pieces DynamoDB table"
  value       = module.dynamodb.pieces_table_name
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_execution_role_arn
}

# ============================================
# Cognito Outputs
# ============================================

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID (フロントエンドで使用)"
  value       = module.cognito.user_pool_id
}

output "cognito_client_id" {
  description = "Cognito User Pool Client ID (フロントエンドで使用)"
  value       = module.cognito.client_id
}

output "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN (API Gatewayで使用)"
  value       = module.cognito.user_pool_arn
}

output "cognito_domain" {
  description = "Cognito User Pool Domain"
  value       = module.cognito.domain
}

output "cognito_auth_url" {
  description = "Cognito Hosted UI URL (テスト用)"
  value       = module.cognito.auth_url
}

# ============================================
# Lambda Outputs
# ============================================

output "puzzle_register_lambda_name" {
  description = "Name of the puzzle register Lambda function"
  value       = module.lambda.puzzle_register_function_name
}

output "puzzle_register_lambda_arn" {
  description = "ARN of the puzzle register Lambda function"
  value       = module.lambda.puzzle_register_function_arn
}

# ============================================
# API Gateway Outputs
# ============================================

output "api_endpoint" {
  description = "Base URL of the API Gateway"
  value       = module.api_gateway.api_endpoint
}

output "puzzles_endpoint" {
  description = "Full URL for the /puzzles endpoint"
  value       = module.api_gateway.puzzles_endpoint
}

output "api_gateway_id" {
  description = "ID of the API Gateway REST API"
  value       = module.api_gateway.rest_api_id
}

# ============================================
# Frontend Outputs
# ============================================

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.frontend.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = module.frontend.cloudfront_distribution_id
}

output "frontend_s3_bucket_name" {
  description = "S3 bucket name for frontend files"
  value       = module.frontend.s3_bucket_name
}

output "frontend_api_base_url_parameter" {
  description = "SSM parameter storing the frontend API base URL"
  value       = aws_ssm_parameter.frontend_api_base_url.name
}

output "backend_env_parameter" {
  description = "SSM parameter containing backend environment variables"
  value       = aws_ssm_parameter.backend_env.name
}

# ============================================
# GitHub OIDC Outputs
# ============================================

output "github_actions_role_arn" {
  description = "GitHub ActionsがAssumeするIAMロールのARN（ワークフローで使用）"
  value       = module.github_oidc.github_actions_role_arn
}

output "github_oidc_provider_arn" {
  description = "GitHub OIDC プロバイダーのARN"
  value       = module.github_oidc.oidc_provider_arn
}
