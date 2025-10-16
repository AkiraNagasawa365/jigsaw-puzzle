terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# S3 Module
module "s3" {
  source = "../../modules/s3"

  project_name    = var.project_name
  environment     = var.environment
  common_tags     = local.common_tags
  allowed_origins = var.allowed_origins
}

# DynamoDB Module
module "dynamodb" {
  source = "../../modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment
  common_tags  = local.common_tags
}

# IAM Module
module "iam" {
  source = "../../modules/iam"

  project_name      = var.project_name
  environment       = var.environment
  common_tags       = local.common_tags
  s3_bucket_arn     = module.s3.bucket_arn
  puzzles_table_arn = module.dynamodb.puzzles_table_arn
  pieces_table_arn  = module.dynamodb.pieces_table_arn
}

# ============================================
# Lambda Module
# ============================================
# Lambda関数を作成します
# 注意: 最初のapply時はzipファイルが必要です
# 作成方法: cd lambda/puzzle-register && zip -r function.zip index.py
module "lambda" {
  source = "../../modules/lambda"

  project_name              = var.project_name
  environment               = var.environment
  common_tags               = local.common_tags
  lambda_execution_role_arn = module.iam.lambda_execution_role_arn
  s3_bucket_name            = module.s3.bucket_name
  puzzles_table_name        = module.dynamodb.puzzles_table_name
  pieces_table_name         = module.dynamodb.pieces_table_name

  # Lambda関数のzipファイルパス
  # 最初は空のzipでも可（後でdeploy-lambda.shで更新）
  puzzle_register_zip_path = "${path.module}/../../../lambda/puzzle-register/function.zip"
}

# ============================================
# API Gateway Module
# ============================================
# HTTP エンドポイントを提供します
# POST /puzzles でパズル登録が可能
module "api_gateway" {
  source = "../../modules/api-gateway"

  project_name    = var.project_name
  environment     = var.environment
  common_tags     = local.common_tags
  log_retention_days = 7

  # Lambda統合
  puzzle_register_lambda_function_name = module.lambda.puzzle_register_function_name
  puzzle_register_lambda_invoke_arn    = module.lambda.puzzle_register_invoke_arn

  # スロットリング設定（必要に応じて調整）
  throttling_burst_limit = 5000
  throttling_rate_limit  = 10000
}
