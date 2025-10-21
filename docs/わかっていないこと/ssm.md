# AWS Systems Manager Parameter Store (SSM) メモ

- AWS が提供するキー・バリュー型の設定ストア。シークレットや設定値を安全に保存・バージョン管理できる。
- 値は AWS SDK / CLI / Terraform から取得・更新でき、IAM でアクセス権限を細かく制御できる。
- 本リポジトリでは `terraform/environments/*` で SSM パラメータを作成し、`scripts/sync_config.py` や CI/CD から取得して `.env` 生成や `VITE_` 変数注入に利用している。
- ローカル開発では `scripts/sync_config.py` のデフォルト (`--environment local`) が localhost 向け値を生成し、`--environment dev` などを指定した場合のみ SSM から AWS 側の設定を取得する。
