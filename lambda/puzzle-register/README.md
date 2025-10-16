# Puzzle Register Lambda Function

パズル登録用のLambda関数。ビジネスロジックは`backend/puzzle_logic.py`で実装されており、このファイルは薄いラッパーです。

## アーキテクチャ

```
Lambda (index.py)
  ↓ (ラッパー)
backend/puzzle_logic.py
  ↓ (ビジネスロジック)
AWS Services (S3, DynamoDB)
```

同じビジネスロジックを使用するため:
- **ローカル開発**: FastAPI (`backend/app.py`)
- **本番環境**: Lambda (`lambda/puzzle-register/index.py`)

## デプロイ

### 1. パッケージング

Lambda用のzipファイルを作成する際、`backend/`ディレクトリも含める必要があります。

```bash
# プロジェクトルートから実行
cd lambda/puzzle-register

# backend をコピー
cp -r ../../backend ./backend

# パッケージング
zip -r function.zip index.py backend/

# backendディレクトリを削除（クリーンアップ）
rm -rf backend
```

### 2. Lambda関数の更新

```bash
aws lambda update-function-code \
  --function-name jigsaw-puzzle-dev-puzzle-register \
  --zip-file fileb://function.zip
```

### 3. Terraform経由でのデプロイ

```bash
# まずzipを作成
cd lambda/puzzle-register
cp -r ../../backend ./backend
zip -r function.zip index.py backend/
rm -rf backend

# Terraformを実行
cd ../../terraform/environments/dev
terraform apply
```

## デプロイスクリプト（推奨）

手動でやるのは面倒なので、スクリプトを作成することを推奨します。

`scripts/deploy-lambda.sh`:
```bash
#!/bin/bash
set -e

FUNCTION_NAME="jigsaw-puzzle-dev-puzzle-register"
LAMBDA_DIR="lambda/puzzle-register"

echo "Packaging Lambda function..."

cd $LAMBDA_DIR

# Clean up
rm -rf backend function.zip

# Copy backend
cp -r ../../backend ./backend

# Package
zip -r function.zip index.py backend/ requirements.txt

# Deploy
echo "Deploying to Lambda..."
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://function.zip

# Clean up
rm -rf backend

echo "Deployment complete!"
```

実行：
```bash
chmod +x scripts/deploy-lambda.sh
./scripts/deploy-lambda.sh
```

## ローカルテスト

### 方法1: FastAPIで開発

```bash
cd backend
uvicorn app:app --reload
```

これが推奨方法です。ブレークポイントも使えます。

### 方法2: Lambda関数を直接テスト

```bash
cd lambda/puzzle-register

# backendをコピー
cp -r ../../backend ./backend

# テストイベントを作成
cat > test_event.json <<EOF
{
  "body": "{\"pieceCount\": 300, \"fileName\": \"test.jpg\"}"
}
EOF

# テスト実行
python3 -c "
import json
import index

event = json.load(open('test_event.json'))
result = index.handler(event, None)
print(json.dumps(result, indent=2))
"

# クリーンアップ
rm -rf backend test_event.json
```

## 環境変数

Lambda関数には以下の環境変数が必要です（Terraformで自動設定）:

- `S3_BUCKET_NAME`: S3バケット名
- `PUZZLES_TABLE_NAME`: DynamoDBテーブル名（Puzzles）
- `PIECES_TABLE_NAME`: DynamoDBテーブル名（Pieces）
- `ENVIRONMENT`: 環境名（dev/staging/prod）

## ディレクトリ構造（デプロイ後）

```
function.zip
├── index.py              # Lambda handler (ラッパー)
├── requirements.txt      # 依存関係
└── backend/
    ├── puzzle_logic.py   # ビジネスロジック
    └── (その他のファイル)
```

## 開発ワークフロー

1. **ローカルで開発**
   ```bash
   cd backend
   uvicorn app:app --reload
   # ブラウザで http://localhost:8000/docs にアクセス
   ```

2. **ビジネスロジックを修正**
   ```bash
   vim backend/puzzle_logic.py
   # FastAPIが自動リロード
   ```

3. **テスト**
   ```bash
   curl -X POST http://localhost:8000/puzzles \
     -H "Content-Type: application/json" \
     -d '{"pieceCount": 300}'
   ```

4. **満足したらLambdaにデプロイ**
   ```bash
   ./scripts/deploy-lambda.sh
   ```

5. **本番環境でテスト**
   ```bash
   curl -X POST https://xxx.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles \
     -H "Content-Type: application/json" \
     -d '{"pieceCount": 300}'
   ```

## トラブルシューティング

### Lambda関数でImportError

```
ImportError: cannot import name 'PuzzleService' from 'puzzle_logic'
```

**原因**: `backend/` ディレクトリがzipに含まれていない

**解決方法**:
```bash
cd lambda/puzzle-register
cp -r ../../backend ./backend
zip -r function.zip index.py backend/
```

### ローカルとLambdaで動作が異なる

**原因**: 環境変数の違い、AWS認証情報の違い

**解決方法**:
- ローカルの環境変数を確認
- Lambda関数の環境変数を確認（AWSコンソール）
- IAMロールの権限を確認

## 次のステップ

1. ✅ Lambda関数をラッパーに変更（完了）
2. ⏭ API Gatewayモジュール作成
3. ⏭ dev環境への統合
4. ⏭ デプロイとテスト
