variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "jigsaw-puzzle"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "allowed_origins" {
  description = "Allowed origins for CORS (S3 and Lambda)"
  type        = list(string)
  default     = [
    "http://localhost:3000",
    "http://localhost:5173",  # Vite dev server
    "https://dykwhpbm0bhdv.cloudfront.net"  # CloudFront distribution
  ]
}
