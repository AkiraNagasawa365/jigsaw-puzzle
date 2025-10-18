// API設定

// 環境変数からAPIベースURLを取得
// デフォルト値はローカル開発用
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// デバッグ用：現在のAPI URLをログ出力
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL)
}
