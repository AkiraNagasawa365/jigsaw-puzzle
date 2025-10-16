variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket for images"
  type        = string
}

variable "puzzles_table_name" {
  description = "Name of the Puzzles DynamoDB table"
  type        = string
}

variable "pieces_table_name" {
  description = "Name of the Pieces DynamoDB table"
  type        = string
}

variable "puzzle_register_zip_path" {
  description = "Path to the puzzle register Lambda function zip file"
  type        = string
  default     = "../../lambda/puzzle-register/function.zip"
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
  default     = "python3.12"
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 30
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 7
}
