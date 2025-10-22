#!/bin/bash

# Frontend deployment script for CloudFront + S3
# Usage: ./scripts/deploy-frontend.sh [environment]

set -e  # Exit on error

ENVIRONMENT=${1:-dev}
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_NAME="jigsaw-puzzle"

echo "==================================="
echo "Frontend Deployment Script"
echo "==================================="
echo "Environment: $ENVIRONMENT"
echo "Project Root: $PROJECT_ROOT"
echo ""

# ============================================
# Step 1: Get all resource information from SSM Parameter Store
# ============================================
echo "Step 1: Getting AWS resource information from SSM Parameter Store..."

SSM_PARAM_NAME="/${PROJECT_NAME}/frontend/${ENVIRONMENT}/resources"
echo "  Reading: $SSM_PARAM_NAME"

# Get the JSON from SSM
RESOURCES_JSON=$(aws ssm get-parameter \
    --name "$SSM_PARAM_NAME" \
    --with-decryption \
    --query 'Parameter.Value' \
    --output text 2>/dev/null)

if [ -z "$RESOURCES_JSON" ]; then
    echo "Error: Could not retrieve resource information from SSM"
    echo "       Expected parameter: $SSM_PARAM_NAME"
    echo ""
    echo "Hint: Run 'cd terraform/environments/$ENVIRONMENT && terraform apply' to create/update the SSM parameter"
    exit 1
fi

# Parse JSON to get individual values
S3_BUCKET=$(echo "$RESOURCES_JSON" | jq -r '.s3_bucket_name')
CLOUDFRONT_ID=$(echo "$RESOURCES_JSON" | jq -r '.cloudfront_distribution_id')
CLOUDFRONT_DOMAIN=$(echo "$RESOURCES_JSON" | jq -r '.cloudfront_domain_name')
API_ENDPOINT=$(echo "$RESOURCES_JSON" | jq -r '.api_base_url')

# Validate required values
if [ -z "$S3_BUCKET" ] || [ "$S3_BUCKET" = "null" ]; then
    echo "Error: S3 bucket name not found in SSM parameter"
    exit 1
fi

if [ -z "$CLOUDFRONT_ID" ] || [ "$CLOUDFRONT_ID" = "null" ]; then
    echo "Warning: CloudFront distribution ID not found"
    echo "         Deployment will continue, but cache invalidation will be skipped"
fi

echo "  ✓ S3 Bucket: $S3_BUCKET"
if [ -n "$CLOUDFRONT_ID" ] && [ "$CLOUDFRONT_ID" != "null" ]; then
    echo "  ✓ CloudFront ID: $CLOUDFRONT_ID"
    echo "  ✓ CloudFront Domain: $CLOUDFRONT_DOMAIN"
fi
if [ -n "$API_ENDPOINT" ] && [ "$API_ENDPOINT" != "null" ]; then
    echo "  ✓ API Endpoint: $API_ENDPOINT"
fi
echo ""

# ============================================
# Step 2: Build frontend for production
# ============================================
echo "Step 2: Building frontend for production..."
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

# Build with API endpoint from SSM
if [ -n "$API_ENDPOINT" ] && [ "$API_ENDPOINT" != "null" ]; then
    echo "  Building with API endpoint: $API_ENDPOINT"
    VITE_API_BASE_URL=$API_ENDPOINT npm run build
else
    echo "  Building with .env.production settings"
    npm run build
fi

if [ ! -d "dist" ]; then
    echo "Error: Build failed - dist/ directory not found"
    exit 1
fi

echo "  ✓ Build complete"
echo ""

# ============================================
# Step 3: Upload to S3
# ============================================
echo "Step 3: Uploading files to S3..."
aws s3 sync dist/ "s3://$S3_BUCKET/" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html"

# Upload index.html with shorter cache (SPAのため)
aws s3 cp dist/index.html "s3://$S3_BUCKET/index.html" \
    --cache-control "public, max-age=0, must-revalidate" \
    --content-type "text/html"

echo "  ✓ Upload complete"
echo ""

# ============================================
# Step 4: Invalidate CloudFront cache
# ============================================
echo "Step 4: Invalidating CloudFront cache..."
if [ -n "$CLOUDFRONT_ID" ] && [ "$CLOUDFRONT_ID" != "null" ]; then
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text 2>/dev/null)

    if [ -n "$INVALIDATION_ID" ] && [ "$INVALIDATION_ID" != "null" ]; then
        echo "  ✓ Invalidation ID: $INVALIDATION_ID"
        echo "  (Cache invalidation is running in the background)"
    else
        echo "  ⚠️  Failed to create cache invalidation"
    fi
else
    echo "  ⚠️  Skipping cache invalidation (CloudFront ID not found)"
fi
echo ""

# ============================================
# Summary
# ============================================
echo "==================================="
echo "Deployment Complete! ✅"
echo "==================================="
echo ""
echo "S3 Bucket: $S3_BUCKET"
if [ -n "$CLOUDFRONT_DOMAIN" ] && [ "$CLOUDFRONT_DOMAIN" != "null" ]; then
    echo "Frontend URL: https://$CLOUDFRONT_DOMAIN"
    echo ""
    echo "Note: CloudFront cache invalidation may take a few minutes."
fi
echo ""
if [ -n "$INVALIDATION_ID" ] && [ "$INVALIDATION_ID" != "null" ]; then
    echo "Check invalidation status:"
    echo "  aws cloudfront get-invalidation --distribution-id $CLOUDFRONT_ID --id $INVALIDATION_ID"
    echo ""
fi
