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

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "Error: backend/ directory not found"
    exit 1
fi

# Navigate to Lambda directory
cd "$LAMBDA_DIR"

echo "Step 1: Cleaning up old files..."
rm -rf backend function.zip

echo "Step 2: Copying backend directory..."
cp -r ../../backend ./backend

echo "Step 3: Exporting dependencies from uv..."
# uvからrequirements.txtを生成（Lambda用）
cd ../..
uv export --no-hashes --format requirements-txt > lambda/puzzle-register/requirements.txt
cd lambda/puzzle-register

echo "Step 4: Packaging Lambda function..."
zip -r function.zip index.py backend/ requirements.txt -q

FILE_SIZE=$(du -h function.zip | cut -f1)
echo "Package size: $FILE_SIZE"

echo "Step 5: Deploying to AWS Lambda..."
aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://function.zip \
    --output json > /dev/null

echo "Step 6: Cleaning up..."
rm -rf backend requirements.txt

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
