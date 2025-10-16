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

        # Initialize AWS clients
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.puzzles_table = self.dynamodb.Table(puzzles_table_name)

    def register_puzzle(
        self,
        piece_count: int,
        file_name: str = 'puzzle.jpg',
        user_id: str = 'anonymous'
    ) -> Dict[str, Any]:
        """
        Register a new puzzle and generate a pre-signed URL for image upload

        Args:
            piece_count: Number of puzzle pieces (100, 300, 500, 1000, 2000)
            file_name: Name of the puzzle image file
            user_id: User ID (default: 'anonymous')

        Returns:
            Dictionary containing puzzle ID, upload URL, and expiration time

        Raises:
            ValueError: If piece_count is invalid
            ClientError: If AWS operation fails
        """
        # Validate piece count
        valid_piece_counts = [100, 300, 500, 1000, 2000]
        if piece_count not in valid_piece_counts:
            raise ValueError(
                f"pieceCount must be one of: {', '.join(map(str, valid_piece_counts))}"
            )

        # Generate puzzle ID
        puzzle_id = str(uuid.uuid4())

        # Generate S3 key
        file_extension = file_name.split('.')[-1] if '.' in file_name else 'jpg'
        s3_key = f"puzzles/{puzzle_id}.{file_extension}"

        # Generate pre-signed URL for upload (valid for 5 minutes)
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.s3_bucket_name,
                    'Key': s3_key,
                    'ContentType': f'image/{file_extension}'
                },
                ExpiresIn=300  # 5 minutes
            )
        except ClientError as e:
            raise ClientError(
                f"Failed to generate pre-signed URL: {str(e)}",
                operation_name='generate_presigned_url'
            )

        # Create puzzle record in DynamoDB
        current_time = datetime.utcnow().isoformat()

        puzzle_item = {
            'userId': user_id,
            'puzzleId': puzzle_id,
            'pieceCount': piece_count,
            'fileName': file_name,
            's3Key': s3_key,
            'status': 'pending',  # pending -> processing -> completed
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

        # Return success response
        return {
            'puzzleId': puzzle_id,
            'uploadUrl': presigned_url,
            'expiresIn': 300,
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
