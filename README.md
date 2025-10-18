# Jigsaw Puzzle Helper System

Web上でジグソーパズルを登録し、ピース画像をアップロードすることで該当ピースの位置を特定できるシステム。

## 技術スタック

### バックエンド
- **インフラ**: AWS (Lambda, API Gateway, S3, DynamoDB)
- **IaC**: Terraform
- **言語**: Python 3.12
- **パッケージ管理**: uv
- **ローカル開発**: FastAPI
- **本番環境**: AWS Lambda

### フロントエンド
- **フレームワーク**: React 18
- **ビルドツール**: Vite
- **言語**: TypeScript
- **ルーティング**: React Router
- **パッケージ管理**: npm

## プロジェクト構成

```
jigsaw-puzzle/
├── frontend/          # React フロントエンド
│   ├── src/
│   │   ├── components/  # 再利用可能なコンポーネント
│   │   ├── pages/       # ページコンポーネント
│   │   ├── types/       # TypeScript型定義
│   │   ├── App.tsx      # メインアプリ
│   │   └── main.tsx     # エントリーポイント
│   ├── package.json
│   └── vite.config.ts
├── backend/           # FastAPI（ローカル開発用）
│   └── app/
│       ├── api/
│       │   ├── main.py          # FastAPIアプリケーション
│       │   └── routes/          # APIルート定義
│       │       └── puzzles.py
│       ├── core/
│       │   ├── config.py        # 設定管理
│       │   └── schemas.py       # Pydanticスキーマ
│       └── services/
│           └── puzzle_service.py # ビジネスロジック（Lambda共通）
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

#### バックエンド (FastAPI)

```bash
# 環境変数を設定（AWSリソースが必要）
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=default
export S3_BUCKET_NAME=jigsaw-puzzle-dev-images
export PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
export PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces
export ENVIRONMENT=dev

# backendディレクトリに移動
cd backend

# FastAPIを起動
uv run uvicorn app.api.main:app --reload

# Swagger UI
# http://localhost:8000/docs
```

#### フロントエンド (React + Vite)

```bash
# 別のターミナルで実行
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動
npm run dev

# ブラウザで開く
# http://localhost:5173/
```

### 4. AWSへのデプロイ

#### バックエンド（Lambda）

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

#### フロントエンド（本番ビルド）

```bash
cd frontend

# 1. 本番環境のAPI URLを設定
# frontend/.env.production を編集してAPI Gateway URLを設定

# 2. ビルド
npm run build

# 3. dist/ フォルダが生成される
# この中身をS3やCloudFrontなどにデプロイ
```

**注意:** フロントエンドのデプロイ先（S3 + CloudFront など）のインフラは今後実装予定です。

## 使い方

### 1. パズルを新規作成

1. ブラウザで `http://localhost:5173/` を開く
2. 「+ 新規作成」ボタンをクリック
3. パズル名を入力（例：「富士山の風景」）
4. ピース数を選択（100, 300, 500, 1000, 2000）
5. 「パズルを作成」ボタンをクリック

### 2. パズル画像をアップロード

1. パズル作成後、自動的に詳細画面に遷移
2. 画像ファイルを選択
3. 「画像をアップロード」ボタンをクリック
4. S3に画像が保存されます

### 3. パズル一覧を確認

1. ホーム画面に登録済みパズルが一覧表示される
2. パズルカードをクリックすると詳細画面に遷移
3. 各パズルのステータス（待機中、アップロード済み、処理中、完了）を確認できる

## ドキュメント

- [システム設計書](docs/system-design.md) - アーキテクチャの全体像
- [実装ロードマップ](docs/implementation-roadmap.md) - Phase別の実装計画
- [デプロイガイド](docs/deployment-guide.md) - AWSへのデプロイ手順
- [React フロントエンド開発ガイド](docs/20251018_react-frontend-guide.md) - フロントエンド実装の詳細

## 開発ワークフロー

### ローカル開発（フルスタック）

```bash
# 1. バックエンドを起動（ターミナル1）
cd backend
uv run uvicorn backend.app:app --reload

# 2. フロントエンドを起動（ターミナル2）
cd frontend
npm run dev

# 3. ブラウザで確認
# フロントエンド: http://localhost:5173/
# API Swagger: http://localhost:8000/docs

# 4. コードを修正
# - バックエンド: backend/puzzle_logic.py または backend/app.py
# - フロントエンド: frontend/src/ 配下のファイル
# 両方とも自動リロードされます

# 5. 満足したらLambdaにデプロイ
./scripts/deploy-lambda.sh
```

### フロントエンド開発

```bash
# TypeScriptの型チェック
cd frontend
npm run type-check

# ビルド
npm run build

# プレビュー（本番環境に近い状態）
npm run preview
```

### パッケージの追加

#### Python（バックエンド）

```bash
# 本番用の依存関係を追加
uv add <package-name>

# 開発用の依存関係を追加
uv add --dev <package-name>

# 依存関係を同期
uv sync
```

#### JavaScript（フロントエンド）

```bash
cd frontend

# 本番用の依存関係を追加
npm install <package-name>

# 開発用の依存関係を追加
npm install --save-dev <package-name>
```

### コードフォーマット

```bash
# コードをフォーマット
uv run black backend/app/ lambda/

# Lintチェック
uv run ruff check backend/app/ lambda/
```

## フロントエンドとバックエンドの接続

フロントエンドは環境変数でバックエンドのAPIエンドポイントを設定します。

### 環境変数の設定

#### ローカル開発（デフォルト）

`frontend/.env` ファイルで設定済み：
```bash
VITE_API_BASE_URL=http://localhost:8000
```

#### 本番環境（Lambda + API Gateway）

`frontend/.env.production` を編集：
```bash
# 実際のAPI Gateway URLに変更してください
VITE_API_BASE_URL=https://your-api-id.execute-api.ap-northeast-1.amazonaws.com/dev
```

#### カスタム設定（開発者ごと）

`frontend/.env.local` を作成（gitignoreされています）：
```bash
VITE_API_BASE_URL=http://localhost:9000
```

### 環境変数の優先順位

Viteは以下の優先順位で環境変数を読み込みます：
1. `.env.local` （最優先、gitignore対象）
2. `.env.[mode]` （`.env.production`など）
3. `.env` （デフォルト）

### 実装の詳細

全てのAPIリクエストは `frontend/src/config/api.ts` で定義された `API_BASE_URL` を使用：

```typescript
import { API_BASE_URL } from '../config/api'

// 使用例
const response = await fetch(`${API_BASE_URL}/puzzles`)
```

## API エンドポイント

### ローカル開発
- Base URL: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### エンドポイント一覧

#### パズル管理
- `POST /puzzles` - 新規パズル作成（画像なし）
- `POST /puzzles/{puzzleId}/upload` - パズル画像のアップロードURL取得
- `GET /puzzles/{puzzleId}` - パズル情報の取得
- `GET /users/{userId}/puzzles` - ユーザーのパズル一覧取得

#### ヘルスチェック
- `GET /` - API ヘルスチェック
- `GET /debug/config` - 設定情報（開発環境のみ）

### AWS (本番)
- Base URL: `https://<api-id>.execute-api.ap-northeast-1.amazonaws.com/dev`

## 環境変数

### バックエンド（ローカル開発用）

ローカル開発では環境変数を直接エクスポートします：

```bash
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=default
export S3_BUCKET_NAME=jigsaw-puzzle-dev-images
export PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
export PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces
export ENVIRONMENT=dev
export ALLOWED_ORIGINS=http://localhost:3000
```

**参考**: デフォルト値は `backend/.env.example` に記載されています。

**ALLOWED_ORIGINS**: CORS許可オリジン（カンマ区切りで複数指定可）
- 開発環境: `http://localhost:3000`
- 本番環境: `https://your-cloudfront-domain.cloudfront.net`

### Lambda用（本番環境）

Terraformで自動的に設定されます（`terraform/modules/lambda/main.tf`）。

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

## アーキテクチャ

### ワークフロー

1. **パズル作成**
   - ユーザーがパズル名とピース数を入力
   - バックエンドがパズルレコードをDynamoDBに作成
   - ステータス: `pending`

2. **画像アップロード**
   - ユーザーが画像ファイルを選択
   - バックエンドがS3用のPre-signed URLを生成
   - フロントエンドが直接S3に画像をアップロード
   - ステータス: `pending` → `uploaded`

3. **画像処理（今後実装予定）**
   - Lambda関数が画像を分割処理
   - 各ピース画像をS3に保存
   - ピース情報をDynamoDBに保存
   - ステータス: `uploaded` → `processing` → `completed`

### データモデル

#### Puzzles テーブル
- `userId` (PK): ユーザーID
- `puzzleId` (SK): パズルID
- `puzzleName`: パズル名
- `pieceCount`: ピース数
- `fileName`: ファイル名（オプショナル）
- `s3Key`: S3キー（オプショナル）
- `status`: ステータス（pending, uploaded, processing, completed）
- `createdAt`: 作成日時
- `updatedAt`: 更新日時

## テスト

### バックエンド

```bash
# テストを実行
uv run pytest

# カバレッジ付き
uv run pytest --cov=backend --cov-report=html
```

### フロントエンド

```bash
cd frontend

# TypeScript型チェック
npm run type-check

# Lintチェック（設定されている場合）
npm run lint
```

