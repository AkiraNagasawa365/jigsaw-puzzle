# DynamoDB table for Puzzles
resource "aws_dynamodb_table" "puzzles" {
  name         = "${var.project_name}-${var.environment}-puzzles"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"
  range_key    = "puzzleId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "puzzleId"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "S"
  }

  # GSI for querying by creation date
  global_secondary_index {
    name            = "CreatedAtIndex"
    hash_key        = "userId"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  # Enable TTL for automatic cleanup
  ttl {
    attribute_name = "expiresAt"
    enabled        = true
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-puzzles"
    }
  )
}

# DynamoDB table for Pieces
resource "aws_dynamodb_table" "pieces" {
  name         = "${var.project_name}-${var.environment}-pieces"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "puzzleId"
  range_key    = "pieceId"

  attribute {
    name = "puzzleId"
    type = "S"
  }

  attribute {
    name = "pieceId"
    type = "S"
  }

  attribute {
    name = "matched"
    type = "N"
  }

  # GSI for querying matched/unmatched pieces
  global_secondary_index {
    name            = "MatchedIndex"
    hash_key        = "puzzleId"
    range_key       = "matched"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Enable encryption at rest
  server_side_encryption {
    enabled = true
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-pieces"
    }
  )
}
