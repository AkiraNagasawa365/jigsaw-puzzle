"""
Lambda wrapper for puzzle registration using Mangum

This is a thin wrapper that uses Mangum to run FastAPI directly on Lambda.
All routing and business logic is handled by the FastAPI application.
"""

import sys
import os

# appパッケージをインポートするためbackend/を追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from mangum import Mangum
from app.api.main import app

# MangumでFastAPIアプリケーションをラップ
# lifespan="off": Lambda環境ではlifespanイベントを無効化
handler = Mangum(app, lifespan="off")
