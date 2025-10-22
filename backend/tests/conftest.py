"""
共通テストフィクスチャ

このファイルは全てのテストから自動的に読み込まれます。
再利用可能なフィクスチャ（テストデータ、モックオブジェクト等）を定義します。
"""

import os
import pytest
from typing import Generator, Dict, Any
from unittest.mock import MagicMock, patch


# ===== 環境変数のモック =====

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """
    テスト実行前に環境変数を設定

    scope="session": 全テストセッションで1回だけ実行
    autouse=True: 明示的に指定しなくても自動的に実行
    """
    # AWS認証情報（motoを使う場合でもboto3初期化に必要）
    os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
    os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
    os.environ.setdefault("AWS_SESSION_TOKEN", "testing")
    os.environ.setdefault("AWS_DEFAULT_REGION", "ap-northeast-1")

    # アプリケーション環境変数
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("LOG_LEVEL", "DEBUG")
    os.environ.setdefault("S3_BUCKET_NAME", "test-bucket")
    os.environ.setdefault("PUZZLES_TABLE_NAME", "test-puzzles")
    os.environ.setdefault("PIECES_TABLE_NAME", "test-pieces")
    os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")


# ===== テストデータフィクスチャ =====

@pytest.fixture
def valid_puzzle_data() -> Dict[str, Any]:
    """
    有効なパズル作成データ

    Returns:
        正常系テストで使用する標準的なパズルデータ
    """
    return {
        "puzzleName": "富士山の風景",
        "pieceCount": 300,
        "userId": "test-user-123"
    }


@pytest.fixture
def valid_upload_data() -> Dict[str, Any]:
    """
    有効な画像アップロードデータ

    Returns:
        正常系テストで使用する標準的なアップロードデータ
    """
    return {
        "fileName": "puzzle.jpg",
        "userId": "test-user-123"
    }


# ===== セキュリティテスト用データ =====

@pytest.fixture
def xss_attack_payloads() -> list[str]:
    """
    XSS攻撃パターンのリスト

    Returns:
        実際の攻撃で使用される可能性があるペイロード
    """
    return [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "javascript:alert('xss')",
        "<iframe src='javascript:alert(1)'>",
        "<body onload=alert(1)>",
        "<div>test</div>",
        "<h1>Header</h1>",
        "<<SCRIPT>alert('XSS');//<</SCRIPT>",
        "<SCRIPT SRC=http://xss.rocks/xss.js></SCRIPT>"
    ]


@pytest.fixture
def path_traversal_payloads() -> list[str]:
    """
    パストラバーサル攻撃パターンのリスト

    Returns:
        ディレクトリトラバーサル攻撃に使用されるパターン
    """
    return [
        "../../../etc/passwd.jpg",
        "..\\..\\..\\windows\\system32\\config.jpg",
        "./../../secret.png",
        "foo/../bar.jpg",
        "../../sensitive/data.jpeg",
        "..%2F..%2F..%2Fetc%2Fpasswd.jpg",  # URL encoded
        "....//....//....//etc/passwd.jpg",
        "..//..//..//etc/passwd.jpg"
    ]


@pytest.fixture
def invalid_filename_chars() -> list[str]:
    """
    ファイル名として不正な文字を含むパターン

    Returns:
        OSで使用できない文字を含むファイル名
    """
    return [
        "file<name>.jpg",
        "image>test.png",
        'file"name.jpeg',
        "test:file.jpg",
        "image|test.png",
        "file?name.jpg",
        "test*file.png",
        "null\x00byte.jpg",
        "control\x01char.png"
    ]


# ===== AWS モックフィクスチャ =====

@pytest.fixture
def mock_s3_client() -> Generator[MagicMock, None, None]:
    """
    S3クライアントのモック

    Yields:
        モックされたboto3 S3クライアント

    使用例:
        def test_upload(mock_s3_client):
            mock_s3_client.generate_presigned_url.return_value = "https://..."
    """
    with patch('boto3.client') as mock:
        mock_s3 = MagicMock()
        mock.return_value = mock_s3

        # デフォルトの戻り値を設定
        mock_s3.generate_presigned_url.return_value = "https://test-bucket.s3.amazonaws.com/test.jpg"

        yield mock_s3


@pytest.fixture
def mock_dynamodb_resource() -> Generator[MagicMock, None, None]:
    """
    DynamoDB resourceのモック

    Yields:
        モックされたboto3 DynamoDB resource

    使用例:
        def test_create_puzzle(mock_dynamodb_resource):
            table = mock_dynamodb_resource.Table.return_value
            table.put_item.return_value = {...}
    """
    with patch('boto3.resource') as mock:
        mock_dynamodb = MagicMock()
        mock.return_value = mock_dynamodb

        # テーブルモックの作成
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # デフォルトの戻り値
        mock_table.put_item.return_value = {}
        mock_table.get_item.return_value = {'Item': {
            'userId': 'test-user',
            'puzzleId': 'test-puzzle-id',
            'puzzleName': 'Test Puzzle',
            'pieceCount': 300,
            'status': 'pending'
        }}
        mock_table.query.return_value = {'Items': []}

        yield mock_dynamodb


@pytest.fixture
def mock_puzzle_service(mock_s3_client, mock_dynamodb_resource) -> MagicMock:
    """
    PuzzleServiceのモック（AWS依存を含む）

    Args:
        mock_s3_client: S3クライアントモック
        mock_dynamodb_resource: DynamoDBリソースモック

    Returns:
        完全にモックされたPuzzleServiceインスタンス
    """
    from app.services.puzzle_service import PuzzleService

    service = PuzzleService(
        s3_bucket_name="test-bucket",
        puzzles_table_name="test-table",
        environment="test"
    )

    return service


# ===== ユーティリティフィクスチャ =====

@pytest.fixture
def sample_puzzle_id() -> str:
    """テスト用のサンプルパズルID"""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_user_id() -> str:
    """テスト用のサンプルユーザーID"""
    return "test-user-123"


# ===== テストマーカー用の設定 =====

def pytest_configure(config):
    """
    pytest起動時の初期化処理

    カスタムマーカーの説明をここで追加登録できます
    """
    config.addinivalue_line(
        "markers", "unit: 単体テスト（外部依存なし）"
    )
    config.addinivalue_line(
        "markers", "integration: 統合テスト（AWS等の外部サービスをモック）"
    )
    config.addinivalue_line(
        "markers", "security: セキュリティテスト"
    )
    config.addinivalue_line(
        "markers", "validation: バリデーションテスト"
    )
