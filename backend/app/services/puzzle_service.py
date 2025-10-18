"""
Puzzle registration business logic

This module contains the core business logic for puzzle registration.
It can be used by both FastAPI (local development) and AWS Lambda (production).
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError


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

        # AWSクライアントの初期化
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
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
            raise ClientError(
                f"Failed to save puzzle to DynamoDB: {str(e)}",
                operation_name='put_item'
            )

        print(f"Created puzzle: {puzzle_id} for user: {user_id}")

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
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'jpg'
        s3_key = f"puzzles/{puzzle_id}.{file_extension}"

        # アップロード用のpre-signed URLを生成
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.s3_bucket_name,
                    'Key': s3_key,
                    'ContentType': f'image/{file_extension}'
                },
                ExpiresIn=3600  # 1時間
            )
        except ClientError as e:
            raise ClientError(
                f"Failed to generate pre-signed URL: {str(e)}",
                operation_name='generate_presigned_url'
            )

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
            raise ClientError(
                f"Failed to update puzzle in DynamoDB: {str(e)}",
                operation_name='update_item'
            )

        print(f"Generated upload URL for puzzle: {puzzle_id}")

        # 成功レスポンスを返す
        return {
            'puzzleId': puzzle_id,
            'uploadUrl': presigned_url,
            'expiresIn': 3600,
            'message': 'Pre-signed URL generated successfully. Upload your image to this URL.'
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
            print(f"Error getting puzzle: {str(e)}")
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
            print(f"Error listing puzzles: {str(e)}")
            return []
