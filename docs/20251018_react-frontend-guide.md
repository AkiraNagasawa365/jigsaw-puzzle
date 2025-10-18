# React フロントエンド開発ガイド

## プロジェクト概要

ジグソーパズルヘルパーのWebフロントエンドをReactで構築します。

### 目的
- ユーザーがブラウザからパズル画像をアップロードできる
- 登録したパズルの一覧を表示できる
- パズルの詳細情報を確認できる

---

## 技術スタック

### コア技術
```
- React 18.x（最新版）
- TypeScript（型安全性）
- Vite（高速ビルドツール）
```

### 主要ライブラリ（順次導入）
```
- React Router（ページ遷移）
- React Query / TanStack Query（API通信・キャッシュ）
- react-dropzone（画像ドラッグ&ドロップ）
- Tailwind CSS（スタイリング）
```

### デプロイ先
```
✅ 本番環境稼働中
- AWS S3 + CloudFront（静的ホスティング）
- URL: https://dykwhpbm0bhdv.cloudfront.net
- Terraform管理（terraform/modules/frontend/）
- 自動デプロイスクリプト: scripts/deploy-frontend.sh
```

**デプロイ手順:**
```bash
# フロントエンドをビルドしてCloudFrontにデプロイ
./scripts/deploy-frontend.sh dev

# スクリプトが自動で以下を実行:
# 1. npm run build
# 2. S3にファイルアップロード
# 3. CloudFrontキャッシュ無効化
```

---

## 環境変数の設定

### フロントエンド環境変数

フロントエンドはViteの環境変数システムを使用しています。

#### 環境ごとの設定ファイル

```
frontend/
├── .env                  # ローカル開発用（デフォルト）
├── .env.production       # 本番ビルド用
└── .env.local            # 個人用設定（gitignore対象）
```

#### .env（ローカル開発）
```bash
VITE_API_BASE_URL=http://localhost:8000
```

#### .env.production（本番環境）
```bash
VITE_API_BASE_URL=https://hbwku63803.execute-api.ap-northeast-1.amazonaws.com/dev
```

#### 使用方法
```typescript
// frontend/src/config/api.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// コンポーネントで使用
import { API_BASE_URL } from '../config/api'
const response = await fetch(`${API_BASE_URL}/puzzles`)
```

**重要な注意点:**
- Viteの環境変数は必ず `VITE_` プレフィックスが必要
- ビルド時に静的に埋め込まれる（実行時に変更不可）
- 環境変数の優先順位: `.env.local` > `.env.[mode]` > `.env`

### バックエンド環境変数

バックエンドはローカル開発時に以下の環境変数を設定する必要があります:

```bash
# AWS設定
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=default

# S3・DynamoDB設定
export S3_BUCKET_NAME=jigsaw-puzzle-dev-images
export PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles
export PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces

# 環境識別
export ENVIRONMENT=dev

# CORS設定（カンマ区切り）
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173,https://dykwhpbm0bhdv.cloudfront.net"
```

参考ファイル: `backend/.env.example`

**設定の読み込み:**
```python
# backend/app/core/config.py
class Settings:
    def __init__(self):
        self.aws_region = os.environ.get('AWS_REGION', 'ap-northeast-1')
        self.s3_bucket_name = os.environ.get('S3_BUCKET_NAME', '...')
        # ...
```

### Lambda環境変数

Lambda関数の環境変数はTerraformで自動設定されます。

設定ファイル: `terraform/modules/lambda/main.tf`

```hcl
environment {
  variables = {
    S3_BUCKET_NAME      = var.s3_bucket_name
    PUZZLES_TABLE_NAME  = var.puzzles_table_name
    PIECES_TABLE_NAME   = var.pieces_table_name
    ENVIRONMENT         = var.environment
    ALLOWED_ORIGINS     = join(",", var.allowed_origins)
  }
}
```

---

## ディレクトリ構造

### バックエンド構造（リファクタリング済み）
```
backend/
└── app/              # メインアプリケーションパッケージ
    ├── api/          # API層
    │   ├── main.py           # FastAPIエントリーポイント
    │   └── routes/           # APIルート定義
    │       └── puzzles.py
    ├── core/         # コア機能
    │   ├── config.py         # 環境変数・設定管理
    │   └── schemas.py        # Pydanticスキーマ
    └── services/     # ビジネスロジック
        └── puzzle_service.py
```

### フロントエンド構造（実装済み）
```
frontend/
├── public/           # 静的ファイル
├── src/
│   ├── components/       # 再利用可能なコンポーネント
│   │   └── PuzzleList.tsx      # ✅ パズル一覧表示（Homeで使用）
│   ├── pages/            # ページコンポーネント（機能別フォルダ構造）
│   │   ├── Home.tsx            # ✅ ホーム画面 (/)
│   │   └── puzzles/            # パズル機能のページ群
│   │       ├── PuzzleCreate.tsx    # ✅ パズル新規作成 (/puzzles/new)
│   │       └── PuzzleDetail.tsx    # ✅ パズル詳細・画像アップロード (/puzzles/:id)
│   ├── config/           # 設定ファイル
│   │   └── api.ts              # ✅ API Base URL設定
│   ├── types/            # TypeScript型定義
│   │   └── puzzle.ts           # ✅ Puzzle型・リクエスト/レスポンス型
│   ├── App.tsx           # メインアプリ（React Router設定）
│   ├── main.tsx          # エントリーポイント
│   └── index.css         # グローバルスタイル
├── .env                  # ローカル開発用環境変数
├── .env.production       # 本番環境用環境変数
├── package.json
├── vite.config.ts
└── tsconfig.json
```

**ディレクトリ設計の原則（パターン2: 機能別フォルダ構造）:**
- **`pages/`**: React Routerでルート定義されているコンポーネント
  - トップレベルページ（Home.tsx など）は直下に配置
  - 機能別にフォルダを作成（`puzzles/`, `users/`, `auth/` など）
  - 各機能フォルダ内にページコンポーネントを配置
- **`components/`**: 複数のページで再利用されるコンポーネント
- **`config/`**: アプリケーション設定（API URL、定数など）
- **`types/`**: TypeScript型定義（ドメインモデル）

**この構造の利点:**
- ✅ 10-50ページ規模に対応可能
- ✅ 機能単位でファイルがグループ化され、見つけやすい
- ✅ 関連するページが近くに配置される
- ✅ 新しい機能追加時にフォルダを増やすだけ

**将来の拡張例:**
```
pages/
├── Home.tsx
├── puzzles/
│   ├── PuzzleList.tsx       # /puzzles (一覧ページ追加時)
│   ├── PuzzleCreate.tsx     # /puzzles/new
│   ├── PuzzleDetail.tsx     # /puzzles/:id
│   └── PuzzleEdit.tsx       # /puzzles/:id/edit (編集機能追加時)
├── users/
│   ├── UserProfile.tsx      # /users/:id (将来追加)
│   └── UserSettings.tsx     # /users/:id/settings
└── auth/
    ├── Login.tsx            # /login (認証機能追加時)
    └── Register.tsx         # /register
```

**構造上の変更履歴:**
- `api/puzzleApi.ts` → `config/api.ts` に変更（よりシンプルな構成）
- `PuzzleDetail.tsx` を `components/` → `pages/` に移動（ページコンポーネントとして正しく配置）
- `pages/` 直下のパズルページを `pages/puzzles/` に移動（機能別フォルダ構造採用）
- `Upload.tsx` → `PuzzleCreate.tsx` に改名（より明確な命名）
- 環境変数ファイル (`.env`, `.env.production`) を追加

---

## 実装済み機能と今後の予定

### Phase 1: 基本機能（✅ 完了）
- [x] プロジェクトセットアップ（Vite + React + TypeScript）
- [x] ホーム画面（パズル一覧表示）
- [x] パズル新規作成画面（名前・ピース数入力）
- [x] API連携（環境変数による切り替え対応）
- [x] React Router導入（3ルート: `/`, `/puzzles/new`, `/puzzles/:id`）

### Phase 2: パズル一覧（✅ 完了）
- [x] パズル一覧表示（グリッドレイアウト）
- [x] ステータス表示（pending/uploaded/processing/completed）
- [x] ローディング・エラーハンドリング
- [x] 更新ボタン（再取得機能）
- [ ] サムネイル表示（画像処理完了後に実装予定）

### Phase 3: パズル詳細（✅ 基本完了）
- [x] 詳細画面（パズル情報表示）
- [x] 画像アップロード機能（Pre-signed URL経由）
- [x] 2段階アップロードフロー（パズル作成→画像アップロード）
- [x] S3直接アップロード実装
- [ ] 画像拡大表示（画像取得API実装後）
- [ ] パズル情報編集
- [ ] ピース画像一覧表示（画像処理実装後）

### Phase 4: UX改善（未実装）
- [ ] レスポンシブデザイン（モバイル対応）
- [ ] ドラッグ&ドロップ（react-dropzone導入）
- [ ] プログレスバー（アップロード進捗表示）
- [ ] トースト通知（react-hot-toastなど）
- [ ] Tailwind CSS導入（現在はインラインスタイル）

### Phase 5: インフラ・デプロイ（✅ 完了）
- [x] CloudFront + S3構築（Terraform）
- [x] 本番環境デプロイ（https://dykwhpbm0bhdv.cloudfront.net）
- [x] デプロイスクリプト作成（`scripts/deploy-frontend.sh`）
- [x] CORS設定（環境変数制御・複数オリジン対応）

---

## 開発フロー

### 1. プロジェクト作成
```bash
# Vite + React + TypeScript でプロジェクト作成
npm create vite@latest frontend -- --template react-ts

# 依存関係インストール
cd frontend
npm install
```

### 2. ローカル開発
```bash
# 開発サーバー起動
npm run dev

# ブラウザで確認
http://localhost:5173
```

### 3. バックエンド連携
```bash
# バックエンド（FastAPI）も起動
cd ../backend
uv run uvicorn app.api.main:app --reload

# フロントエンドから http://localhost:8000 にアクセス
```

**重要:** バックエンドの構造変更に伴い、起動コマンドが変更されています。
- 旧: `backend.app:app` (廃止)
- 新: `app.api.main:app` (現在の正しいパス)

### 4. ビルド・デプロイ
```bash
# 本番ビルド
npm run build

# dist/ ディレクトリが生成される
# これをS3にアップロード
```

---

## API統合

### 環境別のエンドポイント

#### ローカル開発環境
```
Base URL: http://localhost:8000
環境変数: VITE_API_BASE_URL=http://localhost:8000
```

#### 本番環境（Lambda + API Gateway）
```
Base URL: https://hbwku63803.execute-api.ap-northeast-1.amazonaws.com/dev
環境変数: VITE_API_BASE_URL=https://hbwku63803.execute-api.ap-northeast-1.amazonaws.com/dev
```

### 実装済みAPIエンドポイント

#### 1. パズル新規作成（画像なし）
**重要:** 画像アップロードは別ステップです。まずパズルプロジェクトを作成します。

```http
POST /puzzles
Content-Type: application/json

Request Body:
{
  "puzzleName": "富士山の風景",
  "pieceCount": 300,
  "userId": "anonymous"
}

Response (200 OK):
{
  "puzzleId": "550e8400-e29b-41d4-a716-446655440000",
  "puzzleName": "富士山の風景",
  "pieceCount": 300,
  "status": "pending",
  "message": "Puzzle created successfully"
}
```

**実装例（PuzzleCreate.tsx）:**
```typescript
const response = await fetch(`${API_BASE_URL}/puzzles`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    puzzleName: "富士山の風景",
    pieceCount: 300,
    userId: "anonymous"
  })
})
```

#### 2. 画像アップロードURL取得
パズル作成後、このエンドポイントでS3へのアップロードURLを取得します。

```http
POST /puzzles/{puzzleId}/upload
Content-Type: application/json

Request Body:
{
  "fileName": "fuji.jpg",
  "userId": "anonymous"
}

Response (200 OK):
{
  "puzzleId": "550e8400-e29b-41d4-a716-446655440000",
  "uploadUrl": "https://jigsaw-puzzle-dev-images.s3.amazonaws.com/...",
  "expiresIn": 3600,
  "message": "Upload URL generated"
}
```

**実装例（PuzzleDetail.tsx）:**
```typescript
// Step 1: アップロードURL取得
const urlResponse = await fetch(
  `${API_BASE_URL}/puzzles/${puzzleId}/upload`,
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      fileName: file.name,
      userId: 'anonymous'
    })
  }
)
const { uploadUrl } = await urlResponse.json()

// Step 2: S3に直接アップロード
await fetch(uploadUrl, {
  method: 'PUT',
  headers: { 'Content-Type': file.type },
  body: file
})
```

#### 3. パズル詳細取得
```http
GET /puzzles/{puzzleId}?user_id={userId}

Response (200 OK):
{
  "puzzleId": "550e8400-e29b-41d4-a716-446655440000",
  "userId": "anonymous",
  "puzzleName": "富士山の風景",
  "pieceCount": 300,
  "fileName": "fuji.jpg",
  "s3Key": "puzzles/anonymous/550e8400.../fuji.jpg",
  "status": "uploaded",
  "createdAt": "2025-01-18T10:30:00Z",
  "updatedAt": "2025-01-18T10:35:00Z"
}
```

#### 4. ユーザーのパズル一覧取得
```http
GET /users/{userId}/puzzles

Response (200 OK):
{
  "puzzles": [
    {
      "puzzleId": "...",
      "puzzleName": "富士山の風景",
      "pieceCount": 300,
      "status": "uploaded",
      "createdAt": "2025-01-18T10:30:00Z",
      ...
    },
    ...
  ]
}
```

**実装例（PuzzleList.tsx）:**
```typescript
const response = await fetch(`${API_BASE_URL}/users/anonymous/puzzles`)
const data = await response.json()
setPuzzles(data.puzzles || [])
```

### ステータスの遷移

```
pending → uploaded → processing → completed
```

- **pending**: パズル作成済み、画像未アップロード
- **uploaded**: 画像アップロード完了
- **processing**: 画像分割処理中（未実装）
- **completed**: 処理完了（未実装）

---

## React開発のベストプラクティス

### 1. コンポーネント設計
```tsx
// 小さく、単一責任
// 良い例
const ImageUpload = ({ onUpload }) => { ... }

// 悪い例：1つのコンポーネントで全部やる
const MegaComponent = () => { ... }
```

### 2. State管理
```tsx
// useState（シンプルなstate）
const [puzzles, setPuzzles] = useState([])

// useContext（グローバルstate）
const { user } = useUser()

// React Query（サーバーstate）
const { data } = useQuery('puzzles', fetchPuzzles)
```

### 3. 型定義
```typescript
// 型を定義して型安全に
interface Puzzle {
  puzzleId: string
  pieceCount: number
  fileName: string
  userId: string
  createdAt: string
}
```

---

## 学習ロードマップ

### Week 1: React基礎
- [ ] JSX構文
- [ ] コンポーネント
- [ ] Props
- [ ] State（useState）

### Week 2: React応用
- [ ] useEffect
- [ ] カスタムフック
- [ ] React Router
- [ ] フォーム処理

### Week 3: 統合
- [ ] API通信
- [ ] エラーハンドリング
- [ ] ローディング状態
- [ ] 画像アップロード

### Week 4: 仕上げ
- [ ] スタイリング
- [ ] レスポンシブ
- [ ] パフォーマンス最適化
- [ ] デプロイ

---

## トラブルシューティング

### CORS エラー
```
Access to fetch at 'http://localhost:8000/puzzles' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**解決方法：**

#### ローカル開発環境（FastAPI）
CORS設定は環境変数 `ALLOWED_ORIGINS` で制御されています。

```bash
# backend/.env.example を参照
export ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173"
```

設定ファイルの場所:
- `backend/app/api/main.py` - FastAPIのCORS設定
- `backend/app/core/config.py` - 環境変数読み込み

現在の設定:
```python
# backend/app/api/main.py
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # 環境変数から取得
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

#### 本番環境（Lambda）
Lambda関数は動的CORS設定を使用しており、リクエストのOriginヘッダーをチェックします。

許可されているオリジン（環境変数で設定）:
- `http://localhost:3000`
- `http://localhost:5173` (Vite開発サーバー)
- `https://dykwhpbm0bhdv.cloudfront.net` (本番CloudFront)

Terraform設定: `terraform/environments/dev/variables.tf`

### 画像アップロードエラー
```
Failed to upload image to S3
```

**解決方法：**
- Pre-signed URLの有効期限を確認
- Content-Typeが正しいか確認
- ネットワークエラーをキャッチ

---

## 実際のユーザーワークフロー

### 1. パズル新規作成

#### ユーザー操作
1. ホーム画面で「+ 新規作成」ボタンをクリック
2. `/puzzles/new` に遷移
3. パズル名を入力（例：「富士山の風景」）
4. ピース数を選択（100, 300, 500, 1000, 2000）
5. 「パズルを作成」ボタンをクリック

#### システム動作
```typescript
// PuzzleCreate.tsx
POST /puzzles
→ DynamoDB にパズルレコード作成（status: pending）
→ 成功したら /puzzles/{puzzleId} に自動遷移
```

### 2. 画像アップロード

#### ユーザー操作
1. パズル詳細画面で「ファイルを選択」
2. 画像ファイルを選択（JPEG, PNG など）
3. 「画像をアップロード」ボタンをクリック

#### システム動作
```typescript
// PuzzleDetail.tsx (2段階フロー)

// Step 1: Pre-signed URL取得
POST /puzzles/{puzzleId}/upload
→ Lambda が S3 Pre-signed URL を生成（有効期限: 1時間）
→ DynamoDB のファイル名・S3キーを更新

// Step 2: S3に直接アップロード
PUT <pre-signed-url>
→ ブラウザから直接 S3 にアップロード
→ status が pending → uploaded に変更
```

**重要:** Lambda は画像本体を扱わず、URLの発行のみを行います。これによりLambdaのタイムアウトやメモリ制限を回避しています。

### 3. パズル一覧確認

#### ユーザー操作
1. ホーム画面（`/`）でパズル一覧を確認
2. パズルカードをクリックして詳細表示

#### システム動作
```typescript
// PuzzleList.tsx
GET /users/anonymous/puzzles
→ DynamoDB から該当ユーザーのパズルを全件取得
→ ステータスごとに色分け表示
```

**ステータス表示:**
- 🔴 待機中 (pending) - 画像未アップロード
- 🟡 処理中 (processing) - 画像分割処理中 ※未実装
- 🟢 完了 (completed) - 全処理完了 ※未実装

### 4. 画像処理（今後実装予定）

#### 予定されているワークフロー
```
S3イベント
→ S3にファイルアップロード時にLambda起動
→ 画像をピース数に応じて分割
→ 各ピース画像をS3に保存
→ DynamoDB (Pieces テーブル) にピース情報を保存
→ status を uploaded → processing → completed に更新
```

## 次のステップ

### 既に完了している項目
- [x] プロジェクト作成（Vite + React + TypeScript）
- [x] コンポーネント実装（Home, PuzzleCreate, PuzzleList, PuzzleDetail）
- [x] API連携（環境変数制御）
- [x] 画像アップロード（Pre-signed URL方式）
- [x] CloudFrontデプロイ

### 今後実装する項目
1. **画像処理機能** - S3イベント駆動のピース分割
2. **ピース表示** - 分割されたピース画像の一覧表示
3. **UI/UX改善** - Tailwind CSS導入、レスポンシブ対応
4. **認証機能** - 現在は "anonymous" のみ対応

---

## 参考リンク

- [React公式ドキュメント](https://react.dev/)
- [TypeScript公式](https://www.typescriptlang.org/)
- [Vite公式](https://vitejs.dev/)
- [React Router](https://reactrouter.com/)
- [TanStack Query](https://tanstack.com/query/latest)
