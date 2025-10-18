// パズルの型定義
export interface Puzzle {
  puzzleId: string
  userId: string
  puzzleName: string  // ユーザーが決める名前（例：「富士山の風景」）
  pieceCount: number
  fileName?: string   // オプショナル（画像未アップロードの場合はない）
  s3Key?: string      // オプショナル（画像未アップロードの場合はない）
  status: 'pending' | 'uploaded' | 'processing' | 'completed'
  createdAt: string
  updatedAt: string
}

// パズル作成リクエストの型（画像なし）
export interface PuzzleCreateRequest {
  puzzleName: string
  pieceCount: number
  userId: string
}

// パズル作成レスポンスの型
export interface PuzzleCreateResponse {
  puzzleId: string
  puzzleName: string
  pieceCount: number
  status: string
  message: string
}

// 画像アップロードURL取得リクエストの型
export interface UploadUrlRequest {
  fileName: string
  userId: string
}

// 画像アップロードURL取得レスポンスの型
export interface UploadUrlResponse {
  puzzleId: string
  uploadUrl: string
  expiresIn: number
  message: string
}
