"""
API request/response schemas using Pydantic

このモジュールはAPIのリクエスト・レスポンスの型定義とバリデーションを提供します。
FastAPIとLambda関数の両方から使用されます。
"""

from typing import Optional
from pydantic import BaseModel, Field


# パズル作成リクエスト
class PuzzleCreateRequest(BaseModel):
    """パズル作成リクエスト（画像なし）"""
    puzzleName: str = Field(
        ...,
        description="パズルプロジェクト名",
        example="富士山の風景",
        min_length=1,
        max_length=100
    )
    pieceCount: int = Field(
        ...,
        description="パズルのピース数",
        example=300,
        ge=100,
        le=2000
    )
    userId: str = Field(
        default="anonymous",
        description="ユーザーID",
        example="user-123"
    )


# パズル作成レスポンス
class PuzzleCreateResponse(BaseModel):
    """パズル作成レスポンス"""
    puzzleId: str
    puzzleName: str
    pieceCount: int
    status: str
    message: str


# 画像アップロードURLリクエスト
class UploadUrlRequest(BaseModel):
    """画像アップロード用のPre-signed URL取得リクエスト"""
    fileName: str = Field(
        default="puzzle.jpg",
        description="画像ファイル名",
        example="my-puzzle.jpg"
    )
    userId: str = Field(
        default="anonymous",
        description="ユーザーID",
        example="user-123"
    )


# 画像アップロードURLレスポンス
class UploadUrlResponse(BaseModel):
    """画像アップロード用のPre-signed URLレスポンス"""
    puzzleId: str
    uploadUrl: str
    expiresIn: int
    message: str


# エラーレスポンス
class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str
    details: Optional[str] = None
