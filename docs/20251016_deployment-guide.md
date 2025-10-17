# デプロイガイド

Phase 2（パズル登録API）を実際にAWSにデプロイする手順です。

## 前提条件

### 1. AWS CLIの設定

```bash
# AWS CLIがインストールされているか確認
aws --version

# AWS認証情報が設定されているか確認
aws sts get-caller-identity
```

**出力例:**
```json
{
    "UserId": "AIDAXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-name"
}
```

もし設定されていない場合:
```bash
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: ap-northeast-1
# Default output format: json
```

### 2. Terraformのインストール

```bash
# Terraformがインストールされているか確認
terraform version
```

必要なバージョン: >= 1.0

---

## デプロイ手順

### Step 1: 初期化（初回のみ）

```bash
cd terraform/environments/dev
terraform init
```

**何が起こるか:**
- Terraformプラグインのダウンロード
- モジュールの初期化

**出力例:**
```
Initializing modules...
Initializing the backend...
Initializing provider plugins...
Terraform has been successfully initialized!
```

---

### Step 2: プラン確認

```bash
terraform plan
```

**何が起こるか:**
- 作成されるリソースの確認
- エラーチェック

**確認するポイント:**
```
Plan: XX to add, 0 to change, 0 to destroy.
```

作成されるリソース:
- S3バケット (1個)
- DynamoDBテーブル (2個: Puzzles, Pieces)
- IAMロール (1個)
- Lambda関数 (1個)
- API Gateway (1式)
- CloudWatch Logs (2個)

**予想される数:** Plan: 30-40 to add

---

### Step 3: インフラ作成

```bash
terraform apply
```

**プロンプトが表示されます:**
```
Do you want to perform these actions?
  Enter a value:
```

`yes` と入力してEnterを押す

**所要時間:** 3-5分

**何が起こるか:**
1. S3バケットが作成される
2. DynamoDBテーブルが作成される
3. IAMロールが作成される
4. Lambda関数が作成される（まだコードは空）
5. API Gatewayが作成される

**完了時の出力:**
```
Apply complete! Resources: XX added, 0 changed, 0 destroyed.

Outputs:

api_endpoint = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev"
puzzles_endpoint = "https://xxxxxxxxxx.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles"
puzzle_register_lambda_name = "jigsaw-puzzle-dev-puzzle-register"
puzzles_table_name = "jigsaw-puzzle-dev-puzzles"
s3_bucket_name = "jigsaw-puzzle-dev-images"
...
```

**重要:** この `puzzles_endpoint` のURLをメモしておいてください。テスト時に使います。

---

### Step 4: Lambda関数コードのデプロイ

インフラは作成できましたが、Lambda関数のコードはまだ空です。
実際のコードをデプロイします。

#### 方法A: デプロイスクリプト使用（推奨）

```bash
# プロジェクトルートに戻る
cd ../../../

# デプロイスクリプトを実行
./scripts/deploy-lambda.sh
```

**何が起こるか:**
1. `backend/` ディレクトリをコピー
2. zipファイルを作成
3. Lambda関数にアップロード

**出力例:**
```
===================================
Lambda Deployment Script
===================================
Function: jigsaw-puzzle-dev-puzzle-register
...
Package size: 15K
Deploying to AWS Lambda...
===================================
Deployment Complete! ✅
===================================
```

#### 方法B: 手動デプロイ

```bash
cd lambda/puzzle-register

# backendをコピー
cp -r ../../backend ./backend

# zipファイル作成
zip -r function.zip index.py backend/ requirements.txt

# デプロイ
aws lambda update-function-code \
  --function-name jigsaw-puzzle-dev-puzzle-register \
  --zip-file fileb://function.zip

# クリーンアップ
rm -rf backend
```

---

### Step 5: テスト

#### 5-1. API Gatewayエンドポイントの確認

```bash
cd terraform/environments/dev
terraform output puzzles_endpoint
```

出力例:
```
"https://abc123def.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles"
```

#### 5-2. API呼び出し

**リクエスト:**
```bash
curl -X POST https://YOUR_API_ID.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles \
  -H "Content-Type: application/json" \
  -d '{
    "pieceCount": 300,
    "fileName": "test-puzzle.jpg"
  }'
```

**期待されるレスポンス:**
```json
{
  "puzzleId": "abc-123-def-456",
  "uploadUrl": "https://jigsaw-puzzle-dev-images.s3.ap-northeast-1.amazonaws.com/puzzles/abc-123.jpg?X-Amz-Algorithm=...",
  "expiresIn": 300,
  "message": "Pre-signed URL generated successfully. Upload your image to this URL."
}
```

#### 5-3. DynamoDBデータ確認

```bash
# パズルが登録されたか確認
aws dynamodb scan --table-name jigsaw-puzzle-dev-puzzles
```

**出力例:**
```json
{
    "Items": [
        {
            "userId": {"S": "anonymous"},
            "puzzleId": {"S": "abc-123-def-456"},
            "pieceCount": {"N": "300"},
            "fileName": {"S": "test-puzzle.jpg"},
            "status": {"S": "pending"},
            "createdAt": {"S": "2025-01-15T10:30:00.000Z"}
        }
    ],
    "Count": 1
}
```

#### 5-4. CloudWatch Logsで動作確認

```bash
# Lambda関数のログを表示
aws logs tail /aws/lambda/jigsaw-puzzle-dev-puzzle-register --follow
```

---

## トラブルシューティング

### エラー1: terraform init でエラー

```
Error: Failed to query available provider packages
```

**解決方法:**
```bash
rm -rf .terraform .terraform.lock.hcl
terraform init
```

---

### エラー2: terraform apply でS3バケット名が重複

```
Error: creating S3 Bucket: BucketAlreadyExists
```

**原因:** S3バケット名は全世界で一意である必要がある

**解決方法:**
```bash
# terraform/environments/dev/variables.tf を編集
variable "project_name" {
  default     = "jigsaw-puzzle-YOUR-NAME"  # YOUR-NAMEを自分の名前に変更
}
```

---

### エラー3: Lambda関数でImportError

```
ImportError: cannot import name 'PuzzleService' from 'puzzle_logic'
```

**原因:** `backend/` ディレクトリがzipに含まれていない

**解決方法:**
```bash
cd lambda/puzzle-register
rm -rf backend function.zip
cp -r ../../backend ./backend
zip -r function.zip index.py backend/
aws lambda update-function-code --function-name jigsaw-puzzle-dev-puzzle-register --zip-file fileb://function.zip
rm -rf backend
```

---

### エラー4: API呼び出しで403エラー

```
{"message":"Missing Authentication Token"}
```

**原因:** URLが間違っている、またはAPI Gatewayのデプロイが完了していない

**解決方法:**
```bash
# 正しいURLを確認
terraform output puzzles_endpoint

# API Gatewayを再デプロイ
cd terraform/environments/dev
terraform apply -auto-approve
```

---

### エラー5: API呼び出しで500エラー

```
{"message": "Internal server error"}
```

**原因:** Lambda関数のエラー

**解決方法:**
```bash
# CloudWatch Logsでエラーを確認
aws logs tail /aws/lambda/jigsaw-puzzle-dev-puzzle-register --follow

# エラー内容を確認して修正
# 例: 環境変数が正しく設定されているか
aws lambda get-function-configuration --function-name jigsaw-puzzle-dev-puzzle-register
```

---

## デプロイ後の確認チェックリスト

- [ ] `terraform apply` が成功した
- [ ] Lambda関数コードがデプロイされた
- [ ] API呼び出しで200レスポンスが返る
- [ ] DynamoDBにデータが保存される
- [ ] CloudWatch Logsにログが出力される

---

## リソースの削除（必要な場合）

**警告:** 全てのデータが削除されます。

```bash
cd terraform/environments/dev
terraform destroy
```

プロンプトで `yes` と入力

**所要時間:** 3-5分

---

## 次のステップ

Phase 2のデプロイが完了したら:

1. **ローカル開発を試す**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app:app --reload
   # http://localhost:8000/docs にアクセス
   ```

2. **Phase 3へ進む**
   - 画像処理機能の実装
   - S3イベントトリガーの設定

3. **フロントエンド開発**
   - React/Vue.jsでUIを作成
   - APIを呼び出す実装

---

## 参考コマンド

### Terraformの状態確認

```bash
# リソース一覧
terraform state list

# 特定のリソースの詳細
terraform state show module.s3.aws_s3_bucket.images
```

### AWS CLIでリソース確認

```bash
# S3バケット一覧
aws s3 ls

# DynamoDBテーブル一覧
aws dynamodb list-tables

# Lambda関数一覧
aws lambda list-functions

# API Gateway一覧
aws apigateway get-rest-apis
```

### ログの確認

```bash
# Lambda関数のログ
aws logs tail /aws/lambda/jigsaw-puzzle-dev-puzzle-register --follow

# API Gatewayのログ
aws logs tail /aws/api-gateway/jigsaw-puzzle-dev --follow
```

---

## 完了！

Phase 2のデプロイが完了しました。

APIエンドポイント: `https://YOUR_API_ID.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles`

このエンドポイントにPOSTリクエストを送信することで、パズルを登録できます。
