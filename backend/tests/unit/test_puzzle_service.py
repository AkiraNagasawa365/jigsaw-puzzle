"""
PuzzleServiceのビジネスロジック単体テスト

AWS依存（S3, DynamoDB）をモックして、ビジネスロジックの正しさを検証します。

テスト対象:
1. create_puzzle() - パズル作成
2. generate_upload_url() - Pre-signed URL生成
3. get_puzzle() - パズル取得
4. list_puzzles() - パズル一覧取得

テスト戦略:
- motoを使ったAWSモック（実際のAWSを使わずにテスト）
- 正常系: 期待通りの動作をするか
- 異常系: エラーハンドリングが正しいか
- エッジケース: 境界値や特殊なケース
"""

import pytest
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime
from botocore.exceptions import ClientError

from app.services.puzzle_service import PuzzleService


# ===================================================================
# PuzzleServiceのセットアップ
# ===================================================================

@pytest.fixture
def puzzle_service():
    """
    テスト用のPuzzleServiceインスタンス

    AWS依存はモックを使用
    """
    with patch('boto3.client') as mock_client, \
         patch('boto3.resource') as mock_resource:

        # S3クライアントのモック
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3

        # DynamoDBリソースのモック
        mock_dynamodb = MagicMock()
        mock_resource.return_value = mock_dynamodb

        # DynamoDBテーブルのモック
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table

        # サービスインスタンスを作成
        service = PuzzleService(
            s3_bucket_name='test-bucket',
            puzzles_table_name='test-puzzles-table',
            environment='test'
        )

        # モックオブジェクトをサービスに関連付け（テストで使用）
        service._mock_s3 = mock_s3
        service._mock_table = mock_table

        yield service


# ===================================================================
# create_puzzle() のテスト
# ===================================================================

class TestCreatePuzzle:
    """
    パズル作成機能のテスト

    検証項目:
    - 正常なパズル作成
    - DynamoDBへの保存
    - 無効なpieceCountの拒否
    - エラーハンドリング
    """

    @pytest.mark.unit
    def test_create_puzzle_success(self, puzzle_service, sample_user_id):
        """
        正常系: パズルが正しく作成される

        検証:
        - DynamoDB put_itemが呼ばれる
        - 正しいレスポンスが返る
        - UUIDが生成される
        """
        # モックの設定
        puzzle_service._mock_table.put_item.return_value = {}

        # パズル作成
        result = puzzle_service.create_puzzle(
            piece_count=300,
            puzzle_name="Test Puzzle",
            user_id=sample_user_id
        )

        # 検証: DynamoDBへの保存が呼ばれた
        puzzle_service._mock_table.put_item.assert_called_once()
        call_args = puzzle_service._mock_table.put_item.call_args[1]
        item = call_args['Item']

        # 検証: 保存されたデータが正しい
        assert item['userId'] == sample_user_id
        assert item['puzzleName'] == "Test Puzzle"
        assert item['pieceCount'] == 300
        assert item['status'] == 'pending'
        assert 'puzzleId' in item
        assert 'createdAt' in item
        assert 'updatedAt' in item

        # 検証: レスポンスが正しい
        assert result['puzzleName'] == "Test Puzzle"
        assert result['pieceCount'] == 300
        assert result['status'] == 'pending'
        assert 'puzzleId' in result
        assert 'message' in result

    @pytest.mark.unit
    def test_create_puzzle_all_valid_piece_counts(self, puzzle_service):
        """
        正常系: 全ての有効なpieceCountでパズル作成

        検証: [100, 300, 500, 1000, 2000] 全てが成功する
        """
        valid_counts = [100, 300, 500, 1000, 2000]

        puzzle_service._mock_table.put_item.return_value = {}

        for count in valid_counts:
            result = puzzle_service.create_puzzle(
                piece_count=count,
                puzzle_name=f"Puzzle {count}",
                user_id="test-user"
            )
            assert result['pieceCount'] == count, \
                f"pieceCount={count} should be accepted"

    @pytest.mark.unit
    def test_create_puzzle_invalid_piece_count(self, puzzle_service):
        """
        異常系: 無効なpieceCountを拒否

        検証: 有効なリストに無い値はValueErrorになる
        """
        invalid_counts = [50, 150, 250, 999, 2001, 3000]

        for count in invalid_counts:
            with pytest.raises(ValueError) as exc_info:
                puzzle_service.create_puzzle(
                    piece_count=count,
                    puzzle_name="Test",
                    user_id="test-user"
                )
            assert "pieceCount must be one of" in str(exc_info.value), \
                f"pieceCount={count} should raise ValueError"

    @pytest.mark.unit
    def test_create_puzzle_default_user_id(self, puzzle_service):
        """
        正常系: userIdのデフォルト値

        検証: user_idを指定しない場合、'anonymous'になる
        """
        puzzle_service._mock_table.put_item.return_value = {}

        result = puzzle_service.create_puzzle(
            piece_count=300,
            puzzle_name="Test Puzzle"
        )

        call_args = puzzle_service._mock_table.put_item.call_args[1]
        item = call_args['Item']

        assert item['userId'] == 'anonymous'

    @pytest.mark.unit
    def test_create_puzzle_dynamodb_error(self, puzzle_service):
        """
        異常系: DynamoDB保存エラー

        検証: DynamoDBエラー時にClientErrorが発生する
        """
        # DynamoDBエラーをシミュレート
        puzzle_service._mock_table.put_item.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Database error'}},
            'put_item'
        )

        with pytest.raises(ClientError):
            puzzle_service.create_puzzle(
                piece_count=300,
                puzzle_name="Test",
                user_id="test-user"
            )

    @pytest.mark.unit
    def test_create_puzzle_generates_unique_ids(self, puzzle_service):
        """
        正常系: パズルIDがユニークに生成される

        検証: 複数回呼び出しても異なるIDが生成される
        """
        puzzle_service._mock_table.put_item.return_value = {}

        puzzle_ids = set()
        for i in range(10):
            result = puzzle_service.create_puzzle(
                piece_count=300,
                puzzle_name=f"Test {i}",
                user_id="test-user"
            )
            puzzle_ids.add(result['puzzleId'])

        # 全てのIDがユニーク
        assert len(puzzle_ids) == 10


# ===================================================================
# generate_upload_url() のテスト
# ===================================================================

class TestGenerateUploadUrl:
    """
    Pre-signed URL生成のテスト

    検証項目:
    - 正常なURL生成
    - パズルの存在確認
    - DynamoDB更新
    - 拡張子とMIME typeのマッピング
    - エラーハンドリング
    """

    @pytest.mark.unit
    def test_generate_upload_url_success(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: Pre-signed URLが正しく生成される

        検証:
        - S3 generate_presigned_url が呼ばれる
        - DynamoDB update_item が呼ばれる
        - 正しいレスポンスが返る
        """
        # モックの設定: パズルが存在する
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {
                'userId': sample_user_id,
                'puzzleId': sample_puzzle_id,
                'puzzleName': 'Test Puzzle',
                'pieceCount': 300,
                'status': 'pending'
            }
        }

        # モックの設定: Pre-signed URL生成
        test_url = f"https://test-bucket.s3.amazonaws.com/puzzles/{sample_puzzle_id}.jpg"
        puzzle_service._mock_s3.generate_presigned_url.return_value = test_url

        # モックの設定: DynamoDB更新成功
        puzzle_service._mock_table.update_item.return_value = {}

        # URL生成
        result = puzzle_service.generate_upload_url(
            puzzle_id=sample_puzzle_id,
            file_name="test.jpg",
            user_id=sample_user_id
        )

        # 検証: S3が呼ばれた
        puzzle_service._mock_s3.generate_presigned_url.assert_called_once()

        # 検証: DynamoDBが更新された
        puzzle_service._mock_table.update_item.assert_called_once()

        # 検証: レスポンスが正しい
        assert result['puzzleId'] == sample_puzzle_id
        assert result['uploadUrl'] == test_url
        assert result['expiresIn'] == 900  # 15分
        assert 'message' in result

    @pytest.mark.unit
    def test_generate_upload_url_jpg_mime_type(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: .jpg拡張子で正しいMIME typeが設定される

        検証: Content-Type が 'image/jpeg' になる
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }
        puzzle_service._mock_s3.generate_presigned_url.return_value = "https://test.com/upload"
        puzzle_service._mock_table.update_item.return_value = {}

        puzzle_service.generate_upload_url(
            puzzle_id=sample_puzzle_id,
            file_name="photo.jpg",
            user_id=sample_user_id
        )

        # S3呼び出しの引数を確認
        call_args = puzzle_service._mock_s3.generate_presigned_url.call_args
        params = call_args[1]['Params']

        assert params['ContentType'] == 'image/jpeg'

    @pytest.mark.unit
    def test_generate_upload_url_jpeg_mime_type(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: .jpeg拡張子で正しいMIME typeが設定される

        検証: Content-Type が 'image/jpeg' になる
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }
        puzzle_service._mock_s3.generate_presigned_url.return_value = "https://test.com/upload"
        puzzle_service._mock_table.update_item.return_value = {}

        puzzle_service.generate_upload_url(
            puzzle_id=sample_puzzle_id,
            file_name="image.jpeg",
            user_id=sample_user_id
        )

        call_args = puzzle_service._mock_s3.generate_presigned_url.call_args
        params = call_args[1]['Params']

        assert params['ContentType'] == 'image/jpeg'

    @pytest.mark.unit
    def test_generate_upload_url_png_mime_type(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: .png拡張子で正しいMIME typeが設定される

        検証: Content-Type が 'image/png' になる
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }
        puzzle_service._mock_s3.generate_presigned_url.return_value = "https://test.com/upload"
        puzzle_service._mock_table.update_item.return_value = {}

        puzzle_service.generate_upload_url(
            puzzle_id=sample_puzzle_id,
            file_name="screenshot.png",
            user_id=sample_user_id
        )

        call_args = puzzle_service._mock_s3.generate_presigned_url.call_args
        params = call_args[1]['Params']

        assert params['ContentType'] == 'image/png'

    @pytest.mark.unit
    def test_generate_upload_url_expires_in_900_seconds(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: URLの有効期限が900秒（15分）

        検証: ExpiresIn=900 が設定される
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }
        puzzle_service._mock_s3.generate_presigned_url.return_value = "https://test.com/upload"
        puzzle_service._mock_table.update_item.return_value = {}

        puzzle_service.generate_upload_url(
            puzzle_id=sample_puzzle_id,
            file_name="test.jpg",
            user_id=sample_user_id
        )

        call_args = puzzle_service._mock_s3.generate_presigned_url.call_args

        assert call_args[1]['ExpiresIn'] == 900

    @pytest.mark.unit
    def test_generate_upload_url_puzzle_not_found(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        異常系: パズルが存在しない

        検証: ValueError が発生する
        """
        # パズルが見つからない
        puzzle_service._mock_table.get_item.return_value = {}

        with pytest.raises(ValueError) as exc_info:
            puzzle_service.generate_upload_url(
                puzzle_id=sample_puzzle_id,
                file_name="test.jpg",
                user_id=sample_user_id
            )

        assert "Puzzle not found" in str(exc_info.value)

    @pytest.mark.unit
    def test_generate_upload_url_s3_error(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        異常系: S3エラー

        検証: S3エラー時にClientErrorが発生する
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }

        # S3エラーをシミュレート
        puzzle_service._mock_s3.generate_presigned_url.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'S3 error'}},
            'generate_presigned_url'
        )

        with pytest.raises(ClientError):
            puzzle_service.generate_upload_url(
                puzzle_id=sample_puzzle_id,
                file_name="test.jpg",
                user_id=sample_user_id
            )

    @pytest.mark.unit
    def test_generate_upload_url_dynamodb_update_error(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        異常系: DynamoDB更新エラー

        検証: 更新エラー時にClientErrorが発生する
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }
        puzzle_service._mock_s3.generate_presigned_url.return_value = "https://test.com/upload"

        # DynamoDB更新エラーをシミュレート
        puzzle_service._mock_table.update_item.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Update error'}},
            'update_item'
        )

        with pytest.raises(ClientError):
            puzzle_service.generate_upload_url(
                puzzle_id=sample_puzzle_id,
                file_name="test.jpg",
                user_id=sample_user_id
            )

    @pytest.mark.unit
    def test_generate_upload_url_updates_status_to_uploaded(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: パズルステータスが 'uploaded' に更新される

        検証: DynamoDB update_item で status='uploaded' が設定される
        """
        puzzle_service._mock_table.get_item.return_value = {
            'Item': {'userId': sample_user_id, 'puzzleId': sample_puzzle_id}
        }
        puzzle_service._mock_s3.generate_presigned_url.return_value = "https://test.com/upload"
        puzzle_service._mock_table.update_item.return_value = {}

        puzzle_service.generate_upload_url(
            puzzle_id=sample_puzzle_id,
            file_name="test.jpg",
            user_id=sample_user_id
        )

        # update_itemの引数を確認
        call_args = puzzle_service._mock_table.update_item.call_args[1]

        assert call_args['ExpressionAttributeValues'][':st'] == 'uploaded'


# ===================================================================
# get_puzzle() のテスト
# ===================================================================

class TestGetPuzzle:
    """
    パズル取得機能のテスト

    検証項目:
    - 正常な取得
    - パズルが見つからない場合
    - エラーハンドリング
    """

    @pytest.mark.unit
    def test_get_puzzle_success(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        正常系: パズルが正しく取得される

        検証: DynamoDBから取得したデータが返される
        """
        expected_puzzle = {
            'userId': sample_user_id,
            'puzzleId': sample_puzzle_id,
            'puzzleName': 'Test Puzzle',
            'pieceCount': 300,
            'status': 'pending',
            'createdAt': '2024-01-01T00:00:00',
            'updatedAt': '2024-01-01T00:00:00'
        }

        puzzle_service._mock_table.get_item.return_value = {
            'Item': expected_puzzle
        }

        result = puzzle_service.get_puzzle(
            user_id=sample_user_id,
            puzzle_id=sample_puzzle_id
        )

        assert result == expected_puzzle

    @pytest.mark.unit
    def test_get_puzzle_not_found(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        異常系: パズルが見つからない

        検証: None が返される
        """
        puzzle_service._mock_table.get_item.return_value = {}

        result = puzzle_service.get_puzzle(
            user_id=sample_user_id,
            puzzle_id=sample_puzzle_id
        )

        assert result is None

    @pytest.mark.unit
    def test_get_puzzle_dynamodb_error(self, puzzle_service, sample_puzzle_id, sample_user_id):
        """
        異常系: DynamoDBエラー

        検証: エラー時にNoneが返される（例外は握りつぶされる）
        """
        puzzle_service._mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'DB error'}},
            'get_item'
        )

        result = puzzle_service.get_puzzle(
            user_id=sample_user_id,
            puzzle_id=sample_puzzle_id
        )

        assert result is None


# ===================================================================
# list_puzzles() のテスト
# ===================================================================

class TestListPuzzles:
    """
    パズル一覧取得機能のテスト

    検証項目:
    - 正常な一覧取得
    - 空のリスト
    - エラーハンドリング
    """

    @pytest.mark.unit
    def test_list_puzzles_success(self, puzzle_service, sample_user_id):
        """
        正常系: パズル一覧が正しく取得される

        検証: DynamoDBから取得したリストが返される
        """
        expected_puzzles = [
            {
                'userId': sample_user_id,
                'puzzleId': 'puzzle-1',
                'puzzleName': 'Puzzle 1',
                'pieceCount': 300,
                'status': 'pending'
            },
            {
                'userId': sample_user_id,
                'puzzleId': 'puzzle-2',
                'puzzleName': 'Puzzle 2',
                'pieceCount': 500,
                'status': 'uploaded'
            }
        ]

        puzzle_service._mock_table.query.return_value = {
            'Items': expected_puzzles
        }

        result = puzzle_service.list_puzzles(user_id=sample_user_id)

        assert result == expected_puzzles
        assert len(result) == 2

    @pytest.mark.unit
    def test_list_puzzles_empty(self, puzzle_service, sample_user_id):
        """
        正常系: パズルが0件

        検証: 空のリストが返される
        """
        puzzle_service._mock_table.query.return_value = {
            'Items': []
        }

        result = puzzle_service.list_puzzles(user_id=sample_user_id)

        assert result == []
        assert len(result) == 0

    @pytest.mark.unit
    def test_list_puzzles_dynamodb_error(self, puzzle_service, sample_user_id):
        """
        異常系: DynamoDBエラー

        検証: エラー時に空リストが返される
        """
        puzzle_service._mock_table.query.side_effect = ClientError(
            {'Error': {'Code': 'InternalServerError', 'Message': 'Query error'}},
            'query'
        )

        result = puzzle_service.list_puzzles(user_id=sample_user_id)

        assert result == []

    @pytest.mark.unit
    def test_list_puzzles_query_called_with_correct_params(self, puzzle_service, sample_user_id):
        """
        正常系: DynamoDB queryが正しいパラメータで呼ばれる

        検証: userId でクエリが実行される
        """
        puzzle_service._mock_table.query.return_value = {'Items': []}

        puzzle_service.list_puzzles(user_id=sample_user_id)

        # query呼び出しを確認
        call_args = puzzle_service._mock_table.query.call_args[1]

        assert 'KeyConditionExpression' in call_args
        assert call_args['ExpressionAttributeValues'][':uid'] == sample_user_id
