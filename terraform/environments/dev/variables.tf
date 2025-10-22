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
    "http://localhost:3000",                 # Local development (legacy port)
    "http://localhost:5173",                 # Local development (Vite default)
    "https://dykwhpbm0bhdv.cloudfront.net"   # CloudFront distribution (deployed)
  ]
}

variable "github_org" {
  description = "GitHub organization or username (e.g., 'your-username')"
  type        = string
  default     = "AkiraNagasawa365"
}

variable "github_repo" {
  description = "GitHub repository name (e.g., 'jigsaw-puzzle')"
  type        = string
  default     = "jigsaw-puzzle"
}
