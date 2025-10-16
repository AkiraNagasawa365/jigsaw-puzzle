# ジグソーパズル支援システム - システム設計書

## 概要

Web上でジグソーパズルを登録し、ピース画像をアップロードすることで該当ピースの位置を特定できるシステム。
全てAWSサービスで構築する。

## システムの全体構成

### 1. パズル登録フェーズ

- ユーザーがパズルの完成画像をアップロード
- 画像をS3に保存
- Lambda + Amazon Rekognitionで画像を分析
- パズルのピース数（例: 300ピース、1000ピースなど）を入力
- 画像をグリッド分割してピース位置マップを生成
- DynamoDBにパズル情報を保存（パズルID、画像URL、ピース情報）

### 2. ピース照合フェーズ

- ユーザーが手元のピースを撮影してアップロード
- S3にピース画像を一時保存
- Lambda関数が起動
- Amazon Rekognition / SageMakerで画像特徴抽出
- 登録済みパズルのピース情報と照合
- 類似度スコアでマッチング
- どの位置のピースか特定して結果を返却

### 3. フロントエンド

- S3 + CloudFrontで静的Webホスティング
- React/Vue.jsなどでSPA
- API Gateway + Lambdaでバックエンド接続
- パズルの進行状況を可視化（どのピースが配置済みか）

## AWSアーキテクチャ

```
ユーザー
  ↓
CloudFront + S3 (フロントエンド)
  ↓
API Gateway (REST/HTTP API)
  ↓
Lambda関数群
  ├─ パズル登録処理
  ├─ ピース照合処理
  └─ 進行状況管理
  ↓
├─ S3 (画像ストレージ)
├─ DynamoDB (メタデータ・ピース情報)
├─ Rekognition / SageMaker (画像分析)
└─ Cognito (ユーザー認証・オプション)
```

## 使用するAWSサービス

| サービス | 用途 |
|---------|------|
| S3 | 画像ストレージ、静的サイトホスティング |
| CloudFront | CDN、フロントエンド配信 |
| API Gateway | RESTful API エンドポイント |
| Lambda | サーバーレスバックエンド処理 |
| DynamoDB | NoSQLデータベース（パズル・ピース情報） |
| Rekognition | 画像分析・特徴抽出 |
| SageMaker | 機械学習モデル（オプション） |
| Cognito | ユーザー認証・認可（オプション） |

## データベース設計（DynamoDB）

### Puzzlesテーブル

| 属性 | 型 | 説明 |
|------|-------|------|
| userId (PK) | String | ユーザーID |
| puzzleId (SK) | String | パズル固有ID |
| imageUrl | String | S3画像URL |
| pieceCount | Number | ピース数 |
| createdAt | String | 作成日時 |
| status | String | ステータス（active/completed） |

### Piecesテーブル

| 属性 | 型 | 説明 |
|------|-------|------|
| puzzleId (PK) | String | パズルID |
| pieceId (SK) | String | ピースID |
| position | Map | 位置情報 {x: Number, y: Number} |
| imageFeatures | Binary/String | 画像特徴ベクトル |
| matched | Boolean | 配置済みフラグ |
| placedAt | String | 配置日時 |

## 処理フロー

### パズル登録フロー

1. フロントエンド → API Gateway → Lambda (Upload URL生成)
2. クライアントがS3に直接アップロード (Pre-signed URL使用)
3. S3イベントトリガー → Lambda (画像処理開始)
4. Lambdaで画像をグリッド分割
5. Rekognitionで各ピースの特徴抽出
6. DynamoDBにパズル・ピース情報を保存
7. 処理完了を返却

### ピース照合フロー

1. ピース画像をアップロード (Pre-signed URL使用)
2. S3イベント or 直接Lambda起動
3. Rekognitionで特徴抽出
4. DynamoDBから該当パズルの全ピース情報を取得
5. 類似度計算（コサイン類似度など）
6. 最も類似度が高いピース位置を返却
7. フロントエンドで位置を表示

### 進行状況管理フロー

1. API Gateway → Lambda
2. DynamoDBから特定パズルのピース配置状況を取得
3. 配置済み/未配置のマップを生成
4. フロントエンドで可視化

## API設計

### パズル登録

```
POST /api/puzzles
Request:
{
  "pieceCount": 300,
  "fileName": "puzzle.jpg"
}
Response:
{
  "puzzleId": "uuid",
  "uploadUrl": "s3-presigned-url"
}
```

### ピース照合

```
POST /api/puzzles/{puzzleId}/match
Request:
{
  "pieceImageUrl": "s3-url"
}
Response:
{
  "pieceId": "uuid",
  "position": {"x": 5, "y": 3},
  "confidence": 0.95
}
```

### 進行状況取得

```
GET /api/puzzles/{puzzleId}/progress
Response:
{
  "puzzleId": "uuid",
  "totalPieces": 300,
  "matchedPieces": 45,
  "progress": 15.0,
  "pieces": [...]
}
```

## コスト最適化ポイント

- **Lambda**: 必要時のみ実行（サーバーレス）、実行時間を最小化
- **S3**: ライフサイクルポリシーで古い画像を自動削除（30日後など）
- **DynamoDB**: オンデマンドモードで小規模運用、必要に応じてプロビジョニング
- **CloudFront**: キャッシュ活用でS3リクエストを削減
- **Rekognition**: API呼び出し回数を最小化、キャッシュ活用

## セキュリティ考慮事項

- **API Gateway**: API Keyまたはカスタムオーソライザーで認証
- **S3**: バケットポリシーで適切なアクセス制御
- **Lambda**: 最小権限のIAMロール
- **DynamoDB**: 暗号化有効化
- **Cognito**: ユーザー認証・認可（必要に応じて）

## 拡張可能性

- リアルタイム協業機能（WebSocket via API Gateway）
- ヒント機能（似たピースの候補表示）
- SNSシェア機能
- パズル完成度ランキング
- AR機能（実際のテーブル上にピース位置を投影）

## 技術的課題

1. **画像特徴抽出の精度**: Rekognitionの限界、カスタムモデルの必要性
2. **ピース照合の速度**: 大量ピース（1000+）での検索最適化
3. **画像の歪み補正**: 斜めから撮影された場合の補正
4. **ピース形状の考慮**: 凹凸パターンの認識
5. **照明条件の違い**: 登録時と照合時の照明差異

## 実装優先順位

### Phase 1: MVP
- パズル登録機能
- シンプルなピース照合（グリッドベース）
- 基本的なフロントエンド

### Phase 2: 精度向上
- Rekognition統合
- 類似度アルゴリズム改善
- UI/UX改善

### Phase 3: 拡張機能
- 進行状況管理
- 複数パズル管理
- ユーザー認証

## 参考技術

- AWS Rekognition Image Analysis
- OpenCV（Lambda Layerで使用可能）
- Feature Matching Algorithms (SIFT, ORB)
- コサイン類似度、ユークリッド距離
