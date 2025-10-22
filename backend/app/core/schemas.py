"""
API request/response schemas using Pydantic

このモジュールはAPIのリクエスト・レスポンスの型定義とバリデーションを提供します。
FastAPIとLambda関数の両方から使用されます。
"""

import re
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


# パズル作成リクエスト
class PuzzleCreateRequest(BaseModel):
    """パズル作成リクエスト（画像なし）"""
    puzzleName: str = Field(
        ...,
        description="パズルプロジェクト名",
        min_length=1,
        max_length=100,
        json_schema_extra={"example": "富士山の風景"}
    )
    pieceCount: Literal[100, 300, 500, 1000, 2000] = Field(
        ...,
        description="パズルのピース数（100, 300, 500, 1000, 2000のいずれか）",
        json_schema_extra={"example": 300}
    )
    userId: str = Field(
        default="anonymous",
        description="ユーザーID",
        max_length=50,
        json_schema_extra={"example": "user-123"}
    )

    @field_validator('puzzleName')
    @classmethod
    def validate_puzzle_name(cls, v: str) -> str:
        """パズル名のバリデーション（XSS対策）"""
        # 最初にトリミング
        v = v.strip()

        # HTMLタグを含む場合はエラー
        if '<' in v or '>' in v:
            raise ValueError('Puzzle name cannot contain HTML tags')
        # 制御文字を含む場合はエラー
        if any(ord(c) < 32 for c in v):
            raise ValueError('Puzzle name cannot contain control characters')
        return v


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
        description="画像ファイル名（jpg, jpeg, png のみ対応）",
        max_length=255,
        json_schema_extra={"example": "my-puzzle.jpg"}
    )
    userId: str = Field(
        default="anonymous",
        description="ユーザーID",
        max_length=50,
        json_schema_extra={"example": "user-123"}
    )

    @field_validator('fileName')
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        """ファイル名のバリデーション（セキュリティ対策）"""
        # 最初にトリミング
        v = v.strip()

        # 制御文字を含む場合はエラー（最初にチェック）
        if any(ord(c) < 32 for c in v):
            raise ValueError('File name cannot contain control characters')

        # パストラバーサル対策: ../ や ..\\ を拒否
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('File name cannot contain path traversal sequences')

        # ファイル名として不適切な文字を拒否
        if any(c in v for c in ['<', '>', ':', '"', '|', '?', '*']):
            raise ValueError('File name contains invalid characters')

        # 拡張子チェック
        allowed_extensions = {'.jpg', '.jpeg', '.png'}
        file_lower = v.lower()
        if not any(file_lower.endswith(ext) for ext in allowed_extensions):
            raise ValueError(f'File extension must be one of: {", ".join(allowed_extensions)}')

        return v


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
