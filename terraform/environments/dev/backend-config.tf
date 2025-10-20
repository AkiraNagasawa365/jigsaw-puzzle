locals {
  backend_env_parameter_value = join(
    "\n",
    [
      "AWS_REGION=${var.aws_region}",
      "S3_BUCKET_NAME=${module.s3.bucket_name}",
      "PUZZLES_TABLE_NAME=${module.dynamodb.puzzles_table_name}",
      "PIECES_TABLE_NAME=${module.dynamodb.pieces_table_name}",
      "ENVIRONMENT=${var.environment}",
      "ALLOWED_ORIGINS=${join(",", var.allowed_origins)}",
    ],
  )
}

resource "aws_ssm_parameter" "backend_env" {
  name        = "/${var.project_name}/backend/${var.environment}/env"
  description = "Backend .env content for the ${var.environment} environment"
  type        = "String"
  value       = local.backend_env_parameter_value

  tags = local.common_tags
}
