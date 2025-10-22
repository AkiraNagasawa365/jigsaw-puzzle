"""
Configuration management for the application

環境変数を一元管理し、型安全な設定を提供します。
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# .env/.env.localファイルを自動読み込み（ローカル開発用）
# Lambda環境ではこれらのファイルが存在しないため自動的にスキップされる
base_dir = Path(__file__).parent.parent.parent
for dotenv_name in (".env.local", ".env"):
    env_path = base_dir / dotenv_name
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        # ログ設定前なので、ここだけはprintを使用
        print(f"✅ Loaded environment variables from {env_path}")


class Settings:
    """Application settings loaded from environment variables"""

    def __init__(self) -> None:
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
