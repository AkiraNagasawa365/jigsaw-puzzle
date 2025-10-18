# ============================================
# Frontend Module - S3 + CloudFront
# ============================================
# フロントエンド（React）のホスティング環境
# S3でファイルを保存し、CloudFrontでグローバルに配信

# ============================================
# S3 Bucket for Frontend
# ============================================
# ビルド済みのフロントエンドファイル（HTML, JS, CSS）を保存
resource "aws_s3_bucket" "frontend" {
  bucket = "${var.project_name}-${var.environment}-frontend"

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-frontend"
    }
  )
}

# パブリックアクセスをブロック
# CloudFront経由でのみアクセス可能にするため
resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3バケットのウェブサイト設定
# SPAのルーティングサポート
resource "aws_s3_bucket_website_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

# ============================================
# CloudFront Origin Access Control (OAC)
# ============================================
# CloudFrontからS3への安全なアクセス制御
# 古いOAI（Origin Access Identity）より推奨される新方式
resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${var.project_name}-${var.environment}-frontend-oac"
  description                       = "OAC for ${var.project_name}-${var.environment}-frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# ============================================
# CloudFront Distribution
# ============================================
# CDN（Content Delivery Network）でグローバル配信
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name}-${var.environment}-frontend"
  default_root_object = "index.html"
  price_class         = "PriceClass_200" # 北米、ヨーロッパ、アジア

  # S3をオリジンとして設定
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.frontend.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  # デフォルトキャッシュ動作
  default_cache_behavior {
    target_origin_id       = "S3-${aws_s3_bucket.frontend.id}"
    viewer_protocol_policy = "redirect-to-https" # HTTPをHTTPSにリダイレクト

    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods  = ["GET", "HEAD"]

    compress = true # 自動圧縮（gzip、brotli）

    # キャッシュポリシー
    cache_policy_id = aws_cloudfront_cache_policy.frontend.id

    # オリジンリクエストポリシー
    origin_request_policy_id = aws_cloudfront_origin_request_policy.frontend.id
  }

  # SPA（Single Page Application）サポート
  # 存在しないパス（/puzzles/123など）にアクセスした場合、
  # 404の代わりに index.html を返してReact Routerに処理を任せる
  custom_error_response {
    error_code            = 404
    error_caching_min_ttl = 0
    response_code         = 200
    response_page_path    = "/index.html"
  }

  custom_error_response {
    error_code            = 403
    error_caching_min_ttl = 0
    response_code         = 200
    response_page_path    = "/index.html"
  }

  # 地理的制限（今回は制限なし）
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL/TLS証明書
  # CloudFrontのデフォルト証明書を使用（*.cloudfront.netドメイン）
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-frontend"
    }
  )
}

# ============================================
# CloudFront Cache Policy
# ============================================
# キャッシュの動作を定義
resource "aws_cloudfront_cache_policy" "frontend" {
  name        = "${var.project_name}-${var.environment}-frontend-cache"
  comment     = "Cache policy for frontend"
  default_ttl = 86400  # 1日（デフォルト）
  max_ttl     = 31536000 # 1年（最大）
  min_ttl     = 0      # キャッシュしないことも可能

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "none"
    }

    enable_accept_encoding_gzip   = true
    enable_accept_encoding_brotli = true
  }
}

# ============================================
# CloudFront Origin Request Policy
# ============================================
# オリジン（S3）へのリクエスト設定
resource "aws_cloudfront_origin_request_policy" "frontend" {
  name    = "${var.project_name}-${var.environment}-frontend-origin-request"
  comment = "Origin request policy for frontend"

  cookies_config {
    cookie_behavior = "none"
  }

  headers_config {
    header_behavior = "none"
  }

  query_strings_config {
    query_string_behavior = "none"
  }
}

# ============================================
# S3 Bucket Policy
# ============================================
# CloudFrontからのアクセスのみ許可
resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}
