# ============================================
# API Gateway Module Variables
# ============================================

# --------------------------------------------
# 基本設定
# --------------------------------------------

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

# --------------------------------------------
# Lambda統合設定
# --------------------------------------------

variable "puzzle_register_lambda_function_name" {
  description = "Name of the puzzle register Lambda function"
  type        = string
}

variable "puzzle_register_lambda_invoke_arn" {
  description = "Invoke ARN of the puzzle register Lambda function"
  type        = string
}

# --------------------------------------------
# ログ設定
# --------------------------------------------

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days"
  type        = number
  default     = 7
}

# --------------------------------------------
# スロットリング設定（Rate Limiting）
# --------------------------------------------

variable "throttling_burst_limit" {
  description = "API Gateway throttling burst limit (requests)"
  type        = number
  default     = 5000
}

variable "throttling_rate_limit" {
  description = "API Gateway throttling rate limit (requests per second)"
  type        = number
  default     = 10000
}
