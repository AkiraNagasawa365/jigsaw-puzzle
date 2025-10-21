# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

ジグソーパズル支援システム - ユーザーがジグソーパズルを登録し、ピース画像をアップロードして、ピースの位置を特定できるWebアプリケーション。Reactフロントエンド、FastAPIバックエンド（ローカル開発）、AWS Lambda（本番環境）、Terraformでインフラ構築。

## 技術スタック

**バックエンド:**
- Python 3.12（uvで管理）
- FastAPI（ローカル開発）
- AWS Lambda（本番環境）
- DynamoDB（データベース）
- S3（画像ストレージ）

**フロントエンド:**
- React 19 + TypeScript
- Vite（ビルドツール）
- React Router
- AWS Amplify（認証統合）
- AWS Cognito（ユーザー認証）

**インフラ:**
- Terraform（IaC）
- AWS（Lambda, API Gateway, DynamoDB, S3, CloudFront, Cognito）

## よく使うコマンド

### バックエンド開発

```bash
# uvで依存関係をインストール
uv sync

# ローカルでFastAPIサーバーを起動
cd backend
uv run uvicorn app.api.main:app --reload

# カバレッジ付きでテスト実行
cd backend
uv run pytest

# 特定のテストファイルを実行
uv run pytest tests/unit/test_puzzle_service.py -v

# 依存関係を追加
uv add <package-name>

# 開発用依存関係を追加
uv add --dev <package-name>
```

### フロントエンド開発

```bash
cd frontend

# 依存関係をインストール
npm install

# 開発サーバーを起動（http://localhost:5173）
npm run dev

# 型チェック
npm run build  # tsc -b も実行される

# Lint実行
npm run lint

# 本番環境ビルド
npm run build

# 本番環境ビルドをプレビュー
npm run preview
```

### テスト

```bash
# バックエンドのテスト（カバレッジ付き）
cd backend
uv run pytest                              # 全テストを実行
uv run pytest tests/unit/ -v              # 単体テストのみ
uv run pytest tests/unit/ -v --cov-report=term-missing:skip-covered  # カバレッジレポート付き
```

### デプロイ

```bash
# Lambda関数をデプロイ
./scripts/deploy-lambda.sh

# フロントエンドをデプロイ（S3 + CloudFront）
./scripts/deploy-frontend.sh

# Terraform（インフラ）
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

## 全体アーキテクチャ

### デュアルバックエンドパターン

このプロジェクトは、ローカル開発と本番環境の両方をサポートするために**デュアルバックエンドアーキテクチャ**を採用しています：

1. **ローカル開発（FastAPI）**: `backend/app/` に配置、標準的なWebサーバーとして動作
2. **本番環境（Lambda）**: `lambda/puzzle-register/` に配置、サーバーレス関数として動作
3. **共通ビジネスロジック**: 両方のバックエンドが `backend/app/services/` と `backend/app/core/` の同じコードを使用

Lambdaデプロイ時、`deploy-lambda.sh` スクリプトが `backend/app/` をLambdaパッケージにコピーし、両環境で同一のビジネスロジックが実行されることを保証します。

### 設定管理

**環境変数:**
- ローカル開発: `backend/.env` から `python-dotenv` 経由で読み込み
- Lambda本番: Terraform経由で環境変数として注入
- 設定クラス: `backend/app/core/config.py` (`Settings` クラス)

`Settings` クラスは、利用可能な場合は `.env` ファイルを使用し（ローカル開発）、なければ環境変数にフォールバック（Lambda）します。これにより、同じコードが両環境で動作します。

**主要な環境変数:**
- `S3_BUCKET_NAME`: 画像用S3バケット
- `PUZZLES_TABLE_NAME`: パズル用DynamoDBテーブル
- `PIECES_TABLE_NAME`: ピース用DynamoDBテーブル（将来の使用）
- `ENVIRONMENT`: dev/staging/prod
- `AWS_REGION`: AWSリージョン（デフォルト: ap-northeast-1）
- `ALLOWED_ORIGINS`: CORS許可オリジン（カンマ区切り）

### データフロー

1. **パズル作成**:
   - フロントエンド → API（FastAPI/Lambda）→ DynamoDB（status "pending" でパズルレコード作成）
   - フロントエンドに `puzzleId` を返却

2. **画像アップロード**:
   - フロントエンド → API（Pre-signed URL をリクエスト）
   - API → S3（Pre-signed URL を生成）
   - フロントエンド → S3（Pre-signed URL を使って直接アップロード）
   - パズルのステータスを "uploaded" に更新

3. **将来実装予定: 画像処理**:
   - S3イベントがLambdaをトリガー
   - Lambdaが画像を処理し、ピースを抽出
   - ピースデータをDynamoDBに保存
   - パズルのステータスを "completed" に更新

### ディレクトリ構造

```
backend/app/
├── api/
│   ├── main.py           # FastAPIアプリケーションのエントリーポイント
│   └── routes/
│       └── puzzles.py    # パズル関連のAPIルート
├── core/
│   ├── config.py         # 設定（環境変数）
│   ├── schemas.py        # バリデーション用Pydanticモデル
│   └── logger.py         # ロギング設定
└── services/
    ├── puzzle_service.py # コアビジネスロジック（Lambdaと共有）
    └── image_processor.py # 画像処理（将来実装）

frontend/src/
├── components/           # 再利用可能なReactコンポーネント
│   ├── PuzzleList.tsx
│   └── ProtectedRoute.tsx  # 認証が必要なルート用
├── pages/               # ページコンポーネント
│   ├── Home.tsx
│   ├── auth/           # 認証関連ページ
│   │   ├── Login.tsx
│   │   └── Register.tsx
│   └── puzzles/
│       ├── PuzzleCreate.tsx
│       └── PuzzleDetail.tsx
├── contexts/           # Reactコンテキスト
│   └── AuthContext.tsx # 認証状態管理
├── types/              # TypeScript型定義
│   └── puzzle.ts
├── config/
│   ├── api.ts         # APIベースURL設定
│   └── amplify.ts     # AWS Amplify設定
├── App.tsx            # ルーティングを含むメインアプリ
└── main.tsx           # Reactエントリーポイント

terraform/
├── modules/            # 再利用可能なTerraformモジュール
│   ├── s3/            # S3バケット設定
│   ├── dynamodb/      # DynamoDBテーブル
│   ├── lambda/        # Lambda関数
│   ├── api-gateway/   # API Gateway REST API
│   ├── iam/           # IAMロールとポリシー
│   └── frontend/      # CloudFront + S3静的ホスティング
└── environments/
    └── dev/           # 開発環境設定

lambda/
└── puzzle-register/
    ├── index.py       # Lambdaハンドラー関数
    └── README.md
```

### サービスレイヤーパターン

`PuzzleService` クラス（`backend/app/services/puzzle_service.py`）はパズル関連のビジネスロジックをすべてカプセル化しています：
- `create_puzzle()`: DynamoDBにパズルレコードを作成
- `generate_upload_url()`: S3のPre-signed URLを生成
- `get_puzzle()`: IDでパズルを取得
- `list_puzzles()`: ユーザーのパズル一覧を取得

このサービスはFastAPIルートとLambdaハンドラーの両方でインスタンス化され、一貫性を保証します。

### スキーマバリデーション

`backend/app/core/schemas.py` のPydanticモデルは以下を提供します：
- 型バリデーション
- XSS保護（HTMLタグや危険な文字を除去）
- フィールド制約（最小/最大長、許可された値）
- FastAPI経由での自動APIドキュメント生成

例: `PuzzleCreateRequest` は `pieceCount` が [100, 300, 500, 1000, 2000] のいずれかであることを強制します。

### フロントエンドAPI統合

フロントエンドは環境変数でAPIエンドポイントを設定します：
- `.env` の `VITE_API_BASE_URL`（デフォルトは http://localhost:8000）
- `src/config/api.ts` のAPIクライアントが `API_BASE_URL` をエクスポート
- すべてのfetch呼び出しで `${API_BASE_URL}/endpoint` を使用

これにより、ローカルFastAPIと本番LambdaのAPIをシームレスに切り替えられます。

### 認証アーキテクチャ

**AWS Cognito統合:**
- フロントエンドは `aws-amplify` を使用してCognitoと統合
- `AuthContext` がユーザーの認証状態を管理
- `ProtectedRoute` コンポーネントで保護されたページへのアクセスを制御
- 認証フロー: ユーザー登録 → メール確認 → ログイン → ID Token取得

**設定:**
- `frontend/src/config/amplify.ts`: Amplify設定（Cognito UserPoolとClientID）
- 環境変数: `VITE_COGNITO_USER_POOL_ID`, `VITE_COGNITO_CLIENT_ID`

### テスト戦略

テストは種類別に整理されています：
- `backend/tests/unit/`: 単体テスト（外部依存なし）
- `backend/tests/integration/`: 統合テスト（`moto` を使ったAWSモック付き）
- `backend/tests/conftest.py`: 共有pytestフィクスチャ

**カバレッジ要件:**
- 最小カバレッジ: 80%（pytest.iniで強制）
- カバレッジレポート: `backend/htmlcov/` にHTMLレポート

### DynamoDBスキーマ

**Puzzlesテーブル:**
- PK: `userId`（String）
- SK: `puzzleId`（UUID String）
- 属性: `puzzleName`, `pieceCount`, `fileName`, `s3Key`, `status`, `createdAt`, `updatedAt`
- GSI: `CreatedAtIndex` （時系列クエリ用）

**ステータスフロー:** pending → uploaded → processing → completed

**Piecesテーブル**（将来実装）:
- PK: `puzzleId`
- SK: `pieceId`
- 属性: `position`（Map）, `imageFeatures`, `matched`, `placedAt`

### Terraformモジュールパターン

各AWSリソースタイプには独自のモジュールがあります：
- モジュールは環境（dev/staging/prod）間で再利用可能
- 環境固有の値は変数として渡される
- モジュールからの出力は他のモジュールから参照可能
- ステートは環境ごとに分離

例: `terraform/modules/lambda/` はLambda関数、IAMロール、CloudWatch Logsを定義します。開発環境（`terraform/environments/dev/`）はdev固有の設定でインスタンス化します。

### CORS設定

CORSは `ALLOWED_ORIGINS` 環境変数で設定されます：
- **ローカル開発**: `http://localhost:3000,http://localhost:5173`（旧ポートとViteポートの両方をサポート）
- **本番環境**: CloudFrontドメイン（例: `https://d123.cloudfront.net`）
- 設定場所: `backend/app/api/main.py`（FastAPIミドルウェア）

### ロギング

`backend/app/core/logger.py` による集中ログ管理：
- Pythonの `logging` モジュールを使用
- 本番環境用JSON形式（Lambda → CloudWatch）
- ローカル開発用人間可読形式
- 環境によってログレベルを制御

## 重要な実装ノート

### Lambdaデプロイプロセス

1. `deploy-lambda.sh` が `backend/app/` を `lambda/puzzle-register/backend/` にコピー
2. `pyproject.toml` から依存関係を `requirements.txt` にエクスポート
3. `.env`, `__pycache__`, `.pyc` を除外したZIPパッケージを作成
4. AWS CLI経由でAWS Lambdaにアップロード
5. 一時ファイルをクリーンアップ

**重要**: Lambda関数は `backend.app.*` パスからインポートする必要があります（例: `from backend.app.services.puzzle_service import PuzzleService`）。

### uvによるPythonパッケージ管理

このプロジェクトはpipの代わりに `uv`（モダンなPythonパッケージマネージャー）を使用します：
- 依存関係は `pyproject.toml` で定義
- ロックファイル: `uv.lock`
- 仮想環境: `.venv/`
- コマンド実行: `uv run <command>`
- パッケージ追加: `uv add <package>`

### フロントエンド環境変数

Viteでは環境変数に `VITE_` プレフィックスが必要です：
- `.env`: デフォルト値（**削除済み** - セキュリティ上の理由）
- `.env.local`: ローカル上書き（gitignore対象、各開発者が作成）
- `.env.production`: 本番環境値（コミット済み）

**重要な環境変数:**
- `VITE_API_BASE_URL`: APIエンドポイント
- `VITE_COGNITO_USER_POOL_ID`: Cognito User Pool ID
- `VITE_COGNITO_CLIENT_ID`: Cognito App Client ID
- `VITE_AWS_REGION`: AWSリージョン（デフォルト: ap-northeast-1）

TypeScriptでのアクセス: `import.meta.env.VITE_API_BASE_URL`

**注意**: `.env.example` ファイルは削除されました。環境変数は各自でTerraform outputから取得して `.env.local` に設定してください。

### APIエンドポイントパターン

**RESTful設計:**
- `POST /puzzles` - パズル作成
- `GET /puzzles/{puzzleId}?user_id={userId}` - パズル取得
- `GET /users/{userId}/puzzles` - ユーザーのパズル一覧取得
- `POST /puzzles/{puzzleId}/upload` - アップロードURL取得

### React 19とAWS Amplifyの互換性

このプロジェクトは **React 19** を使用しています。`aws-amplify` と `@aws-amplify/ui-react` は React 19 をサポートしています：
- `aws-amplify`: ^6.15.7
- `@aws-amplify/ui-react`: ^6.13.0

**依存関係管理:**
- フロントエンドの依存関係は `frontend/package.json` で管理
- バックエンドの依存関係は `pyproject.toml` で管理（uvパッケージマネージャー）

### セキュリティ考慮事項

1. **XSS保護**: `schemas.py` のバリデーターがHTMLタグと危険な文字を除去
2. **入力バリデーション**: Pydanticがフィールド制約（長さ、許可値）を強制
3. **Pre-signed URL**: S3への直接アップロードでAPI経由の画像ルーティングを回避
4. **IAM**: Lambdaは最小限の権限のみ（S3バケット、DynamoDBテーブルのみ）
5. **CORS**: 許可オリジンを明示的にホワイトリスト化
6. **Lambdaに.envなし**: `deploy-lambda.sh` がパッケージング前に `.env` ファイルを明示的に削除
7. **Cognito認証**: フロントエンドでユーザー認証を実装（ID Tokenをバックエンドに送信）

## 開発ワークフロー

1. **環境変数セットアップ**:
   - Terraformでインフラをデプロイ後、outputからCognito情報を取得
   - `frontend/.env.local` を作成し、必要な環境変数を設定
   - `backend/.env` を作成（ローカル開発用）

2. **ローカルバックエンド起動**: `cd backend && uv run uvicorn app.api.main:app --reload`

3. **フロントエンド起動**: `cd frontend && npm run dev`

4. **変更**: `backend/app/services/` の共有サービスを編集

5. **ローカルテスト**: http://localhost:5173 経由でテスト
   - 未認証時: ログイン/登録ページが表示される
   - 認証後: パズル一覧、作成、アップロードが可能

6. **テスト実行**: `cd backend && uv run pytest`

7. **Lambdaへデプロイ**: `./scripts/deploy-lambda.sh`

8. **インフラ更新**: `cd terraform/environments/dev && terraform apply`
