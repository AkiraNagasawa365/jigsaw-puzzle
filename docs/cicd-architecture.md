# CI/CD パイプライン構成図

このプロジェクトのCI/CDがどこに何を書いているから成り立っているかを説明します。

## 🎯 全体像

```
GitHub Push
    ↓
GitHub Actions (OIDC認証)
    ↓
AWS (Lambda/S3/Terraform)
```

---

## 📁 ファイル構成と役割

### 1. 認証基盤（GitHub → AWS）

| ファイル | 役割 |
|---------|------|
| `terraform/modules/github-oidc/main.tf` | GitHub OIDC Provider + IAMロール定義 |
| GitHub Secrets: `AWS_ROLE_ARN` | ロールARNを保存（環境ごと） |

**これがあるから:** GitHub ActionsがAWSにアクセスできる（長期クレデンシャル不要）

---

### 2. Terraform 状態管理

| ファイル | 役割 |
|---------|------|
| `terraform/bootstrap/main.tf` | S3バケット + DynamoDBテーブル作成 |
| `terraform/environments/*/backend.tf` | S3を状態保存先に指定 |

**これがあるから:** ローカルとGitHub Actionsで同じ状態ファイルを共有できる

**S3の中身:**
```
s3://jigsaw-puzzle-terraform-state/
  ├── dev/terraform.tfstate    ← dev環境の状態
  └── prod/terraform.tfstate   ← prod環境の状態
```

---

### 3. GitHub Actions ワークフロー

#### 📋 CI（テスト）

| ファイル | トリガー | 内容 |
|---------|---------|------|
| `.github/workflows/ci.yml` | 全pushで実行 | バックエンド/フロントエンドのテスト・Lint |

**これがあるから:** コード品質を自動チェック

---

#### 🚀 Lambda Deploy（バックエンド自動デプロイ）

| ファイル | トリガー | 内容 |
|---------|---------|------|
| `.github/workflows/deploy-lambda.yml` | `backend/app/`, `lambda/` 変更時 | Lambda関数コード更新 |
| `scripts/deploy-lambda.sh` | ↑から呼ばれる | zipパッケージ作成 → AWS Lambda更新 |

**ブランチ分岐:**
- `main` ブランチ → prod環境にデプロイ
- `develop` ブランチ → dev環境にデプロイ

**これがあるから:** バックエンドコードのpushで自動デプロイ

---

#### 🎨 Frontend Deploy（フロントエンド自動デプロイ）

| ファイル | トリガー | 内容 |
|---------|---------|------|
| `.github/workflows/deploy-frontend.yml` | `frontend/` 変更時 | React ビルド → S3アップロード → CloudFront無効化 |
| `scripts/deploy-frontend.sh` | ↑から呼ばれる | npm build → S3 sync → CloudFront invalidation |

**ブランチ分岐:**
- `main` ブランチ → prod環境（CloudFront）
- `develop` ブランチ → dev環境（CloudFront）

**これがあるから:** フロントエンドコードのpushで自動デプロイ

---

#### 🏗️ Terraform Plan（インフラ変更プレビュー）

| ファイル | トリガー | 内容 |
|---------|---------|------|
| `.github/workflows/terraform-plan.yml` | PR作成時、`terraform/` 変更時 | terraform plan → PRにコメント投稿 |

**これがあるから:** インフラ変更をレビューできる

---

#### 🏗️ Terraform Apply（インフラ自動更新）

| ファイル | トリガー | 内容 |
|---------|---------|------|
| `.github/workflows/terraform-apply.yml` | `terraform/` 変更時 | terraform apply → インフラ更新 |

**ブランチ分岐:**
- `main` ブランチ → prod環境を更新
- `develop` ブランチ → dev環境を更新

**これがあるから:** インフラ変更が自動反映される

---

## 🔄 動作フロー

### パターン1: バックエンドコード変更

```
1. backend/app/puzzle_service.py を編集
   ↓
2. git push origin main
   ↓
3. GitHub Actions発動
   - CI: テスト実行 ✓
   - deploy-lambda.yml: Lambda更新 ✓
   ↓
4. 完了（約2分）
```

---

### パターン2: フロントエンドコード変更

```
1. frontend/src/App.tsx を編集
   ↓
2. git push origin main
   ↓
3. GitHub Actions発動
   - CI: Lint実行 ✓
   - deploy-frontend.yml: S3+CloudFront更新 ✓
   ↓
4. 完了（約3分）
```

---

### パターン3: インフラ変更

```
1. terraform/environments/prod/main.tf を編集
   ↓
2. PR作成
   ↓
3. terraform-plan.yml: プレビュー → PRにコメント
   ↓
4. レビュー後、マージ
   ↓
5. terraform-apply.yml: 自動適用
   ↓
6. 完了
```

---

## 🔐 認証の仕組み

### GitHub Actions → AWS

```
┌─────────────────────────────────────┐
│ 1. GitHub Actions起動               │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 2. GitHub が OIDC トークン発行      │
│    "このリポジトリのmainブランチ"   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 3. AWS STS が検証                   │
│    terraform/modules/github-oidc/   │
│    のTrust Policyで確認             │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 4. 一時クレデンシャル発行           │
│    (15分〜1時間有効)                 │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│ 5. AWS操作可能                      │
│    ・Lambda更新                     │
│    ・S3アップロード                 │
│    ・Terraform実行                  │
└─────────────────────────────────────┘
```

**キーファイル:**
- `terraform/modules/github-oidc/main.tf` (Trust Policy定義)
- GitHub Secrets: `AWS_ROLE_ARN` (ロール指定)

---

## 🌍 環境分離

### ブランチ戦略

| ブランチ | 環境 | URL |
|---------|------|-----|
| `develop` | dev | https://dykwhpbm0bhdv.cloudfront.net |
| `main` | prod | https://d1tucwzc87xq8x.cloudfront.net |

### 環境ごとの設定

```
terraform/environments/
  ├── dev/
  │   ├── backend.tf         ← S3キー: dev/terraform.tfstate
  │   ├── main.tf            ← dev固有の設定
  │   └── variables.tf       ← デフォルト値: dev
  │
  └── prod/
      ├── backend.tf         ← S3キー: prod/terraform.tfstate
      ├── main.tf            ← prod固有の設定
      └── variables.tf       ← デフォルト値: prod
```

**これがあるから:** dev/prodが完全に分離される

---

## 📦 重要な依存関係

### Bootstrap → 環境

```
terraform/bootstrap/  (最初に1回だけ実行)
  ↓ S3バケット作成
terraform/environments/dev/
terraform/environments/prod/
  ↓ S3を参照
```

**順序が重要:** Bootstrapを先に実行しないと環境が動かない

---

## 🎯 まとめ：どこに何があるか

| 機能 | ファイル | 一言 |
|------|---------|------|
| **認証** | `terraform/modules/github-oidc/` | GitHubからAWSにログイン |
| **状態管理** | `terraform/bootstrap/` + `*/backend.tf` | Terraform状態をS3で共有 |
| **CI** | `.github/workflows/ci.yml` | テスト自動実行 |
| **Lambda** | `.github/workflows/deploy-lambda.yml` | バックエンド自動デプロイ |
| **Frontend** | `.github/workflows/deploy-frontend.yml` | フロントエンド自動デプロイ |
| **Terraform** | `.github/workflows/terraform-*.yml` | インフラ自動更新 |

**これらすべてが揃って、完全なCI/CDパイプラインが完成。**

---

## 🔧 トラブルシューティング

### GitHub Actionsが失敗する

1. **OIDC認証エラー**
   - 確認: GitHub Secrets に `AWS_ROLE_ARN` が設定されているか
   - 確認: `terraform/modules/github-oidc/main.tf` のTrust Policy

2. **Terraform状態エラー**
   - 確認: `terraform/bootstrap/` が実行済みか
   - 確認: S3バケット `jigsaw-puzzle-terraform-state` が存在するか

3. **デプロイエラー**
   - 確認: Lambda関数が存在するか（Terraformで作成済み？）
   - 確認: IAMロールに必要な権限があるか

---

## 📚 関連ドキュメント

- [CLAUDE.md](../CLAUDE.md) - プロジェクト全体の構成
- [system-design.md](./system-design.md) - システム設計
- [20251022_github-oidc-setup.md](./20251022_github-oidc-setup.md) - OIDC設定手順

以上、簡潔版CI/CD構成ドキュメントでした！
