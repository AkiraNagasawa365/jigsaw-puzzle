output "puzzle_register_function_name" {
  description = "Name of the puzzle register Lambda function"
  value       = aws_lambda_function.puzzle_register.function_name
}

output "puzzle_register_function_arn" {
  description = "ARN of the puzzle register Lambda function"
  value       = aws_lambda_function.puzzle_register.arn
}

output "puzzle_register_invoke_arn" {
  description = "Invoke ARN of the puzzle register Lambda function"
  value       = aws_lambda_function.puzzle_register.invoke_arn
}
