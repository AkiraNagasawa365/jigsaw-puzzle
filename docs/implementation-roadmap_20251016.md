# 実装ロードマップ

ジグソーパズル支援システムの実装順序と各ステップの詳細。

## 全体方針

**アプローチ: 最小機能で一気通貫（推奨）**

1つの機能（パズル登録）を完全に実装してから、次の機能に進む。
これにより、AWS全体の連携を早期に理解し、動くものを確認しながら学習できる。

---

## Phase 1: インフラ基盤構築 ✅

### 完了済み
- [x] Terraformディレクトリ構造作成
- [x] S3モジュール作成
- [x] DynamoDBモジュール作成
- [x] IAMモジュール作成
- [x] dev環境設定作成

### 次のステップ
```bash
cd terraform/environments/dev
terraform init
terraform apply
```

**確認事項:**
- S3バケットが作成されたか
- DynamoDBテーブル（Puzzles, Pieces）が作成されたか
- IAMロールが作成されたか

---

## Phase 2: バックエンド - パズル登録機能

### 目標
ユーザーがパズル画像をアップロードし、DynamoDBに登録できる機能を実装。

### 2-1. Lambdaモジュール作成（Terraform）

**作成ファイル:**
```
terraform/modules/lambda/
├── main.tf          # Lambda関数定義
├── variables.tf     # 変数定義
└── outputs.tf       # 出力定義
```

**実装内容:**
- Lambda関数リソース定義
- 環境変数設定（S3バケット名、DynamoDBテーブル名）
- CloudWatch Logsの設定
- IAMロールのアタッチ

### 2-2. Lambda関数コード実装

**作成ファイル:**
```
lambda/puzzle-register/
├── index.py（またはindex.js）
├── requirements.txt（Pythonの場合）
└── README.md
```

**実装内容:**
1. Pre-signed URLの生成
   - S3へのアップロード用URL生成
   - 有効期限設定（例: 5分）
2. DynamoDBへのパズル情報登録
   - puzzleId生成（UUID）
   - userId, createdAt, status等の保存

**APIレスポンス例:**
```json
{
  "puzzleId": "uuid",
  "uploadUrl": "https://s3-presigned-url",
  "expiresIn": 300
}
```

### 2-3. API Gatewayモジュール作成（Terraform）

**作成ファイル:**
```
terraform/modules/api-gateway/
├── main.tf
├── variables.tf
└── outputs.tf
```

**実装内容:**
- REST APIの作成
- `/puzzles` エンドポイント（POST）
- Lambda統合設定
- CORS設定
- デプロイステージ（dev）

### 2-4. dev環境への統合

**編集ファイル:**
```
terraform/environments/dev/main.tf
```

**追加内容:**
```hcl
module "lambda" {
  source = "../../modules/lambda"
  # ...
}

module "api_gateway" {
  source = "../../modules/api-gateway"
  # ...
}
```

### 2-5. デプロイとテスト

```bash
# Terraformでインフラ更新
cd terraform/environments/dev
terraform apply

# Lambda関数コードをパッケージング
cd ../../../lambda/puzzle-register
zip -r function.zip .

# Lambda関数コード更新
aws lambda update-function-code \
  --function-name jigsaw-puzzle-dev-puzzle-register \
  --zip-file fileb://function.zip

# APIテスト
curl -X POST https://xxx.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles \
  -H "Content-Type: application/json" \
  -d '{"pieceCount": 300, "fileName": "test.jpg"}'

# レスポンス確認
# CloudWatch Logsで動作確認
```

**確認事項:**
- API Gatewayエンドポイントにアクセスできるか
- Pre-signed URLが返されるか
- DynamoDBにレコードが保存されるか

---

## Phase 3: バックエンド - 画像処理

### 目標
S3にアップロードされた画像を自動で処理し、ピース情報を生成。

### 3-1. 画像処理Lambda関数作成

**作成ファイル:**
```
lambda/image-processor/
├── index.py
├── requirements.txt  # Pillow, boto3等
└── README.md
```

**実装内容:**
1. S3イベントトリガーで起動
2. 画像をダウンロード
3. グリッド分割（ピース数に応じて）
4. 各ピースの特徴抽出（簡易版: 色の平均値など）
5. DynamoDB Piecesテーブルに保存

### 3-2. S3イベント設定（Terraform）

**編集ファイル:**
```
terraform/modules/s3/main.tf
```

**追加内容:**
```hcl
resource "aws_s3_bucket_notification" "image_upload" {
  bucket = aws_s3_bucket.images.id

  lambda_function {
    lambda_function_arn = var.image_processor_lambda_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "puzzles/"
    filter_suffix       = ".jpg"
  }
}
```

### 3-3. テスト

```bash
# 画像をS3にアップロード
aws s3 cp test.jpg s3://bucket-name/puzzles/test-puzzle-id.jpg

# CloudWatch Logsで処理確認
aws logs tail /aws/lambda/image-processor --follow

# DynamoDB Piecesテーブル確認
aws dynamodb scan --table-name jigsaw-puzzle-dev-pieces
```

---

## Phase 4: バックエンド - ピース照合機能

### 目標
ユーザーがピース画像をアップロードすると、該当するピース位置を返す。

### 4-1. ピース照合Lambda関数作成

**作成ファイル:**
```
lambda/piece-matcher/
├── index.py
└── requirements.txt
```

**実装内容:**
1. ピース画像をS3から取得
2. 特徴抽出
3. DynamoDB Piecesテーブルから全ピースを取得
4. 類似度計算（コサイン類似度など）
5. 最も類似度が高いピースを返却

### 4-2. API Gateway エンドポイント追加

**エンドポイント:**
```
POST /puzzles/{puzzleId}/match
```

**実装:**
```hcl
# terraform/modules/api-gateway/main.tf に追加
resource "aws_api_gateway_resource" "match" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.puzzle.id
  path_part   = "match"
}
```

### 4-3. テスト

```bash
# ピース照合APIをテスト
curl -X POST https://xxx.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles/puzzle-id/match \
  -H "Content-Type: application/json" \
  -d '{"pieceImageUrl": "s3://bucket/pieces/piece.jpg"}'

# レスポンス例
# {
#   "pieceId": "uuid",
#   "position": {"x": 5, "y": 3},
#   "confidence": 0.95
# }
```

---

## Phase 5: フロントエンド - 最小構成

### 目標
Webブラウザでパズル登録とピース照合ができる最小限のUI。

### 5-1. フロントエンドプロジェクト作成

```bash
# Reactの場合
npx create-react-app frontend
cd frontend

# または Viteの場合
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

### 5-2. 画面構成

**最小構成（2画面）:**
1. パズル登録画面
   - 画像アップロード
   - ピース数入力
2. ピース照合画面
   - パズル選択
   - ピース画像アップロード
   - 結果表示（位置）

### 5-3. API接続

**作成ファイル:**
```
frontend/src/
├── api/
│   └── puzzleApi.js  # API呼び出しロジック
├── components/
│   ├── PuzzleUpload.jsx
│   └── PieceMatch.jsx
└── App.jsx
```

### 5-4. ローカルテスト

```bash
npm start
# http://localhost:3000 でアクセス
```

**確認事項:**
- パズル画像をアップロードできるか
- Pre-signed URLでS3にアップロードできるか
- ピース照合ができるか

---

## Phase 6: フロントエンド配信（CloudFront + S3）

### 6-1. CloudFrontモジュール作成

**作成ファイル:**
```
terraform/modules/cloudfront/
├── main.tf
├── variables.tf
└── outputs.tf
```

### 6-2. フロントエンドビルド＆デプロイ

```bash
# ビルド
cd frontend
npm run build

# S3にアップロード
aws s3 sync dist/ s3://jigsaw-puzzle-dev-frontend/

# CloudFrontキャッシュ削除
aws cloudfront create-invalidation \
  --distribution-id DISTRIBUTION_ID \
  --paths "/*"
```

### 6-3. 動作確認

```
https://xxx.cloudfront.net
```

---

## Phase 7: 高度な機能追加

### オプション機能（優先度順）

#### 1. Amazon Rekognition統合
- Lambda関数でRekognition APIを使用
- 画像特徴抽出の精度向上

#### 2. 進行状況管理
- 配置済みピースの可視化
- 進捗率の表示

#### 3. ユーザー認証（Cognito）
- ユーザー登録・ログイン
- 個人のパズル管理

#### 4. リアルタイム更新（WebSocket）
- API Gateway WebSocket
- 複数人での協業

#### 5. モバイル対応
- レスポンシブデザイン
- PWA化

---

## 実装の推奨順序まとめ

```
✅ Phase 1: インフラ基盤構築（完了）
   ↓
⭐ Phase 2: パズル登録API（次はこれ）
   ↓
Phase 3: 画像処理
   ↓
Phase 4: ピース照合API
   ↓
Phase 5: フロントエンド最小構成
   ↓
Phase 6: フロントエンド配信
   ↓
Phase 7: 高度な機能追加
```

---

## 各Phaseの所要時間目安

| Phase | 内容 | 所要時間 |
|-------|------|---------|
| Phase 1 | インフラ基盤 | 完了 |
| Phase 2 | パズル登録API | 2-3時間 |
| Phase 3 | 画像処理 | 3-4時間 |
| Phase 4 | ピース照合API | 2-3時間 |
| Phase 5 | フロントエンド | 4-6時間 |
| Phase 6 | 配信環境 | 1-2時間 |
| Phase 7 | 高度な機能 | 各2-4時間 |

**合計: 約15-20時間**（学習時間を含む）

---

## 学習のポイント

### Phase 2-4（バックエンド）で学べること
- Lambda関数の実装
- API Gatewayの設定
- DynamoDBの操作
- S3の操作
- IAM権限管理
- CloudWatch Logsでのデバッグ
- サーバーレスアーキテクチャの理解

### Phase 5-6（フロントエンド）で学べること
- S3静的サイトホスティング
- CloudFrontの設定
- CORS対応
- Pre-signed URLの使用
- REST API呼び出し

### Phase 7（高度な機能）で学べること
- Rekognitionの使用
- Cognitoでの認証
- WebSocketリアルタイム通信
- 大規模データ処理

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. Lambda関数がタイムアウトする
- タイムアウト時間を延長（デフォルト3秒 → 30秒など）
- メモリを増やす（128MB → 512MB）

#### 2. CORSエラー
- API GatewayでCORS設定を確認
- LambdaレスポンスヘッダーにAccess-Control-Allow-Originを追加

#### 3. IAM権限エラー
- CloudWatch Logsでエラー確認
- IAMポリシーに必要な権限を追加

#### 4. DynamoDBでデータが見つからない
- テーブル名が正しいか確認
- キー構造が正しいか確認（PK/SK）

---

## 次のアクション

1. **terraform apply 実行**
2. **Phase 2開始: Lambdaモジュール作成**

準備ができたら教えてください！
