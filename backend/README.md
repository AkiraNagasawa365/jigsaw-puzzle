# Backend - Local Development Environment

FastAPIを使ったローカル開発環境。Lambda関数と同じビジネスロジック（`puzzle_logic.py`）を使用します。

## セットアップ

### 1. 依存関係のインストール

```bash
cd backend
pip install -r requirements.txt
```

または仮想環境を使う場合：

```bash
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 環境変数の設定

ローカル開発では `uv run python scripts/sync_config.py backend` を実行すると
`backend/.env.local` が生成され、FastAPI 実行時に自動読み込みされます。
直接エクスポートする場合は以下を参考にしてください。

```bash
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=default
export S3_BUCKET_NAME=jigsaw-puzzle-dev-images
export PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
export PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces
export ENVIRONMENT=dev
export ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. AWS認証情報の設定

```bash
# AWS CLIが設定済みであること
aws configure
```

## ローカル実行

### 方法1: uvicornコマンド

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 方法2: Pythonスクリプト実行

```bash
python app.py
```

### アクセス

- API: http://localhost:8000
- Swagger UI (ドキュメント): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API エンドポイント

### 1. ヘルスチェック

```bash
curl http://localhost:8000/
```

### 2. パズル登録

```bash
curl -X POST http://localhost:8000/puzzles \
  -H "Content-Type: application/json" \
  -d '{
    "pieceCount": 300,
    "fileName": "my-puzzle.jpg",
    "userId": "user-123"
  }'
```

レスポンス：
```json
{
  "puzzleId": "abc-123-def-456",
  "uploadUrl": "https://s3-presigned-url...",
  "expiresIn": 300,
  "message": "Pre-signed URL generated successfully..."
}
```

### 3. パズル情報取得

```bash
curl http://localhost:8000/puzzles/abc-123-def-456?user_id=user-123
```

### 4. ユーザーのパズル一覧

```bash
curl http://localhost:8000/users/user-123/puzzles
```

### 5. 設定確認（開発用）

```bash
curl http://localhost:8000/debug/config
```

## デバッグ

### VSCodeでのデバッグ

`.vscode/launch.json` を作成：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": true
    }
  ]
}
```

F5キーでデバッグ開始。ブレークポイントを設定して、ステップ実行が可能。

### Postmanでのテスト

Postmanを使うとGUIでAPIをテストできます：

1. Postmanを開く
2. 新しいリクエストを作成
3. `POST http://localhost:8000/puzzles`
4. Body → raw → JSON を選択
5. リクエストボディを入力して Send

## テスト

### 単体テスト（今後追加予定）

```bash
pytest
```


### ログ確認

FastAPIはリクエスト/レスポンスのログを標準出力に表示します。

```
INFO:     127.0.0.1:52345 - "POST /puzzles HTTP/1.1" 200 OK
```

## 本番環境（Lambda）との違い

| 項目 | ローカル（FastAPI） | 本番（Lambda） |
|------|-------------------|---------------|
| **実行環境** | ローカルPC | AWS Lambda |
| **起動方法** | `uvicorn app:app` | API Gateway経由 |
| **デバッグ** | ブレークポイント可 | CloudWatch Logs |
| **ビジネスロジック** | `puzzle_logic.py` | `puzzle_logic.py`（同じ） |
| **認証** | なし | API Key/Cognito |

## トラブルシューティング

### 1. boto3のエラー

```
NoCredentialsError: Unable to locate credentials
```

**解決方法:**
```bash
aws configure
# または
export AWS_PROFILE=your-profile
```

### 2. DynamoDBテーブルが見つからない

```
ResourceNotFoundException: Requested resource not found
```

**解決方法:**
- Terraformでリソースを作成済みか確認
- テーブル名が正しいか確認（環境変数）

### 3. S3バケットが見つからない

**解決方法:**
- Terraformでバケットを作成済みか確認
- バケット名が正しいか確認（環境変数）

## ファイル構成

```
backend/
├── app.py              # FastAPI アプリケーション
├── puzzle_logic.py     # ビジネスロジック（Lambda共通）
├── requirements.txt    # 依存関係
└── README.md          # このファイル
```

## 次のステップ

1. ローカルで動作確認
2. 必要に応じてビジネスロジックを修正
3. Lambda関数にデプロイ（`puzzle_logic.py`をコピー）
4. API Gateway経由でテスト
