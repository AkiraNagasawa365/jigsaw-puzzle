# GitHub Actions CI/CD セットアップ

このディレクトリには、自動テストとデプロイのためのGitHub Actionsワークフローが含まれています。

## ワークフロー一覧

### 1. CI（継続的インテグレーション）
**ファイル**: `ci.yml`

**トリガー**:
- `main`, `develop` ブランチへのプッシュ
- `main`, `develop` ブランチへのプルリクエスト

**実行内容**:

#### バックエンド
- Python 3.12 環境のセットアップ
- `uv` でパッケージインストール
- `mypy` による型チェック
- `pytest` による単体テスト実行
- `pytest` による統合テスト実行
- カバレッジレポートの生成とアップロード

#### フロントエンド
- Node.js 20 環境のセットアップ
- `npm ci` で依存関係インストール
- TypeScript型チェック (`tsc --noEmit`)
- ESLint実行
- ビルド確認

**成功条件**: 全テストが成功し、型エラーがゼロ

---

### 2. Lambda自動デプロイ
**ファイル**: `deploy-lambda.yml`

**トリガー**:
- `main` ブランチへのプッシュ
- 手動実行（`workflow_dispatch`）

**実行内容**:
- AWS クレデンシャル設定
- `./scripts/deploy-lambda.sh` 実行
- Lambda関数のデプロイ

**必要なSecrets**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---

### 3. フロントエンド自動デプロイ
**ファイル**: `deploy-frontend.yml`

**トリガー**:
- `main` ブランチへのプッシュ（`frontend/` 配下の変更時のみ）
- 手動実行（`workflow_dispatch`）

**実行内容**:
- フロントエンドビルド
- S3へのアップロード
- CloudFrontキャッシュの無効化

**必要なSecrets**:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

---

## セットアップ手順

### 🔐 推奨: OIDC認証（自動化）

**より安全で自動化された方法です！**

1. **Terraformでインフラ構築**:
   ```bash
   cd terraform/environments/dev
   # variables.tf でGitHubユーザー名を設定
   terraform apply
   ```

2. **GitHub Secretsに1つだけ設定**:
   - `AWS_ROLE_ARN`: Terraformの出力値 `github_actions_role_arn` をコピー

**詳細**: `docs/20251022_github-oidc-setup.md` を参照

---

### 従来の方法: Access Key（非推奨）

リポジトリの Settings > Secrets and variables > Actions で以下を追加:

```
AWS_ACCESS_KEY_ID: AWSアクセスキーID
AWS_SECRET_ACCESS_KEY: AWSシークレットアクセスキー
```

**デメリット**:
- ⚠️ 長期的な認証情報をGitHubに保存
- ⚠️ 定期的なローテーションが必要
- ⚠️ 漏洩リスクが高い

### 2. IAMポリシー例

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:*:function:jigsaw-puzzle-dev-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::jigsaw-puzzle-dev-frontend/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:ListDistributions"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## ワークフローの動作確認

### CIワークフロー
プルリクエストを作成すると自動的に実行されます。

```bash
# ローカルで事前確認
uv run mypy app
uv run pytest tests/
cd frontend && npm run lint && npx tsc --noEmit
```

### デプロイワークフロー
mainブランチにマージすると自動的にデプロイされます。

**手動実行**:
1. GitHub > Actions タブ
2. 実行したいワークフローを選択
3. "Run workflow" をクリック

---

## トラブルシューティング

### エラー: uv command not found
→ GitHub ActionsでのuvインストールStep が成功しているか確認

### エラー: AWS credentials not configured
→ GitHub Secrets が正しく設定されているか確認

### エラー: Permission denied
→ `scripts/deploy-*.sh` に実行権限があるか確認
→ ワークフローで `chmod +x` が実行されているか確認

### カバレッジレポートがアップロードされない
→ Codecov token が設定されているか確認（オプション）
→ `codecov/codecov-action@v4` のステップを削除してもOK

---

## 今後の改善案

### パフォーマンス最適化
- [ ] キャッシュの活用（uvキャッシュ、npmキャッシュ）
- [ ] 並列実行の最適化
- [ ] 差分デプロイ（変更があったファイルのみ）

### セキュリティ強化
- [ ] OpenID Connect (OIDC) による認証（Secretsを使わない）
- [ ] Dependabot によるセキュリティアップデート自動化
- [ ] CodeQL による静的解析

### 機能追加
- [ ] ステージング環境への自動デプロイ
- [ ] プルリクエストへのテスト結果コメント
- [ ] Slack通知
- [ ] パフォーマンステスト自動実行

---

## 参考リンク

- [GitHub Actions公式ドキュメント](https://docs.github.com/ja/actions)
- [AWS Actions](https://github.com/aws-actions)
- [uv公式ドキュメント](https://github.com/astral-sh/uv)
