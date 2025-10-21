#!/bin/bash

# Lambda deployment script for puzzle-register function
# Usage: ./scripts/deploy-lambda.sh

set -e  # Exit on error

FUNCTION_NAME="jigsaw-puzzle-dev-puzzle-register"
LAMBDA_DIR="lambda/puzzle-register"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "==================================="
echo "Lambda Deployment Script"
echo "==================================="
echo "Function: $FUNCTION_NAME"
echo "Project Root: $PROJECT_ROOT"
echo ""

cd "$PROJECT_ROOT"

# Check if backend/app directory exists
if [ ! -d "backend/app" ]; then
    echo "Error: backend/app/ directory not found"
    exit 1
fi

# Navigate to Lambda directory
cd "$LAMBDA_DIR"

echo "Step 1: Cleaning up old files..."
rm -rf backend function.zip

echo "Step 2: Copying backend/app directory..."
mkdir -p backend
cp -r ../../backend/app ./backend/

echo "Step 2.5: Removing sensitive files from copied backend..."
# .env ファイルや機密情報を含むファイルを削除（念のため）
find ./backend -name ".env*" -type f -delete
find ./backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find ./backend -name "*.pyc" -type f -delete

echo "Step 3: Exporting dependencies from uv..."
# uvからrequirements.txtを生成（Lambda用、開発用依存関係を除外）
cd ../..
uv export --no-hashes --no-dev --format requirements-txt > lambda/puzzle-register/requirements-full.txt

# プロジェクト自身（jigsaw-puzzle）を除外してrequirements.txtを作成
grep -v "jigsaw-puzzle" lambda/puzzle-register/requirements-full.txt | \
  grep -v "^-e " | \
  grep -v "file://" > lambda/puzzle-register/requirements.txt

rm lambda/puzzle-register/requirements-full.txt
cd lambda/puzzle-register

echo "Step 4: Installing dependencies for Linux (Lambda runtime)..."
# 一時ディレクトリを作成
mkdir -p package

# Linux互換の依存関係をインストール
# legacy-resolverを使用して依存関係の競合を回避
python3 -m pip install \
  --platform manylinux2014_x86_64 \
  --target=./package \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: \
  --upgrade \
  --use-deprecated=legacy-resolver \
  -r requirements.txt

echo "Step 5: Packaging Lambda function..."
# packageディレクトリの内容をzipに追加（依存関係）
cd package
zip -r ../function.zip . -q
cd ..

# index.pyとbackendディレクトリを追加（アプリケーションコード）
zip -ur function.zip index.py backend/ \
    -x "*.env*" "*/__pycache__/*" "*.pyc" "*.pyo" ".DS_Store" \
    -q

FILE_SIZE=$(du -h function.zip | cut -f1)
echo "Package size: $FILE_SIZE"

echo "Step 6: Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://function.zip \
    --output json > /dev/null

echo "Step 7: Cleaning up temporary files..."
rm -rf backend requirements.txt package

echo ""
echo "==================================="
echo "Deployment Complete! ✅"
echo "==================================="
echo ""
echo "Test the function:"
echo "  aws lambda invoke --function-name $FUNCTION_NAME output.json"
echo ""
echo "Or via API Gateway (after API Gateway setup):"
echo "  curl -X POST https://YOUR_API_ID.execute-api.ap-northeast-1.amazonaws.com/dev/puzzles \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"pieceCount\": 300}'"
