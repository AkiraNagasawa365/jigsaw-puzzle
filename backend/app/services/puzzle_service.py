"""
Puzzle registration business logic

This module contains the core business logic for puzzle registration.
It can be used by both FastAPI (local development) and AWS Lambda (production).
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError

from app.core.logger import setup_logger

# ロガーの初期化
logger = setup_logger(__name__)


class PuzzleService:
    """Service class for puzzle operations"""

    def __init__(self, s3_bucket_name: str, puzzles_table_name: str, environment: str = 'dev'):
        """
        Initialize PuzzleService

        Args:
            s3_bucket_name: Name of the S3 bucket for images
            puzzles_table_name: Name of the DynamoDB table for puzzles
            environment: Environment name (dev/staging/prod)
        """
        self.s3_bucket_name = s3_bucket_name
        self.puzzles_table_name = puzzles_table_name
        self.environment = environment

        # AWSリージョンを環境変数から取得（CI/CD環境やLambda環境で必要）
        aws_region = os.environ.get('AWS_REGION', 'ap-northeast-1')

        # AWSクライアントの初期化（region_nameを明示的に指定）
        self.s3_client = boto3.client('s3', region_name=aws_region)
        self.dynamodb = boto3.resource('dynamodb', region_name=aws_region)
        self.puzzles_table = self.dynamodb.Table(puzzles_table_name)

    def create_puzzle(
        self,
        piece_count: int,
        puzzle_name: str,
        user_id: str = 'anonymous'
    ) -> Dict[str, Any]:
        """
        Create a new puzzle without image

        Args:
            piece_count: Number of puzzle pieces (100, 300, 500, 1000, 2000)
            puzzle_name: User-defined puzzle name (e.g., "Mt. Fuji Landscape")
            user_id: User ID (default: 'anonymous')

        Returns:
            Dictionary containing puzzle information

        Raises:
            ValueError: If piece_count is invalid
            ClientError: If AWS operation fails
        """
        # ピース数を検証
        valid_piece_counts = [100, 300, 500, 1000, 2000]
        if piece_count not in valid_piece_counts:
            raise ValueError(
                f"pieceCount must be one of: {', '.join(map(str, valid_piece_counts))}"
            )

        # パズルIDを生成
        puzzle_id = str(uuid.uuid4())

        # DynamoDBにパズルレコードを作成
        current_time = datetime.utcnow().isoformat()

        puzzle_item = {
            'userId': user_id,
            'puzzleId': puzzle_id,
            'puzzleName': puzzle_name,
            'pieceCount': piece_count,
            'status': 'pending',  # pending -> uploaded -> processing -> completed
            'createdAt': current_time,
            'updatedAt': current_time
        }

        try:
            self.puzzles_table.put_item(Item=puzzle_item)
        except ClientError as e:
            logger.error(
                "Failed to save puzzle to DynamoDB",
                extra={
                    "puzzle_id": puzzle_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            raise  # 元のエラーをそのまま再raise

        logger.info(
            f"Created puzzle successfully",
            extra={
                "puzzle_id": puzzle_id,
                "user_id": user_id,
                "piece_count": piece_count,
                "puzzle_name": puzzle_name
            }
        )

        # 成功レスポンスを返す
        return {
            'puzzleId': puzzle_id,
            'puzzleName': puzzle_name,
            'pieceCount': piece_count,
            'status': 'pending',
            'message': 'Puzzle created successfully. You can now upload an image.'
        }

    def generate_upload_url(
        self,
        puzzle_id: str,
        file_name: str = 'puzzle.jpg',
        user_id: str = 'anonymous'
    ) -> Dict[str, Any]:
        """
        Generate a pre-signed URL for uploading an image to an existing puzzle

        Args:
            puzzle_id: Puzzle ID
            file_name: Name of the puzzle image file
            user_id: User ID (default: 'anonymous')

        Returns:
            Dictionary containing upload URL and expiration time

        Raises:
            ValueError: If puzzle not found
            ClientError: If AWS operation fails
        """
        # パズルの存在を確認
        puzzle = self.get_puzzle(user_id, puzzle_id)
        if not puzzle:
            raise ValueError(f"Puzzle not found: {puzzle_id}")

        # S3キーを生成
        file_extension = file_name.split('.')[-1].lower() if '.' in file_name else 'jpg'
        s3_key = f"puzzles/{puzzle_id}.{file_extension}"

        # 拡張子から正しいMIME typeを取得
        mime_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }
        content_type = mime_type_map.get(file_extension, 'image/jpeg')

        # アップロード用のpre-signed URLを生成
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.s3_bucket_name,
                    'Key': s3_key,
                    'ContentType': content_type
                },
                ExpiresIn=900  # 15分（セキュリティ向上のため短縮）
            )
        except ClientError as e:
            logger.error(
                "Failed to generate pre-signed URL",
                extra={
                    "puzzle_id": puzzle_id,
                    "user_id": user_id,
                    "s3_key": s3_key,
                    "error": str(e)
                }
            )
            raise  # 元のエラーをそのまま再raise

        # ファイル情報でパズルレコードを更新
        current_time = datetime.utcnow().isoformat()

        try:
            self.puzzles_table.update_item(
                Key={
                    'userId': user_id,
                    'puzzleId': puzzle_id
                },
                UpdateExpression='SET fileName = :fn, s3Key = :s3k, #status = :st, updatedAt = :ua',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':fn': file_name,
                    ':s3k': s3_key,
                    ':st': 'uploaded',
                    ':ua': current_time
                }
            )
        except ClientError as e:
            logger.error(
                "Failed to update puzzle in DynamoDB",
                extra={
                    "puzzle_id": puzzle_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            raise  # 元のエラーをそのまま再raise

        logger.info(
            "Generated upload URL successfully",
            extra={
                "puzzle_id": puzzle_id,
                "user_id": user_id,
                "file_name": file_name,
                "s3_key": s3_key
            }
        )

        # 成功レスポンスを返す
        return {
            'puzzleId': puzzle_id,
            'uploadUrl': presigned_url,
            'expiresIn': 900,
            'message': 'Pre-signed URL generated successfully. Upload your image to this URL within 15 minutes.'
        }

    def get_puzzle(self, user_id: str, puzzle_id: str) -> Optional[Dict[str, Any]]:
        """
        Get puzzle information by ID

        Args:
            user_id: User ID
            puzzle_id: Puzzle ID

        Returns:
            Puzzle information or None if not found
        """
        try:
            response = self.puzzles_table.get_item(
                Key={
                    'userId': user_id,
                    'puzzleId': puzzle_id
                }
            )
            return response.get('Item')
        except ClientError as e:
            logger.error(
                "Error getting puzzle",
                extra={
                    "puzzle_id": puzzle_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            return None

    def list_puzzles(self, user_id: str) -> list:
        """
        List all puzzles for a user

        Args:
            user_id: User ID

        Returns:
            List of puzzles
        """
        try:
            response = self.puzzles_table.query(
                KeyConditionExpression='userId = :uid',
                ExpressionAttributeValues={
                    ':uid': user_id
                }
            )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(
                "Error listing puzzles",
                extra={
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            return []

    def delete_puzzle(self, user_id: str, puzzle_id: str) -> Dict[str, Any]:
        """
        Delete a puzzle and its associated S3 image

        Args:
            user_id: User ID
            puzzle_id: Puzzle ID

        Returns:
            Dictionary containing deletion confirmation

        Raises:
            ValueError: If puzzle not found
            ClientError: If AWS operation fails
        """
        # パズルの存在を確認
        puzzle = self.get_puzzle(user_id, puzzle_id)
        if not puzzle:
            raise ValueError(f"Puzzle not found: {puzzle_id}")

        # S3から画像を削除（存在する場合）
        s3_key = puzzle.get('s3Key')
        if s3_key:
            try:
                self.s3_client.delete_object(
                    Bucket=self.s3_bucket_name,
                    Key=s3_key
                )
                logger.info(
                    "Deleted S3 object successfully",
                    extra={
                        "puzzle_id": puzzle_id,
                        "user_id": user_id,
                        "s3_key": s3_key
                    }
                )
            except ClientError as e:
                logger.error(
                    "Failed to delete S3 object",
                    extra={
                        "puzzle_id": puzzle_id,
                        "user_id": user_id,
                        "s3_key": s3_key,
                        "error": str(e)
                    }
                )
                # S3削除失敗はエラーとせず継続（DynamoDBレコードは削除）

        # DynamoDBからパズルレコードを削除
        try:
            self.puzzles_table.delete_item(
                Key={
                    'userId': user_id,
                    'puzzleId': puzzle_id
                }
            )
        except ClientError as e:
            logger.error(
                "Failed to delete puzzle from DynamoDB",
                extra={
                    "puzzle_id": puzzle_id,
                    "user_id": user_id,
                    "error": str(e)
                }
            )
            raise

        logger.info(
            "Deleted puzzle successfully",
            extra={
                "puzzle_id": puzzle_id,
                "user_id": user_id,
                "had_image": bool(s3_key)
            }
        )

        return {
            'puzzleId': puzzle_id,
            'message': 'Puzzle deleted successfully'
        }
