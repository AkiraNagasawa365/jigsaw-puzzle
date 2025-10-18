# Lambda function for puzzle registration
resource "aws_lambda_function" "puzzle_register" {
  filename         = var.puzzle_register_zip_path
  function_name    = "${var.project_name}-${var.environment}-puzzle-register"
  role            = var.lambda_execution_role_arn
  handler         = "index.handler"
  source_code_hash = fileexists(var.puzzle_register_zip_path) ? filebase64sha256(var.puzzle_register_zip_path) : null
  runtime         = var.runtime
  timeout         = var.timeout
  memory_size     = var.memory_size

  environment {
    variables = {
      S3_BUCKET_NAME      = var.s3_bucket_name
      PUZZLES_TABLE_NAME  = var.puzzles_table_name
      PIECES_TABLE_NAME   = var.pieces_table_name
      ENVIRONMENT         = var.environment
      ALLOWED_ORIGINS     = var.allowed_origins
    }
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-puzzle-register"
    }
  )
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "puzzle_register" {
  name              = "/aws/lambda/${aws_lambda_function.puzzle_register.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.common_tags
}
