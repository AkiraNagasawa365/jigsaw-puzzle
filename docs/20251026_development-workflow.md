# 開発ワークフロー

このプロジェクトで開発を行う際の手順を説明します。

## 🚀 初回セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/AkiraNagasawa365/jigsaw-puzzle.git
cd jigsaw-puzzle
```

### 2. バックエンド環境構築

```bash
# uvのインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係インストール
uv sync

# 環境変数設定
cd backend
cp .env.example .env  # 存在する場合

# または、Terraform outputから取得
cd ../terraform/environments/dev
terraform output
# ↑の値を backend/.env に設定
```

**backend/.env の例:**
```env
AWS_REGION=ap-northeast-1
S3_BUCKET_NAME=jigsaw-puzzle-dev-images
PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces
ENVIRONMENT=dev
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. フロントエンド環境構築

```bash
cd frontend

# 依存関係インストール
npm install

# 環境変数設定
# .env.local を作成（gitignoreされている）
cat > .env.local <<EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_COGNITO_USER_POOL_ID=ap-northeast-1_xxxxx
VITE_COGNITO_CLIENT_ID=xxxxx
VITE_AWS_REGION=ap-northeast-1
EOF
```

**Cognito情報の取得:**
```bash
cd terraform/environments/dev
terraform output cognito_user_pool_id
terraform output cognito_client_id
```

---

## 📝 日常的な開発フロー

### パターンA: バックエンド開発

```bash
# 1. ブランチ作成
git checkout develop
git pull
git checkout -b feature/add-puzzle-search

# 2. バックエンド起動
cd backend
uv run uvicorn app.api.main:app --reload
# → http://localhost:8000/docs でSwagger確認

# 3. コード編集
vim app/services/puzzle_service.py

# 4. テスト実行
uv run pytest tests/unit/ -v

# 5. 型チェック
uv run mypy app/

# 6. コミット
git add .
git commit -m "feat: Add puzzle search functionality"

# 7. Push & PR作成
git push origin feature/add-puzzle-search
gh pr create --base develop --title "Add puzzle search"
```

### パターンB: フロントエンド開発

```bash
# 1. ブランチ作成
git checkout develop
git pull
git checkout -b feature/improve-ui

# 2. フロントエンド起動
cd frontend
npm run dev
# → http://localhost:5173

# 3. コード編集
vim src/pages/Home.tsx

# 4. 型チェック
npm run build  # tscも実行される

# 5. Lint
npm run lint

# 6. コミット & Push
git add .
git commit -m "feat: Improve home page UI"
git push origin feature/improve-ui
gh pr create --base develop
```

### パターンC: インフラ変更

```bash
# 1. ブランチ作成
git checkout develop
git pull
git checkout -b infra/increase-lambda-memory

# 2. Terraformコード編集
cd terraform/environments/dev
vim main.tf

# 3. ローカルでプレビュー
terraform plan

# 4. 問題なければコミット
git add .
git commit -m "infra: Increase Lambda memory to 1024MB"

# 5. Push & PR作成
git push origin infra/increase-lambda-memory
gh pr create --base develop

# 6. GitHub ActionsでTerraform Planが自動実行される
# 7. PRにコメントで結果が表示される
# 8. レビュー後、マージするとterraform applyが自動実行
```

---

## 🌿 ブランチ戦略

```
main (本番環境)
  ↑ マージ
develop (開発環境)
  ↑ マージ
feature/* (機能開発)
fix/* (バグ修正)
infra/* (インフラ変更)
```

### ルール

1. **直接pushしない**
   - `main`, `develop` に直接pushしない
   - 必ずfeatureブランチからPR

2. **developで動作確認**
   - まずdevelopにマージ
   - dev環境で動作確認
   - 問題なければmainにPR

3. **PRでレビュー**
   - CI（テスト・Lint）が通ること
   - Terraform Planを確認（インフラ変更の場合）
   - 最低1人のLGTM

---

## 🧪 テストの実行

### バックエンド

```bash
cd backend

# 全テスト実行
uv run pytest

# 単体テストのみ
uv run pytest tests/unit/ -v

# 統合テストのみ
uv run pytest tests/integration/ -v

# カバレッジレポート付き
uv run pytest --cov=app --cov-report=html
# → htmlcov/index.html を開く

# 特定のテストファイル
uv run pytest tests/unit/test_puzzle_service.py -v

# 型チェック
uv run mypy app/
```

### フロントエンド

```bash
cd frontend

# テスト実行（ウォッチモード）
npm run test

# カバレッジレポート
npm run test:coverage

# Vitest UI
npm run test:ui

# Lint
npm run lint

# 型チェック
npm run build  # tsc -b も実行
```

---

## 🚢 デプロイフロー

### Dev環境へのデプロイ

```bash
# 1. developブランチにマージ
git checkout develop
git merge feature/your-feature
git push origin develop

# 2. GitHub Actionsが自動実行
# - CI（テスト）
# - Deploy Lambda（backendの変更がある場合）
# - Deploy Frontend（frontendの変更がある場合）
# - Terraform Apply（terraformの変更がある場合）

# 3. 完了後、dev環境で確認
# https://dykwhpbm0bhdv.cloudfront.net
```

### Prod環境へのデプロイ

```bash
# 1. developで十分にテスト

# 2. mainへのPR作成
git checkout main
git pull
gh pr create --base main --head develop --title "Release: v1.2.0"

# 3. PRでTerraform Planを確認（インフラ変更がある場合）

# 4. レビュー & マージ

# 5. GitHub Actionsが自動実行（prod環境へ）

# 6. 本番環境で確認
# https://d1tucwzc87xq8x.cloudfront.net
```

---

## 🔧 よくある開発タスク

### 新しいAPIエンドポイントを追加

```bash
# 1. バックエンドコード
backend/app/api/routes/puzzles.py  # ルート追加
backend/app/services/puzzle_service.py  # ロジック追加
backend/app/core/schemas.py  # スキーマ追加

# 2. テスト
backend/tests/unit/test_puzzle_service.py  # 単体テスト
backend/tests/integration/test_api.py  # APIテスト

# 3. フロントエンド
frontend/src/api/puzzle.ts  # API呼び出し関数
frontend/src/pages/PuzzleList.tsx  # UI更新
```

### 環境変数を追加

```bash
# 1. Terraformで定義
terraform/environments/dev/backend-config.tf
# locals.backend_env_parameter_value に追加

# 2. Terraform適用
cd terraform/environments/dev
terraform apply

# 3. ローカル開発用
backend/.env に追加

# 4. Lambdaデプロイ
# GitHub Actionsが自動的に環境変数を設定
```

### DynamoDBテーブル構造変更

```bash
# 1. Terraformで定義
terraform/modules/dynamodb/main.tf

# 2. マイグレーション計画
# DynamoDBは破壊的変更に注意！
# 必要に応じてデータバックアップ

# 3. Terraform適用
cd terraform/environments/dev
terraform plan  # 必ず確認！
terraform apply

# 4. アプリケーションコード更新
backend/app/services/puzzle_service.py
```

---

## 🐛 トラブルシューティング

### ローカル開発でエラー

#### バックエンドが起動しない

```bash
# 依存関係を再インストール
uv sync

# 仮想環境を確認
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows

# ポートが使用中
lsof -ti:8000 | xargs kill -9  # macOS/Linux
```

#### フロントエンドが起動しない

```bash
# node_modules削除 & 再インストール
rm -rf node_modules package-lock.json
npm install

# ポートが使用中
lsof -ti:5173 | xargs kill -9  # macOS/Linux
```

#### AWSリソースにアクセスできない

```bash
# AWS認証情報を確認
aws sts get-caller-identity

# プロファイル確認
echo $AWS_PROFILE

# 環境変数を確認
cat backend/.env
```

### GitHub Actionsが失敗

#### OIDC認証エラー

```bash
# GitHub Secretsを確認
gh secret list --env prod
gh secret list --env dev

# 必要なシークレット:
# AWS_ROLE_ARN (環境ごと)
```

#### Terraform Applyが失敗

```bash
# ローカルで状態を確認
cd terraform/environments/prod
terraform init
terraform plan

# S3の状態ファイルを確認
aws s3 ls s3://jigsaw-puzzle-terraform-state/prod/
```

#### Lambda Deployが失敗

```bash
# ローカルで手動デプロイしてみる
./scripts/deploy-lambda.sh dev

# Lambda関数が存在するか確認
aws lambda get-function --function-name jigsaw-puzzle-dev-puzzle-register
```

---

## 📦 依存関係の追加

### バックエンド

```bash
# 本番用
uv add requests

# 開発用
uv add --dev pytest-mock

# 依存関係の同期
uv sync
```

### フロントエンド

```bash
cd frontend

# 本番用
npm install axios

# 開発用
npm install --save-dev @types/node
```

---

## 🔍 デバッグ方法

### バックエンド

```bash
# Swagger UIで確認
# http://localhost:8000/docs

# ログ確認
cd backend
uv run uvicorn app.api.main:app --reload --log-level debug

# IPythonでインタラクティブデバッグ
uv add --dev ipython
uv run ipython
>>> from app.services.puzzle_service import PuzzleService
>>> service = PuzzleService()
>>> service.list_puzzles("test-user")
```

### フロントエンド

```bash
# ブラウザのDevTools (F12)
# Console, Network, React DevToolsを活用

# Viteの詳細ログ
npm run dev -- --debug
```

### AWS Lambda（本番）

```bash
# CloudWatch Logsを確認
aws logs tail /aws/lambda/jigsaw-puzzle-prod-puzzle-register --follow

# または
aws logs tail /aws/lambda/jigsaw-puzzle-dev-puzzle-register --follow
```

---

## 📚 参考ドキュメント

- [CLAUDE.md](../CLAUDE.md) - プロジェクト全体の構成
- [20251026_cicd-architecture.md](./20251026_cicd-architecture.md) - CI/CD詳細
- [20251026_cicd-quick-reference.md](./20251026_cicd-quick-reference.md) - クイックリファレンス
- [20251018_react-frontend-guide.md](./20251018_react-frontend-guide.md) - フロントエンド開発ガイド
- [20251022_github-oidc-setup.md](./20251022_github-oidc-setup.md) - OIDC設定

---

## ✅ 開発前チェックリスト

新しい機能開発を始める前に：

- [ ] `develop` ブランチを最新に（`git pull`）
- [ ] featureブランチを作成
- [ ] ローカル環境が動作することを確認
- [ ] 環境変数が正しく設定されている
- [ ] AWS認証情報が有効

開発完了時：

- [ ] テストが通る（`pytest`, `npm test`）
- [ ] Lintエラーがない
- [ ] 型チェックが通る（`mypy`, `tsc`）
- [ ] コミットメッセージが明確
- [ ] PRの説明が十分

以上が開発ワークフローです！
