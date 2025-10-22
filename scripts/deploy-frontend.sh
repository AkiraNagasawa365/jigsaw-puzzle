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

# ============================================
# Step 1: Get S3 bucket name and CloudFront distribution ID
# ============================================
echo "Step 1: Getting AWS resource information..."

# Try to get from environment variables first (for CI/CD)
if [ -n "$S3_BUCKET_NAME" ]; then
    S3_BUCKET="$S3_BUCKET_NAME"
    echo "  Using S3 bucket from environment variable: $S3_BUCKET"
else
    # Try to get from Terraform output (for local development)
    if [ -d "$TERRAFORM_DIR" ]; then
        cd "$TERRAFORM_DIR"
        S3_BUCKET=$(terraform output -raw frontend_s3_bucket_name 2>/dev/null)

        if [ -z "$S3_BUCKET" ]; then
            # Fallback: Query AWS using tags
            echo "  Querying AWS for S3 bucket with tags..."
            S3_BUCKET=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'jigsaw-puzzle-${ENVIRONMENT}-frontend')].Name | [0]" --output text 2>/dev/null)
        fi
    else
        # Fallback: Query AWS using tags
        echo "  Terraform directory not found, querying AWS directly..."
        S3_BUCKET=$(aws s3api list-buckets --query "Buckets[?contains(Name, 'jigsaw-puzzle-${ENVIRONMENT}-frontend')].Name | [0]" --output text 2>/dev/null)
    fi
fi

if [ -z "$S3_BUCKET" ] || [ "$S3_BUCKET" = "None" ]; then
    echo "Error: Could not determine S3 bucket name"
    echo "       Please set S3_BUCKET_NAME environment variable or ensure Terraform is configured"
    exit 1
fi

# Try to get CloudFront distribution ID
if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
    CLOUDFRONT_ID="$CLOUDFRONT_DISTRIBUTION_ID"
    echo "  Using CloudFront ID from environment variable: $CLOUDFRONT_ID"
else
    # Try to get from Terraform output (for local development)
    if [ -d "$TERRAFORM_DIR" ]; then
        cd "$TERRAFORM_DIR"
        CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null)

        if [ -z "$CLOUDFRONT_ID" ]; then
            # Fallback: Query AWS using S3 origin
            echo "  Querying AWS for CloudFront distribution..."
            CLOUDFRONT_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, '${S3_BUCKET}')].Id | [0]" --output text 2>/dev/null)
        fi
    else
        # Fallback: Query AWS using S3 origin
        echo "  Querying AWS for CloudFront distribution..."
        CLOUDFRONT_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?contains(Origins.Items[0].DomainName, '${S3_BUCKET}')].Id | [0]" --output text 2>/dev/null)
    fi
fi

if [ -z "$CLOUDFRONT_ID" ] || [ "$CLOUDFRONT_ID" = "None" ]; then
    echo "Warning: Could not determine CloudFront distribution ID"
    echo "         Deployment will continue, but cache invalidation will be skipped"
fi

echo "  ✓ S3 Bucket: $S3_BUCKET"
if [ -n "$CLOUDFRONT_ID" ] && [ "$CLOUDFRONT_ID" != "None" ]; then
    echo "  ✓ CloudFront ID: $CLOUDFRONT_ID"
fi
echo ""

# ============================================
# Step 1.5: Get API base URL
# ============================================
echo "Step 1.5: Resolving API base URL..."

# Try from environment variable first (for CI/CD)
if [ -n "$API_BASE_URL" ]; then
    API_ENDPOINT="$API_BASE_URL"
    echo "  Using API endpoint from environment variable: $API_ENDPOINT"
else
    # Try from SSM Parameter Store
    API_PARAMETER_NAME="/jigsaw-puzzle/frontend/${ENVIRONMENT}/api_base_url"
    echo "  Querying SSM Parameter: $API_PARAMETER_NAME"
    API_ENDPOINT=$(aws ssm get-parameter --name "$API_PARAMETER_NAME" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null)

    if [ -z "$API_ENDPOINT" ] || [ "$API_ENDPOINT" = "None" ]; then
        # Try from Terraform output (for local development)
        if [ -d "$TERRAFORM_DIR" ]; then
            cd "$TERRAFORM_DIR"
            API_ENDPOINT=$(terraform output -raw api_endpoint 2>/dev/null)
        fi
    fi
fi

if [ -z "$API_ENDPOINT" ] || [ "$API_ENDPOINT" = "None" ]; then
    echo "  Warning: Could not resolve API endpoint"
    echo "           Using default from .env.production"
else
    echo "  ✓ API Endpoint: $API_ENDPOINT"
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
if [ -n "$CLOUDFRONT_ID" ] && [ "$CLOUDFRONT_ID" != "None" ]; then
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text 2>/dev/null)

    if [ -n "$INVALIDATION_ID" ] && [ "$INVALIDATION_ID" != "None" ]; then
        echo "  ✓ Invalidation ID: $INVALIDATION_ID"
        echo "  (Cache invalidation is running in the background)"
    else
        echo "  ⚠️  Failed to create cache invalidation"
    fi
else
    echo "  ⚠️  Skipping cache invalidation (CloudFront ID not found)"
fi
echo ""

# Get CloudFront domain
CLOUDFRONT_DOMAIN=""
if [ -d "$TERRAFORM_DIR" ]; then
    cd "$TERRAFORM_DIR"
    CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name 2>/dev/null)
fi

if [ -z "$CLOUDFRONT_DOMAIN" ] || [ "$CLOUDFRONT_DOMAIN" = "None" ]; then
    # Try to get from AWS CLI
    if [ -n "$CLOUDFRONT_ID" ] && [ "$CLOUDFRONT_ID" != "None" ]; then
        CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution --id "$CLOUDFRONT_ID" --query 'Distribution.DomainName' --output text 2>/dev/null)
    fi
fi

echo "==================================="
echo "Deployment Complete! ✅"
echo "==================================="
echo ""
echo "S3 Bucket: $S3_BUCKET"
if [ -n "$CLOUDFRONT_DOMAIN" ] && [ "$CLOUDFRONT_DOMAIN" != "None" ]; then
    echo "Frontend URL: https://$CLOUDFRONT_DOMAIN"
    echo ""
    echo "Note: CloudFront cache invalidation may take a few minutes."
else
    echo "CloudFront: Not configured or not found"
fi
echo ""
if [ -n "$INVALIDATION_ID" ] && [ "$INVALIDATION_ID" != "None" ]; then
    echo "Check invalidation status:"
    echo "  aws cloudfront get-invalidation --distribution-id $CLOUDFRONT_ID --id $INVALIDATION_ID"
    echo ""
fi
