# Terraform Backend設定
# S3に状態ファイルを保存し、DynamoDBで状態ロック

terraform {
  backend "s3" {
    bucket         = "jigsaw-puzzle-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "ap-northeast-1"
    dynamodb_table = "jigsaw-puzzle-terraform-locks"
    encrypt        = true
  }
}
