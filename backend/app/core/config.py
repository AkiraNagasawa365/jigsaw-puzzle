"""
Configuration management for the application

環境変数を一元管理し、型安全な設定を提供します。
"""

import os
from typing import List


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self):
        # AWS Configuration
        self.aws_region: str = os.environ.get('AWS_REGION', 'ap-northeast-1')
        self.aws_profile: str = os.environ.get('AWS_PROFILE', 'default')

        # S3 Configuration
        self.s3_bucket_name: str = os.environ.get('S3_BUCKET_NAME', 'jigsaw-puzzle-dev-images')

        # DynamoDB Configuration
        self.puzzles_table_name: str = os.environ.get('PUZZLES_TABLE_NAME', 'jigsaw-puzzle-dev-puzzles')
        self.pieces_table_name: str = os.environ.get('PIECES_TABLE_NAME', 'jigsaw-puzzle-dev-pieces')

        # Environment
        self.environment: str = os.environ.get('ENVIRONMENT', 'dev')

        # CORS Configuration
        # デフォルト: Vite開発サーバー(5173)と旧ポート(3000)の両方を許可
        allowed_origins_str = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173')
        self.allowed_origins: List[str] = [origin.strip() for origin in allowed_origins_str.split(',')]

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == 'prod'

    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == 'dev'


# Singleton instance
settings = Settings()
