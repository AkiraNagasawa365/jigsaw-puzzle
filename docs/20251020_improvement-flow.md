# システム改善フロー（2025年10月版）

最終更新: 2025-10-20

## 📊 現在のシステム状態

### ✅ 完了済み（基盤構築フェーズ）

**アーキテクチャ基盤:**
- ✅ デュアルバックエンドアーキテクチャ（FastAPI + Lambda）
- ✅ 機能別ディレクトリ構造（backend/app/, frontend/src/）
- ✅ 環境変数の一元管理（config.py）
- ✅ 構造化ロギング（JSON形式、CloudWatch対応）
- ✅ Terraform IaC（S3, DynamoDB, Lambda, API Gateway, CloudFront）

**セキュリティ基盤:**
- ✅ CORS設定の環境変数化（開発/本番環境対応）
- ✅ エラー情報の適切な露出制御（本番環境では詳細を隠蔽）
- ✅ Input validation強化（XSS対策、パストラバーサル対策）
- ✅ Pre-signed URL有効期限短縮（15分）

**テスト基盤:**
- ✅ pytest環境構築（カバレッジ80%基準）
- ✅ 単体テスト実装（schemas.py: 38テスト、puzzle_service.py: 22テスト）
- ✅ セキュリティテスト（XSS、パストラバーサル）
- ✅ 総カバレッジ100%達成（コアモジュール）

**インフラ:**
- ✅ CloudFront CDN配信（本番URL: https://dykwhpbm0bhdv.cloudfront.net）
- ✅ S3 + OAC（Origin Access Control）
- ✅ デプロイスクリプト（Lambda, Frontend）

### 🚧 実装済みだが改善余地あり

**認証・認可:**
- 現状: 未実装（anonymous ユーザーで動作）
- 影響: セキュリティリスク高、本番利用不可
- 優先度: **高**

**パフォーマンス:**
- ページネーション: 未実装（全件取得）
- 画像最適化: 未実装（アップロードされたままのサイズ）
- Lambda最適化: 基本設定のみ（レイヤー未使用、Cold Start対策なし）

**監視・運用:**
- CloudWatch Logs: 基本ログのみ
- アラート: 未設定
- メトリクス: 未収集

**コード品質:**
- 型チェック: 部分的（TypeScript strict mode未有効、mypy未導入）
- エラーハンドリング: 基本的だが一貫性に欠ける
- フロントエンド: インラインスタイルのみ、状態管理が簡易的

## 🎯 改善フローの優先順位（再評価）

現在のシステムは**基盤構築フェーズを完了**し、**実用化フェーズ**に入っています。
以下の優先順位で改善を進めます。

---

## 🔴 Phase A: 実用化に必須（最優先）

**目標: システムを本番環境で安全に運用できる状態にする**

### A1. 認証・認可の実装 ★最優先★
**所要時間: 2週間 | 難易度: 高 | 影響度: 極大**

現状、誰でもアクセス可能な状態。本番運用のための必須機能。

#### A1-1. AWS Cognito セットアップ（4時間）
- **タスク:**
  - Terraform設定追加（`terraform/modules/cognito/`）
  - User Pool作成（メール認証、パスワードポリシー）
  - User Pool Client作成（フロントエンド用）
  - 環境変数追加（COGNITO_USER_POOL_ID, COGNITO_CLIENT_ID）
- **ファイル:**
  - `terraform/modules/cognito/main.tf`（新規）
  - `terraform/environments/dev/main.tf`（更新）
- **検証方法:**
  - `terraform apply` でUser Pool作成確認
  - AWS ConsoleでUser Pool設定確認

#### A1-2. フロントエンド認証UI実装（8時間）
- **タスク:**
  - AWS Amplify ライブラリ導入（`npm install aws-amplify`）
  - ログイン画面作成（`src/pages/auth/Login.tsx`）
  - サインアップ画面作成（`src/pages/auth/Register.tsx`）
  - 認証状態管理（Context API または Zustand）
  - Protected Routes実装（未ログイン時はリダイレクト）
- **ファイル:**
  - `frontend/src/pages/auth/Login.tsx`（新規）
  - `frontend/src/pages/auth/Register.tsx`（新規）
  - `frontend/src/contexts/AuthContext.tsx`（新規）
  - `frontend/src/App.tsx`（更新）
- **検証方法:**
  - ユーザー登録フロー
  - ログイン/ログアウト
  - トークン取得確認（DevTools）

#### A1-3. API Gateway認証設定（4時間）
- **タスク:**
  - Cognito Authorizer追加
  - 全エンドポイントに認証要求
  - Terraform設定更新
- **ファイル:**
  - `terraform/modules/api-gateway/main.tf`（更新）
- **検証方法:**
  - 未認証リクエスト → 401エラー
  - 認証済みリクエスト → 成功

#### A1-4. バックエンドでuserId取得（2時間）
- **タスク:**
  - Lambda event.requestContext.authorizer.claims.sub からuserId取得
  - 現在のanonymous userを実際のuserIdに置き換え
- **ファイル:**
  - `backend/app/api/routes/puzzles.py`（更新）
  - `lambda/puzzle-register/index.py`（更新）
- **検証方法:**
  - ログでuserIdが正しく取得されているか確認
  - DynamoDBに正しいuserIdでデータが保存されるか確認

### A2. Rate Limiting実装（2時間）
**優先度: 高 | 難易度: 低**

DoS攻撃対策。API Gatewayの機能で実装。

- **タスク:**
  - Usage Plan作成（100 req/sec、バースト200）
  - Quota設定（10,000 req/日）
  - Throttle設定
- **ファイル:**
  - `terraform/modules/api-gateway/main.tf`（更新）
- **検証方法:**
  - 短時間に大量リクエスト送信 → 429エラー確認

### A3. 基本的な監視設定（3時間）
**優先度: 高 | 難易度: 低**

運用開始前に最低限必要な監視を設定。

#### A3-1. CloudWatch Alarms（2時間）
- **タスク:**
  - Lambda Errors（エラー率 > 5%）
  - API Gateway 5xx Errors（5xx > 10件/5分）
  - DynamoDB Throttles（スロットル発生）
- **ファイル:**
  - `terraform/modules/monitoring/`（新規）
- **検証方法:**
  - エラーを故意に発生させてアラーム動作確認

#### A3-2. SNS通知設定（1時間）
- **タスク:**
  - SNS Topic作成
  - メール通知設定
  - （オプション）Slack通知
- **ファイル:**
  - `terraform/modules/monitoring/sns.tf`（新規）
- **検証方法:**
  - テストメッセージ送信

---

## 🟡 Phase B: ユーザビリティ向上

**目標: システムを快適に使えるようにする**

### B1. ページネーション実装（4時間）
**優先度: 中 | 難易度: 中**

パズルが100件以上になると一覧取得が遅くなる問題を解決。

- **タスク:**
  - バックエンド: `list_puzzles()` にLimitとLastEvaluatedKey対応
  - フロントエンド: ページネーションUIコンポーネント
  - 「もっと見る」ボタンまたはページ番号
- **ファイル:**
  - `backend/app/services/puzzle_service.py`（更新）
  - `frontend/src/components/PuzzleList.tsx`（更新）
- **検証方法:**
  - 大量データ（100件以上）で動作確認
  - 次ページ読み込み確認

### B2. 画像最適化Lambda（8時間）
**優先度: 中 | 難易度: 高**

アップロード画像を自動リサイズ・圧縮。

- **タスク:**
  - Lambda関数作成（Pillow使用）
  - S3イベントトリガー設定
  - サムネイル生成（200x200, 800x800）
  - 元画像の最大サイズ制限（2048px）
- **ファイル:**
  - `lambda/image-optimizer/`（新規）
  - `terraform/modules/lambda/image-optimizer.tf`（新規）
- **検証方法:**
  - 大きな画像をアップロード
  - サムネイルが自動生成されるか確認
  - 表示速度の改善確認

### B3. フロントエンドUI/UX改善（8時間）

#### B3-1. スタイリング改善（4時間）
- **タスク:**
  - Tailwind CSS導入（または CSS Modules）
  - インラインスタイルを外部化
  - 統一されたデザインシステム
- **ファイル:**
  - `frontend/tailwind.config.js`（新規）
  - 全てのコンポーネントファイル（更新）
- **検証方法:**
  - デザインの一貫性確認

#### B3-2. エラーハンドリング改善（2時間）
- **タスク:**
  - Error Boundary実装
  - トースト通知ライブラリ導入（react-hot-toast）
  - ローディング状態の改善
- **ファイル:**
  - `frontend/src/components/ErrorBoundary.tsx`（新規）
  - `frontend/src/hooks/useToast.ts`（新規）
- **検証方法:**
  - エラー発生時の挙動確認

#### B3-3. 状態管理改善（2時間）
- **タスク:**
  - React Query (TanStack Query) 導入
  - サーバー状態とクライアント状態の分離
  - 自動リフェッチ、キャッシュ管理
- **ファイル:**
  - `frontend/src/hooks/usePuzzles.ts`（新規）
  - 各コンポーネント（更新）
- **検証方法:**
  - キャッシュ動作確認
  - 自動リフェッチ確認

---

## 🟢 Phase C: テスト・品質向上

**目標: コードの保守性と信頼性を高める**

### C1. APIの統合テスト（4時間）
**優先度: 中 | 難易度: 中**

- **タスク:**
  - FastAPI TestClient使用
  - エンドツーエンドフロー
  - モックAWS環境（moto）
- **ファイル:**
  - `backend/tests/integration/test_api.py`（新規）
- **検証方法:**
  - 全エンドポイントの動作確認
  - エラーケースの確認

### C2. フロントエンドテスト（8時間）

#### C2-1. Vitestセットアップ（2時間）
- **タスク:**
  - Vitest設定
  - Testing Library導入
- **ファイル:**
  - `frontend/vitest.config.ts`（新規）
  - `frontend/src/setupTests.ts`（新規）

#### C2-2. コンポーネントテスト（6時間）
- **タスク:**
  - 主要コンポーネントのテスト
  - ユーザーインタラクションテスト
- **ファイル:**
  - `frontend/src/components/__tests__/`（新規）

### C3. CI/CD構築（8時間）

#### C3-1. GitHub Actions（4時間）
- **タスク:**
  - テスト自動実行
  - Lintチェック
  - 型チェック
- **ファイル:**
  - `.github/workflows/ci.yml`（新規）

#### C3-2. デプロイ自動化（4時間）
- **タスク:**
  - mainブランチへのプッシュで自動デプロイ
  - Terraform plan/apply自動化
- **ファイル:**
  - `.github/workflows/deploy.yml`（新規）

### C4. 型チェック強化（2時間）
- **バックエンド:** mypy設定追加
- **フロントエンド:** TypeScript strict mode有効化
- **ファイル:**
  - `pyproject.toml`（更新）
  - `frontend/tsconfig.json`（更新）

---

## 🔵 Phase D: パフォーマンス最適化

**目標: システムのスケーラビリティを向上させる**

### D1. Lambda最適化（5時間）

#### D1-1. Lambda Layer導入（3時間）
- **タスク:**
  - boto3をLayerに分離
  - デプロイパッケージサイズ削減
- **効果:**
  - Cold Start時間短縮
  - デプロイ速度向上

#### D1-2. Lambda設定改善（2時間）
- **タスク:**
  - DLQ（Dead Letter Queue）追加
  - X-Ray トレーシング有効化
  - 同時実行数制限設定
  - メモリサイズ最適化
- **ファイル:**
  - `terraform/modules/lambda/main.tf`（更新）

### D2. DynamoDB最適化（3時間）

#### D2-1. GSI活用（2時間）
- **タスク:**
  - CreatedAtIndexを使った新しい順ソート
  - ユーザーごとのパズル取得最適化

#### D2-2. TTL設定（1時間）
- **タスク:**
  - 古いパズルデータの自動削除
  - expiresAt属性追加
- **効果:**
  - ストレージコスト削減
  - データベースサイズ管理

---

## 🟣 Phase E: 高度な機能（将来実装）

### E1. 画像処理・ピース認識（未定）
- **内容:**
  - Amazon Rekognition統合
  - パズルピース位置特定
  - 画像特徴抽出
- **注意:** システム設計書に記載があるが、現在は未実装
- **優先度:** 低（コア機能として必須ではない）

### E2. リアルタイム機能（未定）
- **内容:**
  - WebSocket（API Gateway）
  - リアルタイム進捗共有
  - 協業機能
- **優先度:** 低

---

## 📅 推奨実装スケジュール

### 第1週: Phase A（実用化必須）
- **Day 1-2:** A1-1, A1-2（Cognito + フロントエンド認証）
- **Day 3-4:** A1-3, A1-4（API Gateway認証 + バックエンド対応）
- **Day 5:** A2, A3（Rate Limiting + 監視設定）

### 第2週: Phase B（ユーザビリティ）
- **Day 1:** B1（ページネーション）
- **Day 2-3:** B2（画像最適化Lambda）
- **Day 4-5:** B3（フロントエンドUI/UX改善）

### 第3週: Phase C（テスト・品質）
- **Day 1:** C1（統合テスト）
- **Day 2-3:** C2（フロントエンドテスト）
- **Day 4-5:** C3（CI/CD構築）

### 第4週: Phase D（パフォーマンス）
- **Day 1-2:** D1（Lambda最適化）
- **Day 3-4:** D2（DynamoDB最適化）
- **Day 5:** 総合テスト、ドキュメント更新

---

## 🎯 次のアクション（今すぐ着手可能）

### 最優先タスク（Phase A1開始）

1. **Cognito Terraformモジュール作成**
   - ディレクトリ作成: `terraform/modules/cognito/`
   - ファイル作成: `main.tf`, `variables.tf`, `outputs.tf`
   - User Pool定義

2. **フロントエンド認証ページ作成**
   - ディレクトリ作成: `frontend/src/pages/auth/`
   - AWS Amplify導入: `npm install aws-amplify`
   - Login.tsx作成

3. **認証状態管理実装**
   - Context API または Zustand選定
   - AuthContext作成

### 並行して着手可能なタスク

- **Rate Limiting設定**（A2）: Terraform設定のみで完結
- **CloudWatch Alarms設定**（A3-1）: Terraformで実装

---

## 📊 進捗管理

### 完了マーカー
- ✅ 完了
- 🚧 実装中
- ⏳ 保留
- ❌ 不要（スコープ外）

### 定期レビュー
- **毎週金曜:** 進捗確認、優先順位見直し
- **Phase完了時:** 総合テスト、ドキュメント更新

---

## 📝 変更履歴

### 2025-10-20
- **新規作成:** 20251020_improvement-flow.md
- **変更理由:** システムの成熟度が向上し、優先順位の再評価が必要
- **主な変更:**
  - Phase構成を「実装フェーズ」から「目的別フェーズ」に変更
  - Phase A: 実用化必須（認証・監視）を最優先に設定
  - Phase B: ユーザビリティ向上（ページネーション、画像最適化、UI改善）
  - Phase C: テスト・品質向上（統合テスト、CI/CD）
  - Phase D: パフォーマンス最適化（Lambda、DynamoDB）
  - 画像処理・ピース認識機能は Phase E（将来実装）に後回し
  - 具体的な実装スケジュール（4週間プラン）を追加
  - 次のアクションを明確化

### 2025-10-19（前回までの進捗）
- ✅ セキュリティ基盤構築（CORS、エラー制御、ログ、Input validation）
- ✅ テスト基盤構築（pytest、単体テスト、カバレッジ100%）
- ✅ CloudFront CDN設定
- ✅ ディレクトリ構造リファクタリング
