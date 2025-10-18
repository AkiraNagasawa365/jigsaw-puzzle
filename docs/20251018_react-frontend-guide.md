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

### デプロイ先（将来）
```
- AWS S3 + CloudFront（静的ホスティング）
- または AWS Amplify（CI/CD付き）
```

---

## ディレクトリ構造

```
jigsaw-puzzle/
├── backend/           # 既存のFastAPI
├── lambda/            # 既存のLambda
├── terraform/         # 既存のインフラ
└── frontend/          # 新規作成（React）
    ├── public/        # 静的ファイル
    ├── src/
    │   ├── components/    # 再利用可能なコンポーネント
    │   │   ├── ImageUpload.tsx
    │   │   ├── PuzzleCard.tsx
    │   │   └── PuzzleList.tsx
    │   ├── pages/         # ページコンポーネント
    │   │   ├── Home.tsx
    │   │   ├── PuzzleDetail.tsx
    │   │   └── Upload.tsx
    │   ├── api/           # API通信ロジック
    │   │   └── puzzleApi.ts
    │   ├── types/         # TypeScript型定義
    │   │   └── puzzle.ts
    │   ├── App.tsx        # メインアプリ
    │   └── main.tsx       # エントリーポイント
    ├── package.json
    └── vite.config.ts
```

---

## 実装する機能

### Phase 1: 基本機能
- [x] プロジェクトセットアップ（Vite + React + TypeScript）
- [ ] ホーム画面（簡単な説明）
- [ ] パズル登録画面（画像アップロード）
- [ ] API連携（バックエンドとの通信）

### Phase 2: パズル一覧
- [ ] パズル一覧表示
- [ ] サムネイル表示
- [ ] ローディング・エラーハンドリング

### Phase 3: パズル詳細
- [ ] 詳細画面
- [ ] 画像拡大表示
- [ ] パズル情報編集

### Phase 4: UX改善
- [ ] レスポンシブデザイン（モバイル対応）
- [ ] ドラッグ&ドロップ
- [ ] プログレスバー
- [ ] トースト通知

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
uv run uvicorn backend.app:app --reload

# フロントエンドから http://localhost:8000 にアクセス
```

### 4. ビルド・デプロイ
```bash
# 本番ビルド
npm run build

# dist/ ディレクトリが生成される
# これをS3にアップロード
```

---

## API統合

### バックエンドのエンドポイント

現在利用可能なAPI：

#### 1. パズル登録
```
POST http://localhost:8000/puzzles
Body: {
  "pieceCount": 300,
  "fileName": "puzzle.png",
  "userId": "user123"
}

Response: {
  "puzzleId": "...",
  "uploadUrl": "https://...",
  "expiresIn": 3600
}
```

#### 2. パズル取得
```
GET http://localhost:8000/puzzles/{puzzle_id}?user_id={user_id}

Response: {
  "puzzleId": "...",
  "pieceCount": 300,
  "fileName": "puzzle.png",
  ...
}
```

#### 3. パズル一覧
```
GET http://localhost:8000/users/{user_id}/puzzles

Response: [
  { "puzzleId": "...", ... },
  { "puzzleId": "...", ... }
]
```

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
- FastAPIのCORS設定を確認（既に設定済みのはず）
- `backend/app.py` で `allow_origins=["*"]` を確認

### 画像アップロードエラー
```
Failed to upload image to S3
```

**解決方法：**
- Pre-signed URLの有効期限を確認
- Content-Typeが正しいか確認
- ネットワークエラーをキャッチ

---

## 次のステップ

1. **プロジェクト作成** - Vite + React + TypeScript
2. **最初のコンポーネント** - シンプルなホーム画面
3. **API連携** - バックエンドと通信
4. **画像アップロード** - メイン機能実装

---

## 参考リンク

- [React公式ドキュメント](https://react.dev/)
- [TypeScript公式](https://www.typescriptlang.org/)
- [Vite公式](https://vitejs.dev/)
- [React Router](https://reactrouter.com/)
- [TanStack Query](https://tanstack.com/query/latest)
