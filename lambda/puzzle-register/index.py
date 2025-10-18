"""
Lambda wrapper for puzzle registration

This is a thin wrapper that uses the same business logic as FastAPI.
The actual implementation is in puzzle_logic.py
"""

import json
import os
import sys

# puzzle_logicをインポートするためbackendディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from puzzle_logic import PuzzleService

# 環境変数
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
PUZZLES_TABLE_NAME = os.environ['PUZZLES_TABLE_NAME']
PIECES_TABLE_NAME = os.environ['PIECES_TABLE_NAME']
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

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
    print(f"Event: {json.dumps(event)}")

    try:
        # リクエストボディを解析
        body = json.loads(event.get('body', '{}'))

        # パラメータを抽出
        piece_count = body.get('pieceCount')
        puzzle_name = body.get('puzzleName')
        file_name = body.get('fileName', 'puzzle.jpg')
        user_id = body.get('userId', 'anonymous')

        # 必須パラメータを検証
        if not piece_count:
            return create_response(400, {
                'error': 'pieceCount is required'
            })

        if not puzzle_name:
            return create_response(400, {
                'error': 'puzzleName is required'
            })

        # ビジネスロジックを呼び出し
        result = puzzle_service.register_puzzle(
            piece_count=piece_count,
            puzzle_name=puzzle_name,
            file_name=file_name,
            user_id=user_id
        )

        # 成功レスポンスを返す
        return create_response(200, result)

    except ValueError as e:
        # バリデーションエラー
        print(f"Validation error: {str(e)}")
        return create_response(400, {
            'error': str(e)
        })

    except Exception as e:
        # 予期しないエラー
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

        return create_response(500, {
            'error': 'Internal server error',
            'details': str(e)
        })


def create_response(status_code, body):
    """
    Create HTTP response with CORS headers
    """
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # TODO: 本番環境では制限すること
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(body)
    }
