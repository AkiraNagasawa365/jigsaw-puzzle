"""
Lambda wrapper for puzzle registration

This is a thin wrapper that uses the same business logic as FastAPI.
The actual implementation is in app.services.puzzle_service
"""

import json
import os
import sys

# appパッケージをインポートするためbackend/を追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.puzzle_service import PuzzleService
from app.core.logger import setup_logger

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
    Lambda handler for puzzle registration

    This is a thin wrapper around puzzle_logic.PuzzleService
    """
    logger.info(
        "Lambda invoked",
        extra={
            "request_id": context.request_id if context else None,
            "http_method": event.get('httpMethod'),
            "path": event.get('path')
        }
    )

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
                "request_id": context.request_id if context else None,
                "error": str(e),
                "piece_count": body.get('pieceCount'),
                "puzzle_name": body.get('puzzleName'),
                "user_id": body.get('userId', 'anonymous')
            }
        )
        return create_response(event, 400, {
            'error': str(e)
        })

    except Exception as e:
        # 予期しないエラー
        import traceback
        logger.error(
            "Unexpected error in Lambda handler",
            extra={
                "request_id": context.request_id if context else None,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )

        # 本番環境ではエラー詳細を隠す
        error_body = {'error': 'Internal server error'}
        if ENVIRONMENT != 'prod':
            error_body['details'] = str(e)

        return create_response(event, 500, error_body)


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
        'body': json.dumps(body)
    }
