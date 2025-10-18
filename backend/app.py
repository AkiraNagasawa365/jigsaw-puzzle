"""
FastAPI application for local development

This is the local development server that uses the same business logic as Lambda.
Run with: uvicorn app:app --reload
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from puzzle_logic import PuzzleService
from schemas import (
    PuzzleCreateRequest,
    PuzzleCreateResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    ErrorResponse
)

# FastAPIアプリの初期化
app = FastAPI(
    title="Jigsaw Puzzle API",
    description="API for managing jigsaw puzzles",
    version="1.0.0"
)

# Environment variables (開発用のデフォルト値)
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'jigsaw-puzzle-dev-images')
PUZZLES_TABLE_NAME = os.environ.get('PUZZLES_TABLE_NAME', 'jigsaw-puzzle-dev-puzzles')
PIECES_TABLE_NAME = os.environ.get('PIECES_TABLE_NAME', 'jigsaw-puzzle-dev-pieces')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# CORS設定用の許可オリジンを環境変数から取得
# 開発環境: localhost のみ許可
# 本番環境: 実際のフロントエンドドメインを設定
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000').split(',')

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 環境変数で制御
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# サービスの初期化
puzzle_service = PuzzleService(
    s3_bucket_name=S3_BUCKET_NAME,
    puzzles_table_name=PUZZLES_TABLE_NAME,
    environment=ENVIRONMENT
)


# APIエンドポイント
@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Jigsaw Puzzle API",
        "environment": ENVIRONMENT
    }


@app.post("/puzzles", response_model=PuzzleCreateResponse, responses={
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
def create_puzzle(request: PuzzleCreateRequest):
    """
    Create a new puzzle (without image)

    - **puzzleName**: Name of the puzzle project
    - **pieceCount**: Number of puzzle pieces (100, 300, 500, 1000, 2000)
    - **userId**: User ID (optional, default: anonymous)

    After creating the puzzle, use POST /puzzles/{puzzleId}/upload to upload an image.
    """
    try:
        result = puzzle_service.create_puzzle(
            piece_count=request.pieceCount,
            puzzle_name=request.puzzleName,
            user_id=request.userId
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"Error: {str(e)}")
        # 本番環境ではエラー詳細を隠す
        if ENVIRONMENT == 'prod':
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/puzzles/{puzzle_id}/upload", response_model=UploadUrlResponse, responses={
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
def upload_puzzle_image(puzzle_id: str, request: UploadUrlRequest):
    """
    Get a pre-signed URL to upload an image for an existing puzzle

    - **puzzle_id**: Puzzle ID (path parameter)
    - **fileName**: Name of the image file (optional, default: puzzle.jpg)
    - **userId**: User ID (optional, default: anonymous)

    Returns a pre-signed URL that is valid for 1 hour.
    """
    try:
        result = puzzle_service.generate_upload_url(
            puzzle_id=puzzle_id,
            file_name=request.fileName,
            user_id=request.userId
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except Exception as e:
        print(f"Error: {str(e)}")
        # 本番環境ではエラー詳細を隠す
        if ENVIRONMENT == 'prod':
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/puzzles/{puzzle_id}")
def get_puzzle(puzzle_id: str, user_id: str = "anonymous"):
    """
    Get puzzle information by ID

    - **puzzle_id**: Puzzle ID
    - **user_id**: User ID (query parameter, default: anonymous)
    """
    puzzle = puzzle_service.get_puzzle(user_id=user_id, puzzle_id=puzzle_id)

    if not puzzle:
        raise HTTPException(status_code=404, detail="Puzzle not found")

    return puzzle


@app.get("/users/{user_id}/puzzles")
def list_puzzles(user_id: str):
    """
    List all puzzles for a user

    - **user_id**: User ID
    """
    puzzles = puzzle_service.list_puzzles(user_id=user_id)
    return {
        "userId": user_id,
        "count": len(puzzles),
        "puzzles": puzzles
    }


# デバッグ/開発用エンドポイント
@app.get("/debug/config")
def get_config():
    """Get current configuration (development only)"""
    return {
        "s3BucketName": S3_BUCKET_NAME,
        "puzzlesTableName": PUZZLES_TABLE_NAME,
        "piecesTableName": PIECES_TABLE_NAME,
        "environment": ENVIRONMENT
    }


# ローカル実行: uvicorn app:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
