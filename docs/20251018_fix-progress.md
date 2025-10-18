# 修正進捗管理

最終更新: 2025-10-18

## 📋 進捗サマリー

- **Total**: 70+ 件
- **完了**: 1 件
- **進行中**: 0 件
- **未着手**: 69+ 件

---

## 🚨 Phase 1: セキュリティ基盤（最優先）

### 今すぐ実施（所要時間: 2時間）

- [x] **1.1 CORS設定を環境変数化** (30分) ✅ 2025-10-18 完了
  - ファイル: `backend/app.py`, `lambda/puzzle-register/index.py`, `terraform/`
  - 参照: [code-review.md#12-cors設定]
  - 変更内容:
    - `backend/app.py`: ALLOWED_ORIGINS環境変数を追加
    - `lambda/puzzle-register/index.py`: ALLOWED_ORIGINS環境変数を追加
    - `terraform/modules/lambda/`: allowed_origins変数を追加
    - `terraform/environments/dev/variables.tf`: デフォルトを["http://localhost:3000"]に変更
    - `backend/.env.example`: ALLOWED_ORIGINS追加
    - `README.md`: 環境変数の説明を追加

- [ ] **1.2 エラー情報露出の防止** (30分)
  - ファイル: `backend/app.py`, `lambda/puzzle-register/index.py`
  - 参照: [code-review.md#13-エラー情報の露出]

- [ ] **1.3 構造化ログの導入** (1時間)
  - ファイル: `backend/app.py`, `backend/puzzle_logic.py`, `lambda/puzzle-register/index.py`
  - 参照: [code-review.md#31-ログ管理]

### 今週中に実施（所要時間: 3時間）

- [ ] **1.4 Input validationの強化** (1時間)
  - ファイル: `backend/schemas.py`
  - 参照: [code-review.md#14-input-validation]

- [ ] **1.5 Pre-signed URLの有効期限短縮** (15分)
  - ファイル: `backend/puzzle_logic.py`
  - 参照: [code-review.md#15-pre-signed-urlの有効期限]

- [ ] **1.6 Rate Limitingの実装** (2時間)
  - ファイル: API Gateway設定, Lambda
  - 参照: [code-review.md#16-rate-limiting]

---

## 🔴 Phase 2: 認証・認可（2-3週間）

- [ ] **2.1 AWS Cognitoのセットアップ** (4時間)
  - Terraform設定の追加
  - 参照: [code-review.md#11-認証認可]

- [ ] **2.2 フロントエンドにログイン機能追加** (8時間)
  - 新規ページ: `Login.tsx`, `Register.tsx`
  - AWS Amplify ライブラリの導入

- [ ] **2.3 API Gatewayに認証追加** (4時間)
  - Cognito Authorizer の設定
  - Terraform更新

- [ ] **2.4 Lambda Authorizerの実装** (4時間)
  - カスタム認証ロジック

---

## 🟡 Phase 3: テスト・CI/CD（2-3週間）

### バックエンドテスト

- [ ] **3.1 pytestセットアップ** (2時間)
  - `backend/tests/` ディレクトリ構成
  - pytest.ini, conftest.py

- [ ] **3.2 puzzle_logicの単体テスト** (4時間)
  - `test_puzzle_logic.py`
  - motoでAWSモック

- [ ] **3.3 schemasのバリデーションテスト** (2時間)
  - `test_schemas.py`

- [ ] **3.4 APIの統合テスト** (4時間)
  - `test_api.py`
  - FastAPI TestClient使用

### フロントエンドテスト

- [ ] **3.5 Vitest/Jestセットアップ** (2時間)
  - テスト設定ファイル

- [ ] **3.6 コンポーネントの単体テスト** (6時間)
  - PuzzleList.test.tsx
  - PuzzleCreate.test.tsx

### CI/CD

- [ ] **3.7 GitHub Actionsセットアップ** (4時間)
  - `.github/workflows/ci.yml`
  - テスト自動実行

- [ ] **3.8 デプロイ自動化** (4時間)
  - `.github/workflows/deploy.yml`

- [ ] **3.9 E2Eテスト** (8時間)
  - Playwright導入
  - 主要フロー

---

## 🟢 Phase 4: パフォーマンス最適化（2-3週間）

- [ ] **4.1 ページネーションの実装** (4時間)
  - バックエンド: `puzzle_logic.py`
  - フロントエンド: `PuzzleList.tsx`
  - 参照: [code-review.md#21-ページネーション]

- [ ] **4.2 画像最適化Lambdaの追加** (8時間)
  - 新規Lambda関数
  - Pillowでリサイズ
  - 参照: [code-review.md#22-画像最適化]

- [ ] **4.3 CloudFront CDNの設定** (4時間)
  - Terraform設定
  - カスタムドメイン
  - 参照: [code-review.md#23-cdn]

- [ ] **4.4 Lambda Layerの導入** (3時間)
  - boto3をLayerに分離
  - 参照: [code-review.md#24-lambda-cold-start]

- [ ] **4.5 DynamoDB GSIの活用** (2時間)
  - CreatedAtIndexの使用
  - 参照: [code-review.md#25-dynamodbの最適化]

---

## 🔵 Phase 5: 監視・運用（1-2週間）

- [ ] **5.1 CloudWatch Alarmsの設定** (3時間)
  - Lambda errors
  - API Gateway 4xx/5xx
  - DynamoDB throttles
  - 参照: [code-review.md#53-モニタリング]

- [ ] **5.2 SNSでアラート通知** (1時間)
  - SNS Topic作成
  - メール/Slack通知

- [ ] **5.3 デプロイスクリプトの改善** (3時間)
  - エラーハンドリング
  - バックアップ機能
  - ヘルスチェック
  - 参照: [code-review.md#51-デプロイスクリプト]

- [ ] **5.4 ロールバック手順の整備** (2時間)
  - ドキュメント作成
  - スクリプト実装

---

## 🛠️ Phase 6: コード品質改善（継続的）

### 保守性

- [ ] **6.1 環境変数管理の改善** (2時間)
  - pydantic-settings導入
  - 参照: [code-review.md#32-環境変数管理]

- [ ] **6.2 エラーハンドリングの一貫性** (2時間)
  - 参照: [code-review.md#33-エラーハンドリングの一貫性]

- [ ] **6.3 未使用コードの削除** (1時間)
  - PIECES_TABLE_NAMEの整理
  - 参照: [code-review.md#34-未使用コード]

- [ ] **6.4 型チェックの強化** (2時間)
  - mypy設定
  - TypeScript strict mode
  - 参照: [code-review.md#43-型チェック]

### フロントエンド

- [ ] **6.5 スタイリングの改善** (4時間)
  - CSS Modules導入
  - インラインスタイル削減
  - 参照: [code-review.md#61-スタイリング]

- [ ] **6.6 エラーハンドリング改善** (2時間)
  - 参照: [code-review.md#62-エラーハンドリング]

- [ ] **6.7 状態管理の改善** (6時間)
  - React Query導入検討
  - 参照: [code-review.md#63-状態管理]

### アーキテクチャ

- [ ] **6.8 型定義の一貫性** (3時間)
  - snake_case/camelCase変換レイヤー
  - 参照: [code-review.md#7-型定義の一貫性]

- [ ] **6.9 Lambda設定の改善** (2時間)
  - DLQ追加
  - X-Ray トレーシング
  - 同時実行数制限
  - 参照: [code-review.md#52-lambdaの設定]

- [ ] **6.10 DynamoDB TTLの実装** (1時間)
  - expiresAt属性の設定
  - 参照: [code-review.md#54-dynamodb-ttl]

---

## 📝 修正履歴

### 2025-10-18
- fix-progress.md を作成
- レビュー完了、修正開始準備完了

---

## 次のアクション

**今から始める項目:**
1. ✅ CORS設定を環境変数化（30分）

**準備が必要な項目:**
- AWS Cognito（Phase 2で実施）
- テストフレームワーク（Phase 3で実施）
