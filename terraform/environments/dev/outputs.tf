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
