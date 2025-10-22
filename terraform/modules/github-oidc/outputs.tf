output "github_actions_role_arn" {
  description = "GitHub ActionsがAssumeするIAMロールのARN"
  value       = aws_iam_role.github_actions.arn
}

output "oidc_provider_arn" {
  description = "GitHub OIDC プロバイダーのARN"
  value       = aws_iam_openid_connect_provider.github.arn
}
