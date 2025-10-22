# GitHub Actions OIDC Provider for AWS
# これによりGitHub SecretsなしでAWSにアクセス可能

# GitHub OIDCプロバイダーの作成
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  # GitHubのサムプリント（公式値）
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = {
    Name        = "${var.project_name}-${var.environment}-github-oidc"
    Environment = var.environment
  }
}

# GitHub ActionsがAssumeできるIAMロール
resource "aws_iam_role" "github_actions" {
  name               = "${var.project_name}-${var.environment}-github-actions-role"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_role.json

  tags = {
    Name        = "${var.project_name}-${var.environment}-github-actions-role"
    Environment = var.environment
  }
}

# GitHub Actionsがこのロールを引き受けるための信頼ポリシー
data "aws_iam_policy_document" "github_actions_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      # リポジトリとブランチを制限
      values = [
        "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main",
        "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/develop"
      ]
    }
  }
}

# Lambda更新権限
resource "aws_iam_role_policy" "lambda_deploy" {
  name   = "lambda-deploy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.lambda_deploy.json
}

data "aws_iam_policy_document" "lambda_deploy" {
  statement {
    effect = "Allow"
    actions = [
      "lambda:UpdateFunctionCode",
      "lambda:GetFunction",
      "lambda:GetFunctionConfiguration"
    ]
    resources = [
      "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${var.project_name}-${var.environment}-*"
    ]
  }
}

# S3デプロイ権限
resource "aws_iam_role_policy" "s3_deploy" {
  name   = "s3-deploy"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.s3_deploy.json
}

data "aws_iam_policy_document" "s3_deploy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = [
      "arn:aws:s3:::${var.project_name}-${var.environment}-frontend",
      "arn:aws:s3:::${var.project_name}-${var.environment}-frontend/*"
    ]
  }
}

# CloudFront無効化権限
resource "aws_iam_role_policy" "cloudfront_invalidate" {
  name   = "cloudfront-invalidate"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.cloudfront_invalidate.json
}

data "aws_iam_policy_document" "cloudfront_invalidate" {
  statement {
    effect = "Allow"
    actions = [
      "cloudfront:CreateInvalidation",
      "cloudfront:GetInvalidation",
      "cloudfront:ListDistributions"
    ]
    resources = ["*"]
  }
}

# PowerUserAccess（ほぼ全てのAWSサービスを管理可能、IAM管理は不可）
# Terraformでインフラを管理するのに十分な権限
resource "aws_iam_role_policy_attachment" "power_user" {
  role       = aws_iam_role.github_actions.id
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

# 追加で必要なIAM権限（Terraformが管理するリソースのみに限定）
resource "aws_iam_role_policy" "iam_limited" {
  name   = "iam-limited"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.iam_limited.json
}

data "aws_iam_policy_document" "iam_limited" {
  # プロジェクト固有のロールのみ管理可能
  statement {
    effect = "Allow"
    actions = [
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:UpdateRole",
      "iam:PutRolePolicy",
      "iam:DeleteRolePolicy",
      "iam:GetRolePolicy",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListRolePolicies",
      "iam:PassRole",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:ListInstanceProfilesForRole"
    ]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project_name}-*"
    ]
  }

  # OIDC Provider管理（GitHub Actions認証用）
  statement {
    effect = "Allow"
    actions = [
      "iam:CreateOpenIDConnectProvider",
      "iam:DeleteOpenIDConnectProvider",
      "iam:GetOpenIDConnectProvider",
      "iam:UpdateOpenIDConnectProviderThumbprint",
      "iam:TagOpenIDConnectProvider",
      "iam:UntagOpenIDConnectProvider",
      "iam:ListOpenIDConnectProviders"
    ]
    resources = [
      "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/token.actions.githubusercontent.com"
    ]
  }
}

# 現在のAWSアカウントID取得
data "aws_caller_identity" "current" {}
