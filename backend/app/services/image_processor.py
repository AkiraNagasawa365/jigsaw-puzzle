"""
Image processing service for puzzle piece generation

This module handles image splitting into puzzle pieces using Pillow.
"""

import io
import uuid
from datetime import datetime
from typing import Dict, Any, List, Tuple
from PIL import Image
import boto3
from botocore.exceptions import ClientError

from app.core.logger import setup_logger

logger = setup_logger(__name__)


class ImageProcessor:
    """Service class for image processing and puzzle piece generation"""

    # ピース数に対応する推奨グリッド（rows x cols）
    PIECE_GRIDS = {
        100: (10, 10),
        300: (15, 20),
        500: (20, 25),
        1000: (25, 40),
        2000: (40, 50)
    }

    def __init__(self, s3_bucket_name: str, pieces_table_name: str, puzzles_table_name: str):
        """
        Initialize ImageProcessor

        Args:
            s3_bucket_name: Name of the S3 bucket for images
            pieces_table_name: Name of the DynamoDB table for pieces
            puzzles_table_name: Name of the DynamoDB table for puzzles
        """
        self.s3_bucket_name = s3_bucket_name
        self.pieces_table_name = pieces_table_name
        self.puzzles_table_name = puzzles_table_name

        # AWSクライアントの初期化
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.pieces_table = self.dynamodb.Table(pieces_table_name)
        self.puzzles_table = self.dynamodb.Table(puzzles_table_name)

    def calculate_grid(self, piece_count: int, image_width: int, image_height: int) -> Tuple[int, int]:
        """
        Calculate optimal grid dimensions based on piece count and image aspect ratio

        Args:
            piece_count: Number of puzzle pieces
            image_width: Original image width in pixels
            image_height: Original image height in pixels

        Returns:
            Tuple of (rows, cols) for the grid

        Raises:
            ValueError: If piece_count is not supported
        """
        if piece_count not in self.PIECE_GRIDS:
            raise ValueError(f"Unsupported piece count: {piece_count}")

        base_rows, base_cols = self.PIECE_GRIDS[piece_count]

        # 画像のアスペクト比を計算
        aspect_ratio = image_width / image_height

        # アスペクト比が極端に異なる場合は調整
        # 横長の画像（aspect_ratio > 1.5）の場合、列を増やす
        # 縦長の画像（aspect_ratio < 0.67）の場合、行を増やす
        if aspect_ratio > 1.5:
            # 横長: 列を増やして行を減らす
            adjustment_factor = min(aspect_ratio / 1.2, 1.5)
            cols = int(base_cols * adjustment_factor)
            rows = piece_count // cols
            # 端数調整
            while rows * cols < piece_count:
                cols += 1
                rows = piece_count // cols
        elif aspect_ratio < 0.67:
            # 縦長: 行を増やして列を減らす
            adjustment_factor = min(1.2 / aspect_ratio, 1.5)
            rows = int(base_rows * adjustment_factor)
            cols = piece_count // rows
            # 端数調整
            while rows * cols < piece_count:
                rows += 1
                cols = piece_count // rows
        else:
            # 通常のアスペクト比
            rows, cols = base_rows, base_cols

        logger.info(
            f"Calculated grid dimensions",
            extra={
                "piece_count": piece_count,
                "image_width": image_width,
                "image_height": image_height,
                "aspect_ratio": round(aspect_ratio, 2),
                "rows": rows,
                "cols": cols
            }
        )

        return rows, cols

    def split_image(
        self,
        puzzle_id: str,
        user_id: str,
        s3_key: str,
        piece_count: int
    ) -> Dict[str, Any]:
        """
        Split image into puzzle pieces and save to S3/DynamoDB

        Args:
            puzzle_id: Puzzle ID
            user_id: User ID
            s3_key: S3 key of the original image
            piece_count: Number of pieces to create

        Returns:
            Dictionary containing processing results

        Raises:
            ClientError: If AWS operation fails
            ValueError: If image processing fails
        """
        try:
            # パズルのステータスを "processing" に更新
            self._update_puzzle_status(user_id, puzzle_id, 'processing')

            # S3から画像を取得
            logger.info(
                f"Downloading image from S3",
                extra={"puzzle_id": puzzle_id, "s3_key": s3_key}
            )

            response = self.s3_client.get_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key
            )
            image_data = response['Body'].read()

            # Pillowで画像を開く
            image = Image.open(io.BytesIO(image_data))
            image_width, image_height = image.size

            logger.info(
                f"Image loaded successfully",
                extra={
                    "puzzle_id": puzzle_id,
                    "width": image_width,
                    "height": image_height,
                    "format": image.format
                }
            )

            # グリッドサイズを計算
            rows, cols = self.calculate_grid(piece_count, image_width, image_height)

            # ピースサイズを計算
            piece_width = image_width // cols
            piece_height = image_height // rows

            # 画像を分割してS3に保存
            pieces_info = []

            for row in range(rows):
                for col in range(cols):
                    piece_id = str(uuid.uuid4())

                    # ピースを切り出し
                    left = col * piece_width
                    top = row * piece_height
                    right = left + piece_width if col < cols - 1 else image_width
                    bottom = top + piece_height if row < rows - 1 else image_height

                    piece_image = image.crop((left, top, right, bottom))

                    # ピース画像をバイトストリームに変換
                    piece_buffer = io.BytesIO()
                    piece_image.save(piece_buffer, format='JPEG', quality=85)
                    piece_buffer.seek(0)

                    # S3に保存
                    piece_s3_key = f"pieces/{puzzle_id}/{piece_id}.jpg"
                    self.s3_client.put_object(
                        Bucket=self.s3_bucket_name,
                        Key=piece_s3_key,
                        Body=piece_buffer,
                        ContentType='image/jpeg'
                    )

                    # ピース情報を記録
                    current_time = datetime.utcnow().isoformat()
                    piece_info = {
                        'userId': user_id,
                        'pieceId': piece_id,
                        'puzzleId': puzzle_id,
                        'row': row,
                        'col': col,
                        'correctRow': row,
                        'correctCol': col,
                        's3Key': piece_s3_key,
                        'width': right - left,
                        'height': bottom - top,
                        'createdAt': current_time,
                        'updatedAt': current_time
                    }

                    # DynamoDBに保存
                    self.pieces_table.put_item(Item=piece_info)
                    pieces_info.append(piece_info)

                    logger.debug(
                        f"Piece created",
                        extra={
                            "puzzle_id": puzzle_id,
                            "piece_id": piece_id,
                            "row": row,
                            "col": col
                        }
                    )

            # パズルのステータスを "completed" に更新
            self._update_puzzle_status(
                user_id,
                puzzle_id,
                'completed',
                rows=rows,
                cols=cols,
                total_pieces=len(pieces_info)
            )

            logger.info(
                f"Image split completed successfully",
                extra={
                    "puzzle_id": puzzle_id,
                    "total_pieces": len(pieces_info),
                    "rows": rows,
                    "cols": cols
                }
            )

            return {
                'puzzleId': puzzle_id,
                'totalPieces': len(pieces_info),
                'rows': rows,
                'cols': cols,
                'status': 'completed'
            }

        except ClientError as e:
            logger.error(
                f"AWS error during image processing",
                extra={
                    "puzzle_id": puzzle_id,
                    "error": str(e)
                }
            )
            # ステータスをfailedに更新
            self._update_puzzle_status(user_id, puzzle_id, 'failed', error=str(e))
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error during image processing",
                extra={
                    "puzzle_id": puzzle_id,
                    "error": str(e)
                }
            )
            # ステータスをfailedに更新
            self._update_puzzle_status(user_id, puzzle_id, 'failed', error=str(e))
            raise ValueError(f"Image processing failed: {str(e)}")

    def _update_puzzle_status(
        self,
        user_id: str,
        puzzle_id: str,
        status: str,
        **kwargs
    ) -> None:
        """
        Update puzzle status in DynamoDB

        Args:
            user_id: User ID
            puzzle_id: Puzzle ID
            status: New status (processing, completed, failed)
            **kwargs: Additional attributes to update
        """
        current_time = datetime.utcnow().isoformat()

        update_expression = "SET #status = :status, updatedAt = :updated"
        expression_attribute_names = {'#status': 'status'}
        expression_attribute_values = {
            ':status': status,
            ':updated': current_time
        }

        # 追加の属性を更新式に追加
        for key, value in kwargs.items():
            update_expression += f", {key} = :{key}"
            expression_attribute_values[f":{key}"] = value

        try:
            self.puzzles_table.update_item(
                Key={
                    'userId': user_id,
                    'puzzleId': puzzle_id
                },
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )

            logger.info(
                f"Puzzle status updated",
                extra={
                    "puzzle_id": puzzle_id,
                    "status": status,
                    **kwargs
                }
            )

        except ClientError as e:
            logger.error(
                f"Failed to update puzzle status",
                extra={
                    "puzzle_id": puzzle_id,
                    "status": status,
                    "error": str(e)
                }
            )
            raise
