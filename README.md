# Jigsaw Puzzle Helper System

Web上でジグソーパズルを登録し、ピース画像をアップロードすることで該当ピースの位置を特定できるシステム。

## 技術スタック

- **インフラ**: AWS (Lambda, API Gateway, S3, DynamoDB)
- **IaC**: Terraform
- **言語**: Python 3.12
- **パッケージ管理**: uv
- **ローカル開発**: FastAPI
- **本番環境**: AWS Lambda

## プロジェクト構成

```
jigsaw-puzzle/
├── backend/           # FastAPI（ローカル開発用）
│   ├── app.py        # FastAPIアプリケーション
│   └── puzzle_logic.py # ビジネスロジック（Lambda共通）
├── lambda/           # Lambda関数
│   └── puzzle-register/ # パズル登録Lambda
├── terraform/        # インフラ定義
│   ├── modules/     # 再利用可能なモジュール
│   └── environments/ # 環境別設定
├── docs/            # ドキュメント
├── scripts/         # デプロイスクリプト
├── pyproject.toml   # Python依存関係管理
└── .python-version  # Pythonバージョン指定
```

## クイックスタート

### 1. uvのインストール

#### macOS / Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. プロジェクトのセットアップ

```bash
# リポジトリをクローン
git clone <your-repo-url>
cd jigsaw-puzzle

# Python 3.12をインストール & 依存関係をインストール
uv sync

# 仮想環境を有効化
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows
```

### 3. ローカル開発サーバーの起動

```bash
# 環境変数を設定（AWSリソースが必要）
export S3_BUCKET_NAME=jigsaw-puzzle-dev-images
export PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
export PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces

# FastAPIを起動
uv run uvicorn backend.app:app --reload

# ブラウザで開く
# http://localhost:8000/docs
```

### 4. AWSへのデプロイ

```bash
# Terraformでインフラを作成
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# Lambda関数をデプロイ
cd ../../..
./scripts/deploy-lambda.sh
```

## ドキュメント

- [システム設計書](docs/system-design.md) - アーキテクチャの全体像
- [実装ロードマップ](docs/implementation-roadmap.md) - Phase別の実装計画
- [デプロイガイド](docs/deployment-guide.md) - AWSへのデプロイ手順
- [開発環境セットアップ](backend/SETUP.md) - 詳細なセットアップ手順

## 開発ワークフロー

### ローカル開発

```bash
# 1. ローカルでFastAPIを起動
uv run uvicorn backend.app:app --reload

# 2. Swagger UIでテスト
# http://localhost:8000/docs

# 3. ビジネスロジックを修正
vim backend/puzzle_logic.py
# FastAPIが自動リロード

# 4. 満足したらLambdaにデプロイ
./scripts/deploy-lambda.sh
```

### パッケージの追加

```bash
# 本番用の依存関係を追加
uv add <package-name>

# 開発用の依存関係を追加
uv add --dev <package-name>

# 依存関係を同期
uv sync
```

### コードフォーマット

```bash
# コードをフォーマット
uv run black backend/ lambda/

# Lintチェック
uv run ruff check backend/ lambda/
```

## API エンドポイント

### ローカル開発
- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### AWS (本番)
- Base URL: `https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/dev`
- パズル登録: `POST /puzzles`

## 環境変数

### ローカル開発用

```bash
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=default
export S3_BUCKET_NAME=jigsaw-puzzle-dev-images
export PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
export PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces
export ENVIRONMENT=dev
```

### Lambda用

Terraformで自動的に設定されます。

## トラブルシューティング

### Python バージョンエラー

```bash
uv python install 3.12
```

### 依存関係エラー

```bash
uv sync
```

### AWS認証エラー

```bash
aws configure
```

### Terraform エラー

```bash
cd terraform/environments/dev
terraform init -upgrade
terraform plan
```

## テスト

```bash
# テストを実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=backend --cov-report=html
```

## ライセンス

MIT

## 貢献

プルリクエスト歓迎！

## 作者

あなたの名前
