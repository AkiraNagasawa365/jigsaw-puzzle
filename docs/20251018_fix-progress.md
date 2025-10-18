# 修正進捗管理

最終更新: 2025-10-19

## 📋 進捗サマリー

- **Total**: 70+ 件
- **完了**: 5 件 (✅ CORS環境変数化、エラー情報露出防止、構造化ログ導入、CloudFront構築、ディレクトリ構造リファクタリング)
- **進行中**: 0 件
- **未着手**: 65+ 件

## ⚠️ 重要な構造変更

**バックエンドのディレクトリ構造が大幅に変更されました:**
- `backend/app.py` → `backend/app/api/main.py`
- `backend/puzzle_logic.py` → `backend/app/services/puzzle_service.py`
- `backend/schemas.py` → `backend/app/core/schemas.py`
- 新規: `backend/app/core/config.py` (環境変数の一元管理)
- 新規: `backend/app/core/logger.py` (構造化ログ設定) ✅ 2025-10-19
- 新規: `backend/app/api/routes/puzzles.py` (ルート定義)

**フロントエンドも機能別フォルダ構造に移行:**
- `frontend/src/pages/` → `frontend/src/pages/puzzles/` (パズル関連ページ)

---

## 🚨 Phase 1: セキュリティ基盤（最優先）

### 今すぐ実施（所要時間: 2時間）

- [x] **1.1 CORS設定を環境変数化** (30分) ✅ 2025-10-18 完了
  - ファイル: `backend/app/api/main.py`, `backend/app/core/config.py`, `lambda/puzzle-register/index.py`, `terraform/`
  - 参照: [code-review.md#12-cors設定]
  - 変更内容:
    - `backend/app/core/config.py`: Settings クラスで ALLOWED_ORIGINS を環境変数から読み込み
    - `backend/app/api/main.py`: settings.allowed_origins を使用したCORS設定
    - `lambda/puzzle-register/index.py`: 動的CORS実装（リクエストOriginベース）
    - `terraform/modules/lambda/`: allowed_origins変数を追加
    - `terraform/environments/dev/variables.tf`: 複数オリジン対応（localhost:3000, 5173, CloudFront）
    - `backend/.env.example`: ALLOWED_ORIGINS追加（デフォルト: localhost:3000,5173）
    - `README.md`: 環境変数の説明を追加

- [x] **1.2 エラー情報露出の防止** (30分) ✅ 2025-10-19 完了
  - ファイル: `backend/app/api/routes/puzzles.py`, `lambda/puzzle-register/index.py`
  - 参照: [code-review.md#13-エラー情報の露出]
  - 変更内容:
    - `backend/app/api/routes/puzzles.py`: 本番環境で `settings.is_production` チェック、エラー詳細を隠す
    - `lambda/puzzle-register/index.py`: 同様に ENVIRONMENT 環境変数で制御
    - 開発環境: エラー詳細を返す
    - 本番環境: "Internal server error" のみ返す

- [x] **1.3 構造化ログの導入** (1時間) ✅ 2025-10-19 完了
  - ファイル: `backend/app/core/logger.py` (新規), `backend/app/services/puzzle_service.py`, `backend/app/api/routes/puzzles.py`, `lambda/puzzle-register/index.py`
  - 参照: [code-review.md#31-ログ管理]
  - 変更内容:
    - `backend/app/core/logger.py`: 構造化ログモジュール作成
      - `JSONFormatter`: CloudWatch Logs向けJSON形式出力
      - `setup_logger()`: 環境に応じたロガー初期化（dev: 人間が読みやすい形式、prod: JSON形式）
      - ログレベル: 環境変数 `LOG_LEVEL` で制御（デフォルト: INFO）
    - `backend/app/services/puzzle_service.py`: 全ての `print()` を `logger.info/error()` に置き換え
      - コンテキスト情報追加: puzzle_id, user_id, piece_count, error など
    - `backend/app/api/routes/puzzles.py`: エラーハンドリングで構造化ログ追加
    - `lambda/puzzle-register/index.py`: Lambda関数でも同じロガーを使用
      - Lambda invocation, validation error, unexpected error のログ追加
      - request_id をログに含める
    - 動作確認:
      - 開発環境: `2025-10-19 03:40:25 [INFO] app.services.puzzle_service - Created puzzle successfully`
      - 本番環境: `{"timestamp": "2025-10-18T18:39:26.843024Z", "level": "INFO", "logger": "test", "message": "Production log test", "puzzle_id": "test-123", "user_id": "test-user"}`

### 今週中に実施（所要時間: 3時間）

- [ ] **1.4 Input validationの強化** (1時間)
  - ファイル: `backend/app/core/schemas.py`
  - 参照: [code-review.md#14-input-validation]
  - 現状: Pydanticによる基本的なバリデーション実装済み
    - `pieceCount`: ge=100, le=2000
    - `puzzleName`: min_length=1, max_length=100
  - 追加検討項目:
    - ファイル名のサニタイゼーション（パストラバーサル対策）
    - pieceCount を有効な値リスト [100, 300, 500, 1000, 2000] に限定
    - ファイルサイズ制限の明示化
    - 画像形式のバリデーション（MIME typeチェック）

- [ ] **1.5 Pre-signed URLの有効期限短縮** (15分)
  - ファイル: `backend/app/services/puzzle_service.py`
  - 参照: [code-review.md#15-pre-signed-urlの有効期限]
  - 現状: `ExpiresIn=3600` (1時間)
  - 推奨: `ExpiresIn=900` (15分) または `ExpiresIn=300` (5分)
  - 変更箇所: `puzzle_service.py` の `generate_presigned_url()` メソッド

- [ ] **1.6 Rate Limitingの実装** (2時間)
  - ファイル: `terraform/modules/api_gateway/` (Terraform設定)
  - 参照: [code-review.md#16-rate-limiting]
  - 必要な作業:
    - API Gateway Usage Plan作成
    - Throttle設定（例: 100リクエスト/秒、バースト200）
    - Quota設定（例: 10,000リクエスト/日）
    - API Keyの発行と管理

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
  - バックエンド: `backend/app/services/puzzle_service.py`
  - フロントエンド: `frontend/src/components/PuzzleList.tsx`
  - 参照: [code-review.md#21-ページネーション]
  - 必要な作業:
    - DynamoDB クエリに `Limit` と `LastEvaluatedKey` を追加
    - フロントエンドでページネーションUIを実装

- [ ] **4.2 画像最適化Lambdaの追加** (8時間)
  - 新規Lambda関数作成
  - Pillowライブラリでリサイズ・圧縮
  - 参照: [code-review.md#22-画像最適化]
  - 必要な作業:
    - S3イベントトリガーの設定
    - サムネイル生成（複数サイズ）
    - WebP変換の検討

- [x] **4.3 CloudFront CDNの設定** (4時間) ✅ 2025-10-18 完了
  - Terraform設定: `terraform/modules/frontend/`
  - カスタムドメイン: 未設定（将来対応）
  - 参照: [code-review.md#23-cdn]
  - 変更内容:
    - CloudFront Distribution作成
    - S3 OAC (Origin Access Control) 設定
    - デプロイスクリプト作成: `scripts/deploy-frontend.sh`
    - 本番URL: https://dykwhpbm0bhdv.cloudfront.net
    - キャッシュ設定: 静的ファイル1年、index.html無キャッシュ

- [ ] **4.4 Lambda Layerの導入** (3時間)
  - boto3をLayerに分離
  - 参照: [code-review.md#24-lambda-cold-start]
  - 必要な作業:
    - Lambda Layer作成（共通ライブラリ）
    - デプロイパッケージサイズ削減

- [ ] **4.5 DynamoDB GSIの活用** (2時間)
  - CreatedAtIndexの使用
  - 参照: [code-review.md#25-dynamodbの最適化]
  - 必要な作業:
    - GSI作成（Terraformで定義）
    - ソート順での取得（新しい順）

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
  - ファイル: `backend/app/core/config.py`
  - pydantic-settings導入（オプション）
  - 参照: [code-review.md#32-環境変数管理]
  - 現状: 独自Settingsクラスで実装済み
  - 改善余地: pydantic-settingsでより厳密な型チェック

- [ ] **6.2 エラーハンドリングの一貫性** (2時間)
  - ファイル: `backend/app/api/routes/puzzles.py`, `backend/app/services/puzzle_service.py`
  - 参照: [code-review.md#33-エラーハンドリングの一貫性]
  - 必要な作業:
    - カスタム例外クラスの定義
    - 例外ハンドラーの統一
    - エラーレスポンス形式の標準化

- [ ] **6.3 未使用コードの削除** (1時間)
  - ファイル: `backend/app/core/config.py`, `backend/app/services/puzzle_service.py`
  - PIECES_TABLE_NAMEの整理（現在未使用）
  - 参照: [code-review.md#34-未使用コード]
  - 検討: 将来のピース処理機能で使用予定か確認

- [ ] **6.4 型チェックの強化** (2時間)
  - バックエンド: mypy設定追加
  - フロントエンド: TypeScript strict mode有効化
  - 参照: [code-review.md#43-型チェック]
  - 必要な作業:
    - `pyproject.toml` にmypy設定追加
    - `tsconfig.json` の strict: true 設定

### フロントエンド

- [ ] **6.5 スタイリングの改善** (4時間)
  - ファイル: `frontend/src/pages/puzzles/*.tsx`, `frontend/src/components/*.tsx`
  - CSS Modules または Tailwind CSS導入
  - インラインスタイル削減
  - 参照: [code-review.md#61-スタイリング]
  - 現状: 全てインラインスタイル

- [ ] **6.6 エラーハンドリング改善** (2時間)
  - ファイル: `frontend/src/components/PuzzleList.tsx`, `frontend/src/pages/puzzles/*.tsx`
  - 参照: [code-review.md#62-エラーハンドリング]
  - 必要な作業:
    - エラーバウンダリーの実装
    - トースト通知の追加
    - リトライ機能の実装

- [ ] **6.7 状態管理の改善** (6時間)
  - React Query (TanStack Query) 導入検討
  - 参照: [code-review.md#63-状態管理]
  - メリット:
    - サーバー状態のキャッシュ
    - 自動リフェッチ
    - ローディング・エラー状態の統一管理

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

### 2025-10-19
- **大規模リファクタリング完了**
  - バックエンド構造変更: `backend/app.py` → `backend/app/` (機能別フォルダ構造)
  - フロントエンド構造変更: `pages/` → `pages/puzzles/` (機能別フォルダ構造)
  - 環境変数管理の一元化: `backend/app/core/config.py` 作成
  - RESTful API設計改善: `/users/{userId}/puzzles` エンドポイント追加
- **Phase 1 完了項目:**
  - 1.1 CORS設定を環境変数化 ✅
  - 1.2 エラー情報露出の防止 ✅
- **Phase 4 完了項目:**
  - 4.3 CloudFront CDN設定 ✅
- fix-progress.md を現在の実装に合わせて全面更新
  - 全てのファイルパスを更新
  - 現状分析を追加
  - 必要な作業を詳細化

### 2025-10-18
- fix-progress.md を作成
- レビュー完了、修正開始準備完了
- Phase 1.1 CORS設定完了

---

## 次のアクション

**すぐに着手できる項目（Phase 1 残り）:**
1. **1.3 構造化ログの導入** (1時間) - `print()` を `logging` モジュールに置き換え
2. **1.5 Pre-signed URLの有効期限短縮** (15分) - 3600秒 → 900秒に変更

**今週中に実施すべき項目:**
3. **1.4 Input validationの強化** (1時間) - Pydanticバリデーションの追加
4. **1.6 Rate Limitingの実装** (2時間) - API Gateway設定

**準備が必要な項目:**
- AWS Cognito（Phase 2で実施）
- テストフレームワーク（Phase 3で実施）
- 画像処理Lambda（Phase 4で実施）

**完了済み項目:**
- ✅ CORS環境変数化（Phase 1.1）
- ✅ エラー情報露出防止（Phase 1.2）
- ✅ CloudFront構築（Phase 4.3）
- ✅ ディレクトリ構造リファクタリング
