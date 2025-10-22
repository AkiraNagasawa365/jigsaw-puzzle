resource "aws_ssm_parameter" "frontend_api_base_url" {
  name        = "/${var.project_name}/frontend/${var.environment}/api_base_url"
  description = "Base URL for the frontend to reach API Gateway"
  type        = "String"
  value       = module.api_gateway.api_endpoint

  tags = local.common_tags
}

# ============================================
# Frontend Resources Information (for CI/CD)
# ============================================
# デプロイスクリプトが必要とするリソース情報をまとめて保存
resource "aws_ssm_parameter" "frontend_resources" {
  name        = "/${var.project_name}/frontend/${var.environment}/resources"
  description = "Frontend deployment resource information (S3, CloudFront, etc.)"
  type        = "String"
  value = jsonencode({
    s3_bucket_name            = module.frontend.s3_bucket_name
    cloudfront_distribution_id = module.frontend.cloudfront_distribution_id
    cloudfront_domain_name    = module.frontend.cloudfront_domain_name
    api_base_url              = module.api_gateway.api_endpoint
    environment               = var.environment
  })

  tags = local.common_tags
}
