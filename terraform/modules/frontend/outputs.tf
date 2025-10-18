# ============================================
# Frontend Module - Outputs
# ============================================

# CloudFrontのドメイン名
# 例: d1a2b3c4d5e6f7.cloudfront.net
# 用途: フロントエンドにアクセスするURL、CORS設定
output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.frontend.domain_name
}

# CloudFront Distribution ID
# 例: E1A2B3C4D5E6F7
# 用途: キャッシュ無効化（デプロイスクリプト）
output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for cache invalidation"
  value       = aws_cloudfront_distribution.frontend.id
}

# S3バケット名
# 例: jigsaw-puzzle-dev-frontend
# 用途: デプロイスクリプトでのアップロード先
output "s3_bucket_name" {
  description = "S3 bucket name for frontend files"
  value       = aws_s3_bucket.frontend.id
}

# S3バケットARN
# 用途: IAMポリシーなどで使用
output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.frontend.arn
}

# CloudFront Distribution ARN
# 用途: 監視、アラート設定などで使用
output "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.frontend.arn
}
