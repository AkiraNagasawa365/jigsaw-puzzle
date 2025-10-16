output "puzzles_table_name" {
  description = "Name of the Puzzles DynamoDB table"
  value       = aws_dynamodb_table.puzzles.name
}

output "puzzles_table_arn" {
  description = "ARN of the Puzzles DynamoDB table"
  value       = aws_dynamodb_table.puzzles.arn
}

output "pieces_table_name" {
  description = "Name of the Pieces DynamoDB table"
  value       = aws_dynamodb_table.pieces.name
}

output "pieces_table_arn" {
  description = "ARN of the Pieces DynamoDB table"
  value       = aws_dynamodb_table.pieces.arn
}
