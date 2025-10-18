"""
FastAPI application entry point

This is the main application file that initializes FastAPI and registers routes.
Run with: uvicorn app.api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import puzzles


# FastAPIアプリの初期化
app = FastAPI(
    title="Jigsaw Puzzle API",
    description="API for managing jigsaw puzzles",
    version="1.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,  # 環境変数で制御
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ルーターの登録
app.include_router(puzzles.router)


# ルートエンドポイント
@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Jigsaw Puzzle API",
        "environment": settings.environment
    }


# ユーザーのパズル一覧取得エンドポイント
@app.get("/users/{user_id}/puzzles")
def get_user_puzzles(user_id: str):
    """
    Get all puzzles for a specific user

    - **user_id**: User ID (path parameter)

    This is an alias for GET /puzzles?user_id={user_id}
    Provided for RESTful API design.
    """
    from app.services.puzzle_service import PuzzleService

    puzzle_service = PuzzleService(
        s3_bucket_name=settings.s3_bucket_name,
        puzzles_table_name=settings.puzzles_table_name,
        environment=settings.environment
    )

    puzzles_list = puzzle_service.list_puzzles(user_id=user_id)
    return {
        "userId": user_id,
        "count": len(puzzles_list),
        "puzzles": puzzles_list
    }


# デバッグ/開発用エンドポイント
@app.get("/debug/config")
def get_config():
    """Get current configuration (development only)"""
    if settings.is_production:
        return {"error": "Configuration endpoint is disabled in production"}

    return {
        "s3BucketName": settings.s3_bucket_name,
        "puzzlesTableName": settings.puzzles_table_name,
        "piecesTableName": settings.pieces_table_name,
        "environment": settings.environment,
        "allowedOrigins": settings.allowed_origins
    }


# ローカル実行用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
