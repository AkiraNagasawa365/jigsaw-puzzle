# フロントエンドテスト実装 (Vitest + Testing Library)

**日付**: 2025-10-22
**目的**: フロントエンドの自動テストを実装し、完全なCI/CDパイプラインを構築する

---

## 実装内容

### 1. テストフレームワークのセットアップ

**インストールしたパッケージ**:
```bash
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

**設定ファイル**:
- `vitest.config.ts` - Vitestの設定（jsdom環境、カバレッジ設定）
- `src/test/setup.ts` - テストセットアップ（グローバルモック、クリーンアップ）
- `src/test/vitest.d.ts` - TypeScript型定義

**package.jsonスクリプト追加**:
```json
{
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:coverage": "vitest --coverage"
}
```

---

## 2. コンポーネントテストの作成

### テスト対象コンポーネント

#### A. PuzzleList コンポーネント
**ファイル**: `src/components/__tests__/PuzzleList.test.tsx`
**テスト数**: 8件

| テストケース | 内容 |
|------------|------|
| ローディング状態を表示する | fetchがpending状態の時に「読み込み中...」が表示されることを確認 |
| パズル一覧を表示する | モックデータが正しく表示されることを確認 |
| 空の状態を表示する | パズルが0件の時の表示を確認 |
| エラー状態を表示する | APIエラー時のエラーメッセージ表示を確認 |
| パズルクリック時にコールバックが呼ばれる | onPuzzleClickが正しく呼ばれることを確認 |
| 更新ボタンクリックでデータを再取得する | 更新ボタンでfetchが再実行されることを確認 |
| 正しいAPIエンドポイントを呼び出す | userIdに応じた正しいURLが呼ばれることを確認 |
| ステータスに応じた表示が変わる | pending/processing/completedの表示切り替えを確認 |

#### B. PuzzleCreate コンポーネント
**ファイル**: `src/pages/puzzles/__tests__/PuzzleCreate.test.tsx`
**テスト数**: 11件

| テストケース | 内容 |
|------------|------|
| フォームが正しくレンダリングされる | 入力フォームとボタンが表示されることを確認 |
| パズル名の入力が機能する | テキスト入力が正しく動作することを確認 |
| ピース数の選択が機能する | セレクトボックスが正しく動作することを確認 |
| 空のパズル名で作成ボタンが無効化される | バリデーションによるボタン無効化を確認 |
| パズル名が入力されると作成ボタンが有効化される | 入力後のボタン有効化を確認 |
| 空のパズル名で作成を試みるとエラーメッセージが表示される | クライアント側バリデーションを確認 |
| 作成成功時に詳細画面に遷移する | navigate関数が正しいパスで呼ばれることを確認 |
| 作成中はボタンが無効化され、ローディング表示になる | ローディング状態のUI変化を確認 |
| 作成失敗時にエラーメッセージが表示される | API失敗時のエラーハンドリングを確認 |
| 正しいAPIエンドポイントとデータで作成リクエストが送信される | fetchの引数（URL、メソッド、ボディ）を確認 |
| 一覧に戻るボタンで戻る | 戻るボタンのナビゲーションを確認 |

#### C. Home コンポーネント
**ファイル**: `src/pages/__tests__/Home.test.tsx`
**テスト数**: 5件

| テストケース | 内容 |
|------------|------|
| ページタイトルが表示される | ヘッダー情報が表示されることを確認 |
| ログインユーザーのメールアドレスが表示される | AuthContextからのユーザー情報表示を確認 |
| 新規作成ボタンが表示され、クリックで作成画面に遷移する | ボタンクリックでナビゲーションを確認 |
| ログアウトボタンが機能する | logout関数が呼ばれることを確認 |
| PuzzleListコンポーネントが表示される | 子コンポーネントがレンダリングされることを確認 |

---

## 3. CI/CDパイプラインへの統合

**変更ファイル**: `.github/workflows/ci.yml`

**追加ステップ**:
```yaml
- name: Run Vitest (Unit Tests)
  working-directory: frontend
  run: npm test -- --run
```

**実行順序**:
1. TypeScript型チェック (`npx tsc --noEmit`)
2. **Vitestテスト実行** ← 新規追加
3. ESLint (警告のみ、非ブロッキング)
4. ビルド (`npm run build`)

---

## 4. テスト実行結果

### ローカル実行
```bash
npm test -- --run
```

**結果**:
- ✅ Test Files: 3 passed (3)
- ✅ Tests: 24 passed (24)
- ✅ Duration: 1.24s

### TypeScriptビルド
```bash
npm run build
```

**結果**:
- ✅ TypeScript型チェック: エラー0件
- ✅ ビルド成功: dist/index.html, assets 生成

---

## 5. テスト戦略

### モックの使用
- **fetch API**: `vi.fn()` でモック化し、レスポンスをシミュレート
- **react-router-dom**: `useNavigate` をモックしてナビゲーションをテスト
- **AuthContext**: モックユーザーオブジェクトで認証状態をシミュレート

### テストのスコープ
- ✅ **テスト対象**: コンポーネントのUI、ユーザーインタラクション、状態管理
- ❌ **テスト対象外**: 実際のAPI呼び出し（バックエンドの統合テストでカバー）

### カバレッジ除外
```typescript
exclude: [
  'node_modules/',
  'src/test/',
  '**/*.config.ts',
  '**/*.d.ts',
  '**/main.tsx',
]
```

---

## 6. 技術的な課題と解決方法

### 課題1: label要素とinputの関連付け
**問題**: コンポーネントが `htmlFor` 属性を使っていないため、`getByLabelText()` でエラー

**解決**: `getByPlaceholderText()` と `getByRole()` を使用
```typescript
// Before (エラー)
const input = screen.getByLabelText(/パズル名/)

// After (正常動作)
const input = screen.getByPlaceholderText('例：富士山の風景、海の絵')
```

### 課題2: TypeScript型エラー (global.fetch)
**問題**: `vi.fn()` の返り値が `fetch` 型と互換性がない

**解決**: `as any` でキャスト
```typescript
global.fetch = vi.fn(() => new Promise(() => {})) as any
```

### 課題3: act() 警告
**問題**: PuzzleListの非同期状態更新により `act(...)` 警告が表示

**解決**: 警告のみでテストは成功するため、現時点では許容
- 警告は実害なし（テストは全て通過）
- 実装の改善で将来対応可能

---

## 7. 今後の改善案

### A. テストカバレッジの拡大
- [ ] PuzzleDetail コンポーネントのテスト
- [ ] 認証ページ (Login, Register) のテスト
- [ ] ProtectedRoute コンポーネントのテスト
- [ ] カバレッジ80%以上を目標

### B. テストの質向上
- [ ] act() 警告の解消（waitForで非同期処理を適切に待機）
- [ ] スナップショットテストの追加（UI回帰テスト）
- [ ] アクセシビリティテスト（axe-core連携）

### C. E2Eテストの検討
- [ ] Playwright / Cypress の導入検討
- [ ] 実際のブラウザでの動作テスト
- [ ] APIとの統合テスト

---

## 8. まとめ

### 達成したこと
✅ **Vitest + Testing Library のセットアップ完了**
✅ **24件のコンポーネントテストを実装**
✅ **CI/CDパイプラインに統合し、自動テスト実行を実現**
✅ **TypeScript型チェック + テスト + ビルドの完全な自動化**

### 品質向上への効果
- **バグの早期発見**: PRごとに自動テストが実行され、リグレッションを防止
- **リファクタリングの安全性**: テストがあることでコード変更の影響を検証可能
- **開発速度の向上**: 手動テストの削減により開発に集中できる
- **ドキュメント効果**: テストコードが仕様書の役割を果たす

### Phase C (テスト・品質向上) の完了
- ✅ **C1**: API統合テスト実装 (15件)
- ✅ **C2**: フロントエンドテスト実装 (24件)
- ✅ **C3**: CI/CD構築 (GitHub Actions)
- ✅ **C4**: 型チェック強化 (mypy + TypeScript strict mode)

---

## 参考コマンド

```bash
# テスト実行
npm test                    # watch mode（開発中）
npm test -- --run          # 1回だけ実行（CI用）
npm test -- --ui           # UIモードで実行

# カバレッジ確認
npm run test:coverage

# TypeScript型チェック
npx tsc --noEmit

# フルビルド（型チェック + ビルド）
npm run build
```

---

**次のステップ**: Phase A (認証機能) の実装、または本番環境へのデプロイ準備
