"""
Structured logging configuration

CloudWatch Logsで検索しやすいJSON形式のログを出力します。
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    JSON形式でログを出力するカスタムフォーマッター

    CloudWatch Logsで以下のようにクエリ可能:
    - fields @timestamp, level, message, puzzle_id, user_id
    - filter level = "ERROR"
    """

    def format(self, record: logging.LogRecord) -> str:
        """ログレコードをJSON形式に変換"""

        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 追加のコンテキスト情報を含める
        if hasattr(record, "puzzle_id"):
            log_data["puzzle_id"] = record.puzzle_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        # エラーの場合はスタックトレースを追加
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 追加の任意フィールド（extra= で渡された値）
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str = None) -> logging.Logger:
    """
    構造化ログを出力するロガーをセットアップ

    Args:
        name: ロガー名（通常は __name__ を渡す）

    Returns:
        設定済みのロガー

    環境変数:
        LOG_LEVEL: ログレベル（DEBUG, INFO, WARNING, ERROR）デフォルト: INFO
        ENVIRONMENT: 環境名（dev: 詳細ログ, prod: 簡潔ログ）
    """
    logger = logging.getLogger(name or __name__)

    # 既にハンドラが設定されている場合はスキップ（重複防止）
    if logger.handlers:
        return logger

    # ログレベルを環境変数から取得
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # ハンドラーの作成
    handler = logging.StreamHandler()

    # 環境に応じてフォーマッターを選択
    environment = os.environ.get("ENVIRONMENT", "dev")

    if environment == "prod":
        # 本番環境: JSON形式
        handler.setFormatter(JSONFormatter())
    else:
        # 開発環境: 人間が読みやすい形式
        # ただし、構造化情報も含める
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)

    logger.addHandler(handler)

    # 親ロガーへの伝播を防止（重複ログ防止）
    logger.propagate = False

    return logger


# デフォルトロガーをエクスポート
logger = setup_logger("jigsaw-puzzle")
