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

variable "s3_bucket_arn" {
  description = "ARN of the S3 bucket for Lambda access"
  type        = string
}

variable "puzzles_table_arn" {
  description = "ARN of the Puzzles DynamoDB table"
  type        = string
}

variable "pieces_table_arn" {
  description = "ARN of the Pieces DynamoDB table"
  type        = string
}
