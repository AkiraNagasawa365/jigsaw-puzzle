"""
Puzzle API routes

パズル関連のAPIエンドポイントを定義します。
"""

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.logger import setup_logger
from app.core.schemas import (
    PuzzleCreateRequest,
    PuzzleCreateResponse,
    UploadUrlRequest,
    UploadUrlResponse,
    ErrorResponse
)
from app.services.puzzle_service import PuzzleService

# ロガーの初期化
logger = setup_logger(__name__)

# ルーターの作成
router = APIRouter(prefix="/puzzles", tags=["puzzles"])

# サービスの初期化
puzzle_service = PuzzleService(
    s3_bucket_name=settings.s3_bucket_name,
    puzzles_table_name=settings.puzzles_table_name,
    environment=settings.environment
)


@router.post("", response_model=PuzzleCreateResponse, responses={
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
        logger.error(
            "Error creating puzzle",
            extra={
                "puzzle_name": request.puzzleName,
                "piece_count": request.pieceCount,
                "user_id": request.userId,
                "error": str(e)
            }
        )
        # 本番環境ではエラー詳細を隠す
        if settings.is_production:
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{puzzle_id}/upload", response_model=UploadUrlResponse, responses={
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

    Returns a pre-signed URL that is valid for 15 minutes.
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
        logger.error(
            "Error generating upload URL",
            extra={
                "puzzle_id": puzzle_id,
                "file_name": request.fileName,
                "user_id": request.userId,
                "error": str(e)
            }
        )
        # 本番環境ではエラー詳細を隠す
        if settings.is_production:
            raise HTTPException(status_code=500, detail="Internal server error")
        else:
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{puzzle_id}")
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
