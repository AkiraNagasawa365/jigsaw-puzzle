# ============================================
# API Gateway Module Outputs
# ============================================
# これらの値は他のモジュールやユーザーから参照されます

# --------------------------------------------
# API Gateway基本情報
# --------------------------------------------

output "rest_api_id" {
  description = "ID of the REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "rest_api_name" {
  description = "Name of the REST API"
  value       = aws_api_gateway_rest_api.main.name
}

output "rest_api_root_resource_id" {
  description = "Root resource ID of the REST API"
  value       = aws_api_gateway_rest_api.main.root_resource_id
}

# --------------------------------------------
# エンドポイントURL
# --------------------------------------------

output "api_endpoint" {
  description = "Base URL of the API Gateway stage"
  value       = aws_api_gateway_stage.main.invoke_url
}

output "puzzles_endpoint" {
  description = "Full URL for the /puzzles endpoint"
  value       = "${aws_api_gateway_stage.main.invoke_url}/puzzles"
}

# --------------------------------------------
# ステージ情報
# --------------------------------------------

output "stage_name" {
  description = "Name of the API Gateway stage"
  value       = aws_api_gateway_stage.main.stage_name
}

output "stage_arn" {
  description = "ARN of the API Gateway stage"
  value       = aws_api_gateway_stage.main.arn
}

# --------------------------------------------
# デプロイメント情報
# --------------------------------------------

output "deployment_id" {
  description = "ID of the API Gateway deployment"
  value       = aws_api_gateway_deployment.main.id
}

output "deployment_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

# --------------------------------------------
# ログ情報
# --------------------------------------------

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.api_gateway.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.api_gateway.arn
}
