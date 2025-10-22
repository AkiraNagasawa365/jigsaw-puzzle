# GitHub OIDC認証の自動化セットアップ

**日付**: 2025-10-22
**目的**: GitHub SecretsなしでAWSへの自動デプロイを実現

---

## 🎯 概要

従来の方法では`AWS_ACCESS_KEY_ID`と`AWS_SECRET_ACCESS_KEY`を手動でGitHub Secretsに設定する必要がありましたが、**OpenID Connect (OIDC)** を使うことで：

✅ **GitHub Secretsへの手動設定が不要**
✅ **一時的な認証情報で安全**
✅ **Terraformで完全自動化**
✅ **アクセスキーのローテーション不要**

---

## 📋 セットアップ手順

### Step 1: GitHubユーザー名の設定

`terraform/environments/dev/variables.tf` を編集:

```hcl
variable "github_org" {
  description = "GitHub organization or username"
  type        = string
  default     = "YOUR_GITHUB_USERNAME"  # ← あなたのGitHubユーザー名に置き換え
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "jigsaw-puzzle"  # リポジトリ名が異なる場合は変更
}
```

**例**:
- あなたのGitHubユーザー名が `akira-nagasawa` の場合
- リポジトリが `https://github.com/akira-nagasawa/jigsaw-puzzle` の場合

```hcl
variable "github_org" {
  default = "akira-nagasawa"
}

variable "github_repo" {
  default = "jigsaw-puzzle"
}
```

---

### Step 2: Terraformでインフラ構築

```bash
cd terraform/environments/dev

# 初期化（初回のみ）
terraform init

# 変更内容を確認
terraform plan

# 適用
terraform apply
```

**作成されるリソース**:
- ✅ GitHub OIDC Provider
- ✅ IAM Role (GitHub Actionsがassumeする)
- ✅ IAM Policies (Lambda、S3、CloudFrontへの権限)

**実行後の出力例**:
```
Outputs:

github_actions_role_arn = "arn:aws:iam::123456789012:role/jigsaw-puzzle-dev-github-actions-role"
github_oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
```

---

### Step 3: GitHub SecretsにロールARNを設定

**必要なSecret: 1つだけ！**

1. GitHubリポジトリページを開く
2. **Settings** → **Secrets and variables** → **Actions**
3. **New repository secret** をクリック
4. 以下を追加:

| Name | Value |
|------|-------|
| `AWS_ROLE_ARN` | `terraform apply`で出力された`github_actions_role_arn`の値 |

**例**:
```
Name:  AWS_ROLE_ARN
Value: arn:aws:iam::123456789012:role/jigsaw-puzzle-dev-github-actions-role
```

---

### Step 4: 動作確認

#### 方法1: mainブランチにプッシュ
```bash
git add .
git commit -m "Add OIDC authentication"
git push origin main
```

#### 方法2: GitHub Actionsから手動実行
1. GitHub → **Actions** タブ
2. **Deploy Lambda** または **Deploy Frontend** を選択
3. **Run workflow** をクリック

---

## 🔧 仕組み

### 従来の方法（Access Key）
```
GitHub Actions
  ↓ (AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY)
AWS API
  ↓
リソースにアクセス
```

**問題点**:
- ⚠️ 長期的な認証情報がGitHub Secretsに保存される
- ⚠️ 漏洩リスクが高い
- ⚠️ 定期的なローテーションが必要

---

### 新しい方法（OIDC）
```
GitHub Actions
  ↓ (1) OIDCトークンをリクエスト
GitHub OIDC Provider
  ↓ (2) トークン発行（有効期限: 1時間）
AWS STS (Security Token Service)
  ↓ (3) トークンを検証
  ↓ (4) 一時的な認証情報を発行
AWS API
  ↓ (5) リソースにアクセス
```

**利点**:
- ✅ 一時的な認証情報（1時間で自動失効）
- ✅ リポジトリ・ブランチごとに制限可能
- ✅ 長期的なキーをGitHubに保存しない

---

## 🔒 セキュリティ設定

### 1. リポジトリ・ブランチの制限

`terraform/modules/github-oidc/main.tf` でリポジトリとブランチを制限:

```hcl
condition {
  test     = "StringLike"
  variable = "token.actions.githubusercontent.com:sub"
  values = [
    "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/main",
    "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/develop"
  ]
}
```

**意味**:
- ✅ 指定したリポジトリからのみアクセス可能
- ✅ `main`と`develop`ブランチのみアクセス可能
- ❌ 他のリポジトリ・ブランチは拒否

---

### 2. 最小権限の原則

各ワークフローに必要な権限のみを付与:

| ワークフロー | 必要な権限 |
|-------------|-----------|
| Deploy Lambda | Lambda更新権限のみ |
| Deploy Frontend | S3書き込み + CloudFront無効化のみ |
| CI (テスト) | **AWS権限不要** |

---

### 3. 一時的な認証情報

OIDCで発行される認証情報は**1時間で自動失効**します。

---

## 📊 比較表

| 項目 | Access Key | **OIDC** |
|------|-----------|---------|
| GitHub Secrets設定 | 2つ必要 | **1つのみ** |
| 認証情報の種類 | 長期的 | **一時的** |
| 有効期限 | 無制限 | **1時間** |
| ローテーション | 手動 | **自動** |
| リポジトリ制限 | 不可 | **可能** |
| ブランチ制限 | 不可 | **可能** |
| セキュリティリスク | 高 | **低** |
| セットアップの自動化 | 不可 | **Terraformで可能** |

---

## 🚀 ワークフローの変更点

### 従来
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: ap-northeast-1
```

### OIDC使用
```yaml
# OIDCトークンの取得を許可
permissions:
  id-token: write   # 必須
  contents: read

jobs:
  deploy:
    steps:
      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ap-northeast-1
```

---

## ⚠️ トラブルシューティング

### エラー: "Not authorized to perform sts:AssumeRoleWithWebIdentity"

**原因**: リポジトリ名またはブランチ名が一致していない

**解決方法**:
1. `terraform/environments/dev/variables.tf` のリポジトリ名を確認
2. 現在のブランチ名を確認 (`git branch`)
3. `main` または `develop` ブランチで実行していることを確認

---

### エラー: "No OpenIDConnect provider found"

**原因**: Terraformが適用されていない

**解決方法**:
```bash
cd terraform/environments/dev
terraform apply
```

---

### エラー: "Access Denied" (Lambda/S3/CloudFront)

**原因**: IAMロールに権限が不足している

**解決方法**:
1. `terraform/modules/github-oidc/main.tf` のIAMポリシーを確認
2. 必要な権限を追加してterraform apply

---

## 📝 まとめ

### ✅ 達成したこと
- GitHub Secretsへの手動設定が**2つ → 1つ**に削減
- 長期的なアクセスキーを**完全に廃止**
- セキュリティリスクを**大幅に低減**
- インフラ構築を**完全自動化**

### 🎯 次のステップ
1. `variables.tf` でGitHubユーザー名を設定
2. `terraform apply` でOIDC Providerを作成
3. `AWS_ROLE_ARN` をGitHub Secretsに設定（1つだけ）
4. `git push` で自動デプロイを確認

---

## 参考リンク

- [GitHub Actions: OpenID Connect](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [AWS IAM: OIDC Identity Providers](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)
- [Terraform: aws_iam_openid_connect_provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_openid_connect_provider)
