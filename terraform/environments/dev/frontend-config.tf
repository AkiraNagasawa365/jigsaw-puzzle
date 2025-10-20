resource "aws_ssm_parameter" "frontend_api_base_url" {
  name        = "/${var.project_name}/frontend/${var.environment}/api_base_url"
  description = "Base URL for the frontend to reach API Gateway"
  type        = "String"
  value       = module.api_gateway.api_endpoint

  tags = local.common_tags
}
