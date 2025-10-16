# Jigsaw Puzzle Terraform Infrastructure

このディレクトリには、ジグソーパズル支援システムのAWSインフラをTerraformで管理するための設定が含まれています。

## ディレクトリ構造

```
terraform/
├── modules/              # 再利用可能なモジュール
│   ├── s3/              # S3バケット
│   ├── dynamodb/        # DynamoDBテーブル
│   ├── iam/             # IAMロール・ポリシー
│   ├── lambda/          # Lambda関数（今後追加）
│   └── api-gateway/     # API Gateway（今後追加）
├── environments/        # 環境ごとの設定
│   └── dev/            # 開発環境
└── .gitignore
```

## セットアップ

### 前提条件

- Terraform >= 1.5.0
- AWS CLI設定済み
- 適切なAWS認証情報

### 初期化

```bash
cd terraform/environments/dev
terraform init
```

### プラン確認

```bash
terraform plan
```

### リソース作成

```bash
terraform apply
```

### リソース削除

```bash
terraform destroy
```

## モジュール説明

### S3モジュール

画像保存用のS3バケットを作成します。

**機能:**
- バージョニング有効化
- サーバーサイド暗号化（AES256）
- パブリックアクセスブロック
- ライフサイクルルール（一時ファイル7日後削除、古いファイルGlacier移行）
- CORS設定

### DynamoDBモジュール

パズルとピースの情報を保存するDynamoDBテーブルを作成します。

**Puzzlesテーブル:**
- PK: userId
- SK: puzzleId
- GSI: CreatedAtIndex（作成日時での検索用）

**Piecesテーブル:**
- PK: puzzleId
- SK: pieceId
- GSI: MatchedIndex（マッチ済み/未マッチの検索用）

**機能:**
- Pay-per-requestモード（従量課金）
- ポイントインタイムリカバリ有効
- 暗号化有効
- TTL有効（自動削除）

### IAMモジュール

Lambda関数が必要なAWSリソースにアクセスするためのIAMロール・ポリシーを作成します。

**権限:**
- CloudWatch Logsへの書き込み
- S3バケットへの読み書き
- DynamoDBテーブルへのCRUD操作
- Amazon Rekognitionの使用

## 出力

`terraform apply`後、以下の情報が出力されます：

```
s3_bucket_name           = "jigsaw-puzzle-dev-images"
puzzles_table_name       = "jigsaw-puzzle-dev-puzzles"
pieces_table_name        = "jigsaw-puzzle-dev-pieces"
lambda_execution_role_arn = "arn:aws:iam::xxxx:role/..."
```

## カスタマイズ

### 変数の変更

`terraform/environments/dev/variables.tf`を編集するか、`terraform.tfvars`ファイルを作成して変数を上書きできます。

```hcl
# terraform.tfvars の例
aws_region   = "us-east-1"
project_name = "my-puzzle-app"
```

### 新しい環境の追加

```bash
cp -r environments/dev environments/staging
cd environments/staging
# variables.tf を編集して環境名を変更
terraform init
terraform apply
```

## トラブルシューティング

### 初期化エラー

```bash
rm -rf .terraform
terraform init
```

### バケット名の競合

S3バケット名はグローバルに一意である必要があります。`variables.tf`の`project_name`を変更してください。

### 権限エラー

AWS CLIが正しく設定されているか確認：

```bash
aws sts get-caller-identity
```

## 次のステップ

1. Lambda関数モジュールの追加
2. API Gatewayモジュールの追加
3. CloudFrontモジュールの追加
4. ステート管理のためのS3バックエンド設定
5. CI/CDパイプラインの構築
