"""
Lambda wrapper for puzzle registration

This is a thin wrapper that uses the same business logic as FastAPI.
The actual implementation is in app.services.puzzle_service
"""

import json
import os
import sys
from decimal import Decimal

# appパッケージをインポートするためbackend/を追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.puzzle_service import PuzzleService
from app.core.logger import setup_logger


class DecimalEncoder(json.JSONEncoder):
    """
    DynamoDBから取得したDecimal型をJSON変換可能な形式に変換するエンコーダー

    DynamoDBはすべての数値をDecimal型で返すため、標準のjson.dumps()では
    シリアライズできない。このエンコーダーを使用することで、
    - 整数値のDecimal → int
    - 小数値のDecimal → float
    に自動変換される。
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # 整数値の場合はintに、小数値の場合はfloatに変換
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

# ロガーの初期化
logger = setup_logger(__name__)

# 環境変数
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
PUZZLES_TABLE_NAME = os.environ['PUZZLES_TABLE_NAME']
PIECES_TABLE_NAME = os.environ['PIECES_TABLE_NAME']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# CORS設定用の許可オリジンを環境変数から取得
# 開発環境: localhost のみ許可
# 本番環境: 実際のフロントエンドドメインを設定
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000')
# カンマ区切りをリストに変換（一度だけ処理）
ALLOWED_ORIGINS_LIST = [origin.strip() for origin in ALLOWED_ORIGINS.split(',')]

# サービスの初期化
puzzle_service = PuzzleService(
    s3_bucket_name=S3_BUCKET_NAME,
    puzzles_table_name=PUZZLES_TABLE_NAME,
    environment=ENVIRONMENT
)


def handler(event, context):
    """
    Lambda handler for puzzle operations

    Handles multiple endpoints:
    - POST /puzzles - Create a new puzzle
    - GET /users/{userId}/puzzles - List user's puzzles
    """
    logger.info(
        "Lambda invoked",
        extra={
            "request_id": context.aws_request_id if context else None,
            "http_method": event.get('httpMethod'),
            "path": event.get('path')
        }
    )

    try:
        http_method = event.get('httpMethod')
        path = event.get('path', '')

        # ルーティング
        if http_method == 'POST' and path == '/puzzles':
            return handle_create_puzzle(event, context)
        elif http_method == 'POST' and '/puzzles/' in path and path.endswith('/upload'):
            return handle_generate_upload_url(event, context)
        elif http_method == 'GET' and '/users/' in path and path.endswith('/puzzles'):
            return handle_list_puzzles(event, context)
        elif http_method == 'GET' and path.startswith('/puzzles/'):
            return handle_get_puzzle(event, context)
        else:
            return create_response(event, 404, {
                'error': 'Not found',
                'path': path,
                'method': http_method
            })

    except Exception as e:
        # 予期しないエラー
        import traceback
        logger.error(
            "Unexpected error in Lambda handler",
            extra={
                "request_id": context.aws_request_id if context else None,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

        # 本番環境ではエラー詳細を隠す
        error_body = {'error': 'Internal server error'}
        if ENVIRONMENT != 'prod':
            error_body['details'] = str(e)

        return create_response(event, 500, error_body)


def handle_create_puzzle(event, context):
    """パズル作成を処理"""
    try:
        # リクエストボディを解析
        body = json.loads(event.get('body', '{}'))

        # パラメータを抽出
        piece_count = body.get('pieceCount')
        puzzle_name = body.get('puzzleName')
        user_id = body.get('userId', 'anonymous')

        # 必須パラメータを検証
        if not piece_count:
            return create_response(event, 400, {
                'error': 'pieceCount is required'
            })

        if not puzzle_name:
            return create_response(event, 400, {
                'error': 'puzzleName is required'
            })

        # ビジネスロジックを呼び出し（画像なしでパズル作成）
        result = puzzle_service.create_puzzle(
            piece_count=piece_count,
            puzzle_name=puzzle_name,
            user_id=user_id
        )

        # 成功レスポンスを返す
        return create_response(event, 200, result)

    except ValueError as e:
        # バリデーションエラー
        logger.warning(
            "Validation error",
            extra={
                "request_id": context.aws_request_id if context else None,
                "error": str(e)
            }
        )
        return create_response(event, 400, {
            'error': str(e)
        })


def handle_generate_upload_url(event, context):
    """アップロード用のPre-signed URLを生成"""
    try:
        # パスからpuzzleIdを取得
        # /puzzles/{puzzleId}/upload の形式
        path = event.get('path', '')
        path_parts = path.split('/')

        # pathは "/puzzles/048db3cc-12b4-4372-b9a8-06c3924aaac0/upload" のような形式
        if len(path_parts) >= 3 and path_parts[1] == 'puzzles':
            puzzle_id = path_parts[2]
        else:
            return create_response(event, 400, {
                'error': 'Invalid path format'
            })

        # リクエストボディを解析
        body = json.loads(event.get('body', '{}'))

        # パラメータを抽出
        file_name = body.get('fileName', 'puzzle.jpg')
        user_id = body.get('userId', 'anonymous')

        logger.info(
            "Generating upload URL",
            extra={
                "request_id": context.aws_request_id if context else None,
                "puzzle_id": puzzle_id,
                "user_id": user_id,
                "file_name": file_name
            }
        )

        # ビジネスロジックを呼び出し
        result = puzzle_service.generate_upload_url(
            puzzle_id=puzzle_id,
            file_name=file_name,
            user_id=user_id
        )

        # 成功レスポンスを返す
        return create_response(event, 200, result)

    except ValueError as e:
        # バリデーションエラー（パズルが見つからないなど）
        logger.warning(
            "Validation error in generate_upload_url",
            extra={
                "request_id": context.aws_request_id if context else None,
                "error": str(e)
            }
        )
        return create_response(event, 400, {
            'error': str(e)
        })
    except Exception as e:
        import traceback
        logger.error(
            "Error generating upload URL",
            extra={
                "request_id": context.aws_request_id if context else None,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return create_response(event, 500, {
            'error': 'Failed to generate upload URL',
            'details': str(e) if ENVIRONMENT != 'prod' else None
        })


def handle_get_puzzle(event, context):
    """パズルの個別情報を取得"""
    try:
        # パスからpuzzleIdを取得
        # /puzzles/{puzzleId} の形式
        path = event.get('path', '')
        path_parts = path.split('/')

        # pathは "/puzzles/14d1c83f-d562-4478-8e23-642db20d6b39" のような形式
        if len(path_parts) >= 3 and path_parts[1] == 'puzzles':
            puzzle_id = path_parts[2]
        else:
            return create_response(event, 400, {
                'error': 'Invalid path format'
            })

        # クエリパラメータからuser_idを取得
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id', 'anonymous')

        logger.info(
            "Getting puzzle",
            extra={
                "request_id": context.aws_request_id if context else None,
                "puzzle_id": puzzle_id,
                "user_id": user_id
            }
        )

        # ビジネスロジックを呼び出し
        puzzle = puzzle_service.get_puzzle(user_id=user_id, puzzle_id=puzzle_id)

        if not puzzle:
            return create_response(event, 404, {
                'error': 'Puzzle not found',
                'puzzleId': puzzle_id
            })

        # 成功レスポンスを返す
        return create_response(event, 200, puzzle)

    except Exception as e:
        import traceback
        logger.error(
            "Error getting puzzle",
            extra={
                "request_id": context.aws_request_id if context else None,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return create_response(event, 500, {
            'error': 'Failed to get puzzle',
            'details': str(e) if ENVIRONMENT != 'prod' else None
        })


def handle_list_puzzles(event, context):
    """ユーザーのパズル一覧を取得"""
    try:
        logger.info("Step 1: Extracting path parameters")
        # パスパラメータからuserIdを取得
        # /users/{userId}/puzzles の形式
        path = event.get('path', '')
        path_parts = path.split('/')
        logger.info(f"Path: {path}, Parts: {path_parts}")

        # pathは "/users/anonymous/puzzles" のような形式
        if len(path_parts) >= 3 and path_parts[1] == 'users':
            user_id = path_parts[2]
            logger.info(f"Step 2: Extracted user_id: {user_id}")
        else:
            logger.error(f"Invalid path format: {path}")
            return create_response(event, 400, {
                'error': 'Invalid path format'
            })

        # ビジネスロジックを呼び出し
        logger.info(f"Step 3: Calling puzzle_service.list_puzzles for user_id: {user_id}")
        puzzles_list = puzzle_service.list_puzzles(user_id=user_id)
        logger.info(f"Step 4: Got {len(puzzles_list)} puzzles")

        # 成功レスポンスを返す
        logger.info("Step 5: Creating response")
        return create_response(event, 200, {
            'userId': user_id,
            'count': len(puzzles_list),
            'puzzles': puzzles_list
        })

    except Exception as e:
        import traceback
        logger.error(
            "Error listing puzzles",
            extra={
                "request_id": context.aws_request_id if context else None,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        return create_response(event, 500, {
            'error': 'Failed to list puzzles',
            'details': str(e) if ENVIRONMENT != 'prod' else None
        })


def create_response(event, status_code, body):
    """
    Create HTTP response with CORS headers

    CORSヘッダーはリクエストのOriginに基づいて動的に設定される
    """
    # リクエストのOriginヘッダーを取得（大文字小文字を考慮）
    headers = event.get('headers', {})
    request_origin = headers.get('origin') or headers.get('Origin') or ''

    # リクエストOriginが許可リストに含まれているか確認
    if request_origin in ALLOWED_ORIGINS_LIST:
        cors_origin = request_origin
    else:
        # デフォルトは最初のオリジン（開発環境用）
        cors_origin = ALLOWED_ORIGINS_LIST[0] if ALLOWED_ORIGINS_LIST else 'http://localhost:3000'

    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': cors_origin,  # リクエストOriginに基づいて動的に設定
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
            'Access-Control-Allow-Credentials': 'true'  # credentialsをサポート
        },
        'body': json.dumps(body, cls=DecimalEncoder)  # DynamoDBのDecimal型を自動変換
    }
