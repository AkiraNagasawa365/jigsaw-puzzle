# ============================================
# REST API Gateway for Jigsaw Puzzle
# ============================================
# This module creates an API Gateway that provides HTTP endpoints
# to invoke Lambda functions

# --------------------------------------------
# 1. REST API (APIのベース)
# --------------------------------------------
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_name}-${var.environment}-api"
  description = "API Gateway for ${var.project_name} ${var.environment} environment"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = merge(
    var.common_tags,
    {
      Name = "${var.project_name}-${var.environment}-api"
    }
  )
}

# --------------------------------------------
# 2. リソース: /puzzles
# --------------------------------------------
# URLのパス部分を定義
# 例: https://api.example.com/dev/puzzles
resource "aws_api_gateway_resource" "puzzles" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "puzzles"
}

# --------------------------------------------
# 3. メソッド: POST /puzzles
# --------------------------------------------
# POSTリクエストを受け付ける設定
resource "aws_api_gateway_method" "post_puzzles" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.puzzles.id
  http_method   = "POST"
  authorization = "NONE" # 認証なし（後でCognitoを追加可能）

  # リクエストバリデーション
  request_parameters = {
    "method.request.header.Content-Type" = true
  }
}

# --------------------------------------------
# 4. Lambda統合
# --------------------------------------------
# API GatewayからLambda関数を呼び出す設定
resource "aws_api_gateway_integration" "lambda_post_puzzles" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.puzzles.id
  http_method = aws_api_gateway_method.post_puzzles.http_method

  # Lambda関数との統合タイプ
  integration_http_method = "POST"
  type                    = "AWS_PROXY" # Lambda Proxy統合（推奨）
  uri                     = var.puzzle_register_lambda_invoke_arn
}

# --------------------------------------------
# 5. メソッドレスポンス
# --------------------------------------------
# API Gatewayがクライアントに返すレスポンスの設定
resource "aws_api_gateway_method_response" "post_puzzles_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.puzzles.id
  http_method = aws_api_gateway_method.post_puzzles.http_method
  status_code = "200"

  # CORSヘッダー
  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# --------------------------------------------
# 6. CORS設定: OPTIONS /puzzles
# --------------------------------------------
# ブラウザからのリクエストに必要なCORS設定

# OPTIONSメソッド
resource "aws_api_gateway_method" "options_puzzles" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.puzzles.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# OPTIONSメソッドの統合（Mockレスポンス）
resource "aws_api_gateway_integration" "options_puzzles" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.puzzles.id
  http_method = aws_api_gateway_method.options_puzzles.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# OPTIONSメソッドのレスポンス
resource "aws_api_gateway_method_response" "options_puzzles_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.puzzles.id
  http_method = aws_api_gateway_method.options_puzzles.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

# OPTIONSメソッドの統合レスポンス
resource "aws_api_gateway_integration_response" "options_puzzles_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.puzzles.id
  http_method = aws_api_gateway_method.options_puzzles.http_method
  status_code = aws_api_gateway_method_response.options_puzzles_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'" # 本番環境では制限すること
  }
}

# --------------------------------------------
# 7. Lambda権限
# --------------------------------------------
# API GatewayがLambda関数を呼び出す権限を付与
resource "aws_lambda_permission" "api_gateway_invoke_puzzle_register" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.puzzle_register_lambda_function_name
  principal     = "apigateway.amazonaws.com"

  # API Gatewayの特定のエンドポイントからのみ許可
  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# --------------------------------------------
# 8. デプロイメント
# --------------------------------------------
# API Gatewayを実際に使えるようにデプロイ
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  # リソースが変更されたら自動的に再デプロイ
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.puzzles.id,
      aws_api_gateway_method.post_puzzles.id,
      aws_api_gateway_integration.lambda_post_puzzles.id,
      aws_api_gateway_method.options_puzzles.id,
      aws_api_gateway_integration.options_puzzles.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.lambda_post_puzzles,
    aws_api_gateway_integration.options_puzzles,
  ]
}

# --------------------------------------------
# 9. ステージ（環境）
# --------------------------------------------
# dev, staging, prodなどの環境を分けるためのステージ
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  # アクセスログ設定
  # 注意: ログを有効にするには、AWSアカウント全体でCloudWatch Logsロールの設定が必要
  # 開発初期段階では一旦無効化
  # access_log_settings {
  #   destination_arn = aws_cloudwatch_log_group.api_gateway.arn
  #   format = jsonencode({
  #     requestId      = "$context.requestId"
  #     ip             = "$context.identity.sourceIp"
  #     caller         = "$context.identity.caller"
  #     user           = "$context.identity.user"
  #     requestTime    = "$context.requestTime"
  #     httpMethod     = "$context.httpMethod"
  #     resourcePath   = "$context.resourcePath"
  #     status         = "$context.status"
  #     protocol       = "$context.protocol"
  #     responseLength = "$context.responseLength"
  #   })
  # }

  tags = var.common_tags
}

# --------------------------------------------
# 10. CloudWatch Logs
# --------------------------------------------
# API Gatewayのアクセスログを保存
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/api-gateway/${var.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = var.common_tags
}

# --------------------------------------------
# 11. メソッド設定（オプション）
# --------------------------------------------
# スロットリング、キャッシュなどの設定
resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    # ロギング設定
    # 注意: ログを有効にするには、AWSアカウント全体でCloudWatch Logsロールの設定が必要
    # 開発初期段階では一旦無効化
    # logging_level      = "INFO"
    # data_trace_enabled = true
    metrics_enabled    = true  # メトリクスは有効（ログとは別）

    # スロットリング設定（Rate Limiting）
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
  }
}
