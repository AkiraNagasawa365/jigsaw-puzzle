import { useState } from 'react'
import type { PuzzleCreateRequest, PuzzleCreateResponse } from '../types/puzzle'

const PuzzleUpload = () => {
  const [pieceCount, setPieceCount] = useState<number>(300)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [message, setMessage] = useState<string>('')

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setMessage('画像ファイルを選択してください')
      return
    }

    setUploading(true)
    setMessage('')

    try {
      // Step 1: パズル登録APIを呼び出し
      const request: PuzzleCreateRequest = {
        pieceCount,
        fileName: file.name,
        userId: 'anonymous'
      }

      const response = await fetch('http://localhost:8000/puzzles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error('パズル登録に失敗しました')
      }

      const data: PuzzleCreateResponse = await response.json()

      // Step 2: S3に画像をアップロード
      const uploadResponse = await fetch(data.uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': file.type
        },
        body: file
      })

      if (!uploadResponse.ok) {
        throw new Error('画像のアップロードに失敗しました')
      }

      setMessage(`アップロード成功！パズルID: ${data.puzzleId}`)
      setFile(null)
    } catch (error) {
      setMessage(`エラー: ${error}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>パズル画像をアップロード</h2>

      <div style={{ marginBottom: '15px' }}>
        <label>
          ピース数:
          <select
            value={pieceCount}
            onChange={(e) => setPieceCount(Number(e.target.value))}
            style={{ marginLeft: '10px', padding: '5px' }}
          >
            <option value={100}>100</option>
            <option value={300}>300</option>
            <option value={500}>500</option>
            <option value={1000}>1000</option>
            <option value={2000}>2000</option>
          </select>
        </label>
      </div>

      <div style={{ marginBottom: '15px' }}>
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
        />
      </div>

      {file && (
        <div style={{ marginBottom: '15px' }}>
          選択されたファイル: {file.name}
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{
          padding: '10px 20px',
          backgroundColor: uploading ? '#ccc' : '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: uploading ? 'not-allowed' : 'pointer'
        }}
      >
        {uploading ? 'アップロード中...' : 'アップロード'}
      </button>

      {message && (
        <div style={{
          marginTop: '15px',
          padding: '10px',
          backgroundColor: message.includes('成功') ? '#d4edda' : '#f8d7da',
          borderRadius: '4px'
        }}>
          {message}
        </div>
      )}
    </div>
  )
}

export default PuzzleUpload
