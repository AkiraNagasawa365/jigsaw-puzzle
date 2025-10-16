"""
FastAPI application for local development

This is the local development server that uses the same business logic as Lambda.
Run with: uvicorn app:app --reload
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from puzzle_logic import PuzzleService

# Initialize FastAPI app
app = FastAPI(
    title="Jigsaw Puzzle API",
    description="API for managing jigsaw puzzles",
    version="1.0.0"
)

# CORS設定（開発用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では制限すること
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables (開発用のデフォルト値)
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'jigsaw-puzzle-dev-images')
PUZZLES_TABLE_NAME = os.environ.get('PUZZLES_TABLE_NAME', 'jigsaw-puzzle-dev-puzzles')
PIECES_TABLE_NAME = os.environ.get('PIECES_TABLE_NAME', 'jigsaw-puzzle-dev-pieces')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')

# Initialize service
puzzle_service = PuzzleService(
    s3_bucket_name=S3_BUCKET_NAME,
    puzzles_table_name=PUZZLES_TABLE_NAME,
    environment=ENVIRONMENT
)


# Request/Response models
class PuzzleCreateRequest(BaseModel):
    pieceCount: int = Field(..., description="Number of puzzle pieces", example=300)
    fileName: str = Field(default="puzzle.jpg", description="Image file name", example="my-puzzle.jpg")
    userId: str = Field(default="anonymous", description="User ID", example="user-123")


class PuzzleCreateResponse(BaseModel):
    puzzleId: str
    uploadUrl: str
    expiresIn: int
    message: str


class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None


# API Endpoints
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
    Create a new puzzle and get a pre-signed URL for image upload

    - **pieceCount**: Number of puzzle pieces (100, 300, 500, 1000, 2000)
    - **fileName**: Name of the image file (optional, default: puzzle.jpg)
    - **userId**: User ID (optional, default: anonymous)

    Returns a pre-signed URL that is valid for 5 minutes.
    """
    try:
        result = puzzle_service.register_puzzle(
            piece_count=request.pieceCount,
            file_name=request.fileName,
            user_id=request.userId
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"Error: {str(e)}")
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


# Debug/Development endpoints
@app.get("/debug/config")
def get_config():
    """Get current configuration (development only)"""
    return {
        "s3BucketName": S3_BUCKET_NAME,
        "puzzlesTableName": PUZZLES_TABLE_NAME,
        "piecesTableName": PIECES_TABLE_NAME,
        "environment": ENVIRONMENT
    }


# Run locally with: uvicorn app:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
