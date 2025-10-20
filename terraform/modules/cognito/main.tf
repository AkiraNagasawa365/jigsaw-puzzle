# Cognito User Pool for user authentication
# ユーザー認証のためのCognito User Pool

resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-${var.environment}-user-pool"

  # ユーザー名の設定（メールアドレスでログイン）
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # パスワードポリシー
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # アカウント回復設定
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # メール設定
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # ユーザー属性のスキーマ
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = false

    string_attribute_constraints {
      min_length = 5
      max_length = 255
    }
  }

  # MFA設定（オプショナル）
  mfa_configuration = "OFF"

  # ユーザープールの削除保護（本番環境では ACTIVE にする）
  deletion_protection = var.environment == "prod" ? "ACTIVE" : "INACTIVE"

  tags = {
    Name        = "${var.project_name}-${var.environment}-user-pool"
    Environment = var.environment
  }
}

# User Pool Client (フロントエンド用)
resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.project_name}-${var.environment}-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # 認証フロー
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # トークンの有効期限
  refresh_token_validity = 30 # 30日
  access_token_validity  = 60 # 60分
  id_token_validity      = 60 # 60分

  token_validity_units {
    refresh_token = "days"
    access_token  = "minutes"
    id_token      = "minutes"
  }

  # OAuth設定（将来的にソーシャルログインを追加する場合に備えて）
  allowed_oauth_flows_user_pool_client = false
  generate_secret                      = false

  # セキュリティ設定
  prevent_user_existence_errors = "ENABLED"

  # コールバックURL（フロントエンドのURL）
  # 環境に応じて変更
  read_attributes  = ["email"]
  write_attributes = ["email"]
}

# User Pool Domain（サインアップ・サインインのホストUI用、オプション）
# カスタムUIを使う場合は不要だが、テスト用に作成しておく
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-${var.environment}-auth"
  user_pool_id = aws_cognito_user_pool.main.id
}
