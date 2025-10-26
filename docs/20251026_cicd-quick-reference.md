# CI/CD クイックリファレンス

## 📊 1枚で分かるCI/CD構成

```
┌─────────────────────────────────────────────────────────────────┐
│                         開発フロー                               │
└─────────────────────────────────────────────────────────────────┘

  コード変更
      ↓
  git push
      ↓
┌──────────────────────────────────────────────────────┐
│           GitHub Actions (OIDC認証でAWSへ)            │
├──────────────────────────────────────────────────────┤
│ ① CI                  │ テスト・Lint                │
│ ② Lambda Deploy       │ バックエンドデプロイ        │
│ ③ Frontend Deploy     │ フロントエンドデプロイ      │
│ ④ Terraform Apply     │ インフラ更新                │
└──────────────────────────────────────────────────────┘
      ↓
┌──────────────────────────────────────────────────────┐
│                    AWS環境                            │
├──────────────────────────────────────────────────────┤
│ ・Lambda (バックエンド)                               │
│ ・S3 + CloudFront (フロントエンド)                    │
│ ・DynamoDB, API Gateway, Cognito                      │
└──────────────────────────────────────────────────────┘
```

---

## 🗂️ ファイルの場所早見表

### 認証（GitHub → AWS）

| 何を | どこに |
|------|--------|
| OIDCプロバイダー | `terraform/modules/github-oidc/main.tf` |
| ロールARN | GitHub Secrets (`AWS_ROLE_ARN`) |

### Terraform状態管理

| 何を | どこに |
|------|--------|
| S3バケット作成 | `terraform/bootstrap/main.tf` |
| S3を使う設定 | `terraform/environments/*/backend.tf` |
| 実際の状態ファイル | S3: `s3://jigsaw-puzzle-terraform-state/*/terraform.tfstate` |

### ワークフロー

| 何を | どこに | いつ |
|------|--------|------|
| テスト | `.github/workflows/ci.yml` | 全push |
| Lambdaデプロイ | `.github/workflows/deploy-lambda.yml` | `backend/` 変更 |
| フロントエンドデプロイ | `.github/workflows/deploy-frontend.yml` | `frontend/` 変更 |
| Terraformプレビュー | `.github/workflows/terraform-plan.yml` | PR作成 |
| Terraformデプロイ | `.github/workflows/terraform-apply.yml` | `terraform/` 変更 |

---

## ⚡ よくある操作

### ローカルでTerraform実行

```bash
# prod環境
cd terraform/environments/prod
terraform plan   # 確認
terraform apply  # 適用

# dev環境
cd terraform/environments/dev
terraform plan
terraform apply
```

### GitHub Actionsを手動実行

```bash
# Terraform Applyを手動実行（prod環境）
gh workflow run "Terraform Apply" -f environment=prod

# Lambda Deployを手動実行
gh workflow run "Deploy Lambda" -f environment=prod
```

### 状態ファイル確認

```bash
# S3の状態ファイル一覧
aws s3 ls s3://jigsaw-puzzle-terraform-state/ --recursive

# 特定の状態ファイル取得
aws s3 cp s3://jigsaw-puzzle-terraform-state/prod/terraform.tfstate .
```

---

## 🔍 トラブル時のチェックリスト

### ✅ 基本確認

- [ ] GitHub Secrets に `AWS_ROLE_ARN` 設定済み（prod/dev両方）
- [ ] Bootstrap実行済み（`terraform/bootstrap/`）
- [ ] S3バケット存在確認（`aws s3 ls | grep terraform-state`）
- [ ] ローカルでterraform initできるか

### ❌ エラーパターン

| エラー | 原因 | 解決 |
|--------|------|------|
| OIDC認証エラー | Secretsが未設定 | GitHub Secretsを確認 |
| 状態ファイルが見つからない | Bootstrapが未実行 | `terraform/bootstrap/` を実行 |
| リソースが既に存在 | 状態ファイル不一致 | `terraform import` で状態を同期 |

---

## 🎯 覚えておくべき3つのポイント

1. **Bootstrap → 環境**
   - 最初に `terraform/bootstrap/` を実行（1回だけ）
   - その後 `terraform/environments/*/` を使用

2. **ブランチ = 環境**
   - `develop` ブランチ → dev環境
   - `main` ブランチ → prod環境

3. **push = 自動デプロイ**
   - コード変更 → 該当するワークフローが自動実行
   - PRでプレビュー → マージで自動反映

---

## 📞 もっと詳しく知りたい

- 全体構成: [cicd-architecture.md](./cicd-architecture.md)
- プロジェクト概要: [CLAUDE.md](../CLAUDE.md)
- システム設計: [system-design.md](./system-design.md)
