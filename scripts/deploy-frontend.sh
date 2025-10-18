#!/bin/bash

# Frontend deployment script for CloudFront + S3
# Usage: ./scripts/deploy-frontend.sh [environment]

set -e  # Exit on error

ENVIRONMENT=${1:-dev}
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform/environments/$ENVIRONMENT"

echo "==================================="
echo "Frontend Deployment Script"
echo "==================================="
echo "Environment: $ENVIRONMENT"
echo "Project Root: $PROJECT_ROOT"
echo ""

# Check if terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    echo "Error: Terraform directory not found: $TERRAFORM_DIR"
    exit 1
fi

# Get S3 bucket name and CloudFront distribution ID from Terraform
echo "Step 1: Getting AWS resource information from Terraform..."
cd "$TERRAFORM_DIR"

S3_BUCKET=$(terraform output -raw frontend_s3_bucket_name 2>/dev/null)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null)

if [ -z "$S3_BUCKET" ]; then
    echo "Error: Could not get S3 bucket name from Terraform"
    exit 1
fi

if [ -z "$CLOUDFRONT_ID" ]; then
    echo "Error: Could not get CloudFront distribution ID from Terraform"
    exit 1
fi

echo "  S3 Bucket: $S3_BUCKET"
echo "  CloudFront ID: $CLOUDFRONT_ID"
echo ""

# Get API endpoint from Terraform
echo "Step 1.5: Getting API endpoint from Terraform..."
cd "$TERRAFORM_DIR"
API_ENDPOINT=$(terraform output -raw api_endpoint 2>/dev/null)

if [ -z "$API_ENDPOINT" ]; then
    echo "Warning: Could not get API endpoint from Terraform"
    echo "         Using default from .env.production"
else
    echo "  API Endpoint: $API_ENDPOINT"
fi
echo ""

# Build frontend
echo "Step 2: Building frontend for production..."
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  Installing dependencies..."
    npm install
fi

# Build with API endpoint from Terraform (if available)
# Viteは環境変数をビルド時に埋め込むため、ここで指定する必要がある
if [ -n "$API_ENDPOINT" ]; then
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

echo "  Build complete ✓"
echo ""

# Upload to S3
echo "Step 3: Uploading files to S3..."
aws s3 sync dist/ "s3://$S3_BUCKET/" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html"

# Upload index.html with shorter cache (SPAのため)
aws s3 cp dist/index.html "s3://$S3_BUCKET/index.html" \
    --cache-control "public, max-age=0, must-revalidate" \
    --content-type "text/html"

echo "  Upload complete ✓"
echo ""

# Invalidate CloudFront cache
echo "Step 4: Invalidating CloudFront cache..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CLOUDFRONT_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

echo "  Invalidation ID: $INVALIDATION_ID"
echo "  (Cache invalidation is running in the background)"
echo ""

# Get CloudFront domain
CLOUDFRONT_DOMAIN=$(cd "$TERRAFORM_DIR" && terraform output -raw cloudfront_domain_name 2>/dev/null)

echo "==================================="
echo "Deployment Complete! ✅"
echo "==================================="
echo ""
echo "Your frontend is now available at:"
echo "  https://$CLOUDFRONT_DOMAIN"
echo ""
echo "Note: CloudFront cache invalidation may take a few minutes."
echo ""
echo "Check invalidation status:"
echo "  aws cloudfront get-invalidation --distribution-id $CLOUDFRONT_ID --id $INVALIDATION_ID"
echo ""
