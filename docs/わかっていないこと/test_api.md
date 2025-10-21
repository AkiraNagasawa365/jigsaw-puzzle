# API統合テスト（test_api.py）

作成日: 2025-10-22

## 何をしているか

FastAPIアプリケーション全体の動作を自動テストで検証しています。

**主な検証内容:**
- エンドポイントが正しくルーティングされるか
- リクエストのバリデーションが機能しているか
- レスポンスの形式が正しいか
- CORS設定が正しいか
- エラーハンドリングが適切か

**目的:**
- Mangum実装後、ローカル（FastAPI）とLambda本番環境で同じコードが正しく動作することを保証
- コード変更時に既存機能が壊れていないことを自動確認（リグレッションテスト）
- 手動テストの手間を削減

---

## どのような方法が用いられているか

### 1. FastAPI TestClient

```python
from fastapi.testclient import TestClient
from app.api.main import app

client = TestClient(app)
response = client.get("/")
```

**説明:**
- FastAPIの組み込みテストクライアント
- 実際のHTTPリクエストを送らずに、FastAPIアプリを直接呼び出してテスト
- 高速で、外部依存なし

### 2. pytest フィクスチャ

```python
@pytest.fixture
def client():
    return TestClient(app)
```

**説明:**
- テストで共通利用するオブジェクトを定義
- 各テストメソッドで`client`引数を受け取るだけで使える

### 3. テストクラスによる整理

```python
class TestHealthCheck:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
```

**説明:**
- テストをカテゴリ別（ヘルスチェック、ルーティング、バリデーション等）にグループ化
- テストの目的が明確になり、保守しやすい

### 4. アサーション（assert）による検証

```python
assert response.status_code == 200
assert "status" in data
assert data["status"] == "ok"
```

**説明:**
- 期待値と実際の値を比較
- 一致しなければテスト失敗

---

## テストの実行方法

```bash
# 統合テストのみ実行
uv run pytest tests/integration/test_api.py -v

# 全テスト実行
uv run pytest

# カバレッジ付きで実行
uv run pytest --cov=app --cov-report=html
```

---

## テストの構成

### TestHealthCheck
ルートエンドポイント（`/`）が正しく応答することを確認

### TestEndpointRouting
4つのAPIエンドポイントが存在し、アクセス可能であることを確認

### TestRequestValidation
- 無効なデータでバリデーションエラーが返ること
- XSS攻撃が検出されること
- 必須フィールドが検証されること

### TestCORSHeaders
CORS設定が正しく適用されていることを確認

### TestErrorHandling
404エラー、405エラーが適切に返されることを確認

### TestResponseFormat
レスポンスの形式（JSON、Content-Type）が正しいことを確認

---

## なぜAWS呼び出しをモック化しないのか

**理由:**
- このテストは「エンドポイントのルーティングとバリデーション」に焦点を当てている
- AWS呼び出しの詳細は単体テスト（`test_puzzle_service.py`）でカバー済み
- 統合テストはAPI層の動作のみを検証する役割

**結果:**
- テストが高速（AWS接続不要）
- テストがシンプル（モック化コードが不要）
- テストの目的が明確

---

## 今後の改善案

1. **motoを使った完全統合テスト**
   - DynamoDBとS3をモック化し、エンドツーエンドでテスト
   - 実際のデータ作成→取得→更新のフローを検証

2. **パフォーマンステスト**
   - レスポンスタイムの計測
   - 大量リクエストの処理

3. **認証テスト（Phase A後）**
   - Cognito認証が正しく機能することを確認
   - 未認証リクエストが拒否されることを確認

---

## 参考リンク

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest公式ドキュメント](https://docs.pytest.org/)
- [TestClient API](https://www.starlette.io/testclient/)
