"""Sync configuration values from AWS SSM Parameter Store.

Currently supports writing the frontend `.env.local` with the API base URL
retrieved from Parameter Store. Designed to be extended for other targets (e.g. backend).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

DEFAULT_PROJECT = "jigsaw-puzzle"
FRONTEND_ENV_FILE = Path("frontend/.env.local")
BACKEND_ENV_FILE = Path("backend/.env.local")
LOCAL_API_BASE_URL = "http://localhost:8000"
LOCAL_BACKEND_ENV_LINES = [
    "AWS_REGION=ap-northeast-1",
    "S3_BUCKET_NAME=jigsaw-puzzle-dev-images",
    "PUZZLES_TABLE_NAME=jigsaw-puzzle-dev-puzzles",
    "PIECES_TABLE_NAME=jigsaw-puzzle-dev-pieces",
    "ENVIRONMENT=dev",
    "ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://192.168.100.12:5173",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync configuration from SSM Parameter Store")
    parser.add_argument(
        "target",
        choices=["frontend", "backend"],
        help="Which component to sync (additional targets can be added later)",
    )
    parser.add_argument(
        "--environment",
        default="local",
        help="Environment name (default: local -> uses localhost; specify dev/staging/prod for AWS)",
    )
    parser.add_argument(
        "--project",
        default=DEFAULT_PROJECT,
        help="Project name used in the SSM parameter path (default: jigsaw-puzzle)",
    )
    parser.add_argument(
        "--aws-profile",
        dest="aws_profile",
        default=None,
        help="Optional AWS CLI profile name to use for authentication",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Optional AWS region override (falls back to standard resolution order)",
    )
    return parser.parse_args()


def build_frontend_parameter_name(project: str, environment: str) -> str:
    return f"/{project}/frontend/{environment}/api_base_url"


def build_backend_parameter_name(project: str, environment: str) -> str:
    return f"/{project}/backend/{environment}/env"


def fetch_parameter(name: str, *, profile: str | None, region: str | None) -> str:
    session_kwargs = {}
    if profile:
        session_kwargs["profile_name"] = profile
    session = boto3.Session(**session_kwargs)
    client = session.client("ssm", region_name=region)
    response = client.get_parameter(Name=name, WithDecryption=False)
    return response["Parameter"]["Value"]


def write_frontend_env_file(value: str) -> None:
    FRONTEND_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    FRONTEND_ENV_FILE.write_text(f"VITE_API_BASE_URL={value}\n", encoding="utf-8")


def write_backend_env_file(value: str) -> None:
    BACKEND_ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKEND_ENV_FILE.write_text(f"{value}\n", encoding="utf-8")


def sync_frontend(environment: str, project: str, profile: str | None, region: str | None) -> None:
    if environment == "local":
        value = LOCAL_API_BASE_URL
        print(f"Using local API base URL: {value}")
    else:
        parameter_name = build_frontend_parameter_name(project, environment)
        print(f"Fetching frontend config from SSM parameter: {parameter_name}")
        value = fetch_parameter(parameter_name, profile=profile, region=region)

    write_frontend_env_file(value)
    print(f"Wrote {FRONTEND_ENV_FILE} with VITE_API_BASE_URL={value}")


def sync_backend(environment: str, project: str, profile: str | None, region: str | None) -> None:
    if environment == "local":
        value = "\n".join(LOCAL_BACKEND_ENV_LINES)
        print("Using local backend configuration (localhost-friendly defaults)")
    else:
        parameter_name = build_backend_parameter_name(project, environment)
        print(f"Fetching backend config from SSM parameter: {parameter_name}")
        value = fetch_parameter(parameter_name, profile=profile, region=region)

    write_backend_env_file(value)
    print(f"Wrote {BACKEND_ENV_FILE}")


def main() -> int:
    args = parse_args()

    try:
        if args.target == "frontend":
            sync_frontend(args.environment, args.project, args.aws_profile, args.region)
        elif args.target == "backend":
            sync_backend(args.environment, args.project, args.aws_profile, args.region)
        else:
            raise ValueError(f"Unsupported target: {args.target}")
    except (ClientError, BotoCoreError) as err:
        print(f"Failed to fetch parameter: {err}", file=sys.stderr)
        return 1
    except Exception as err:  # noqa: BLE001 - catch-all to simplify CLI usage
        print(f"Unexpected error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
