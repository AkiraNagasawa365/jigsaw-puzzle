// パズルの型定義
export interface Puzzle {
  puzzleId: string
  userId: string
  pieceCount: number
  fileName: string
  s3Key: string
  status: 'pending' | 'processing' | 'completed'
  createdAt: string
  updatedAt: string
}

// パズル登録リクエストの型
export interface PuzzleCreateRequest {
  pieceCount: number
  fileName: string
  userId: string
}

// パズル登録レスポンスの型
export interface PuzzleCreateResponse {
  puzzleId: string
  uploadUrl: string
  expiresIn: number
  message: string
}
