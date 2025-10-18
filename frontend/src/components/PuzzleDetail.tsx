import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import type { Puzzle, UploadUrlResponse } from '../types/puzzle'
import { API_BASE_URL } from '../config/api'

const PuzzleDetail = () => {
  const { puzzleId } = useParams<{ puzzleId: string }>()
  const navigate = useNavigate()
  const [puzzle, setPuzzle] = useState<Puzzle | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  // 画像アップロード用の状態
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMessage, setUploadMessage] = useState<string>('')

  useEffect(() => {
    if (puzzleId) {
      fetchPuzzle(puzzleId)
    }
  }, [puzzleId])

  const fetchPuzzle = async (id: string) => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${API_BASE_URL}/puzzles/${id}?user_id=anonymous`)

      if (!response.ok) {
        throw new Error('パズルの取得に失敗しました')
      }

      const data = await response.json()
      setPuzzle(data)
    } catch (err) {
      setError(`エラー: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setUploadMessage('')
    }
  }

  const handleUpload = async () => {
    if (!file || !puzzleId) {
      setUploadMessage('画像ファイルを選択してください')
      return
    }

    setUploading(true)
    setUploadMessage('')

    try {
      // Step 1: アップロードURL取得
      const urlResponse = await fetch(`${API_BASE_URL}/puzzles/${puzzleId}/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          fileName: file.name,
          userId: 'anonymous'
        })
      })

      if (!urlResponse.ok) {
        throw new Error('アップロードURLの取得に失敗しました')
      }

      const urlData: UploadUrlResponse = await urlResponse.json()

      // Step 2: S3に画像をアップロード
      const uploadResponse = await fetch(urlData.uploadUrl, {
        method: 'PUT',
        headers: {
          'Content-Type': file.type
        },
        body: file
      })

      if (!uploadResponse.ok) {
        throw new Error('画像のアップロードに失敗しました')
      }

      setUploadMessage('画像のアップロードに成功しました！')
      setFile(null)

      // パズル情報を再取得
      fetchPuzzle(puzzleId)

    } catch (error) {
      setUploadMessage(`エラー: ${error}`)
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <button onClick={() => navigate('/')} style={backButtonStyle}>
          ← 一覧に戻る
        </button>
        <div style={{ marginTop: '20px' }}>読み込み中...</div>
      </div>
    )
  }

  if (error || !puzzle) {
    return (
      <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <button onClick={() => navigate('/')} style={backButtonStyle}>
          ← 一覧に戻る
        </button>
        <div style={{
          marginTop: '20px',
          padding: '20px',
          backgroundColor: '#f8d7da',
          borderRadius: '4px',
          color: '#721c24'
        }}>
          {error || 'パズルが見つかりませんでした'}
        </div>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <button onClick={() => navigate('/')} style={backButtonStyle}>
        ← 一覧に戻る
      </button>

      <div style={{
        marginTop: '20px',
        padding: '20px',
        border: '1px solid #ccc',
        borderRadius: '8px',
        backgroundColor: '#fff'
      }}>
        <h1 style={{ margin: '0 0 20px 0' }}>{puzzle.puzzleName}</h1>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '15px',
          marginBottom: '30px'
        }}>
          <div>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#666' }}>パズル情報</h3>
            <div style={{ fontSize: '14px' }}>
              <p><strong>パズルID:</strong> {puzzle.puzzleId}</p>
              <p><strong>ピース数:</strong> {puzzle.pieceCount}</p>
              <p><strong>ファイル名:</strong> {puzzle.fileName}</p>
              <p>
                <strong>ステータス:</strong>{' '}
                <span style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  backgroundColor: puzzle.status === 'completed' ? '#d4edda' :
                                   puzzle.status === 'processing' ? '#fff3cd' : '#f8d7da',
                  color: puzzle.status === 'completed' ? '#155724' :
                         puzzle.status === 'processing' ? '#856404' : '#721c24'
                }}>
                  {puzzle.status === 'pending' ? '待機中' :
                   puzzle.status === 'processing' ? '処理中' : '完了'}
                </span>
              </p>
            </div>
          </div>

          <div>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '16px', color: '#666' }}>日時情報</h3>
            <div style={{ fontSize: '14px' }}>
              <p><strong>作成日時:</strong><br />{new Date(puzzle.createdAt).toLocaleString('ja-JP')}</p>
              <p><strong>更新日時:</strong><br />{new Date(puzzle.updatedAt).toLocaleString('ja-JP')}</p>
            </div>
          </div>
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #ddd', margin: '20px 0' }} />

        <div>
          <h2 style={{ margin: '0 0 15px 0' }}>パズル画像</h2>

          {puzzle.status === 'pending' && (
            <div>
              <div style={{
                padding: '20px',
                backgroundColor: '#fff3cd',
                borderRadius: '4px',
                color: '#856404',
                marginBottom: '15px'
              }}>
                <p style={{ margin: '0' }}>
                  <strong>⚠️ 画像がまだアップロードされていません</strong>
                </p>
                <p style={{ fontSize: '14px', marginTop: '5px', marginBottom: '0' }}>
                  下のフォームから画像をアップロードしてください
                </p>
              </div>

              {/* 画像アップロードフォーム */}
              <div style={{
                padding: '20px',
                border: '2px dashed #ccc',
                borderRadius: '8px',
                backgroundColor: '#f8f9fa'
              }}>
                <h3 style={{ margin: '0 0 15px 0', fontSize: '16px' }}>画像をアップロード</h3>

                <div style={{ marginBottom: '15px' }}>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    disabled={uploading}
                    style={{ fontSize: '14px' }}
                  />
                </div>

                {file && (
                  <div style={{ marginBottom: '15px', fontSize: '14px', color: '#666' }}>
                    選択されたファイル: <strong>{file.name}</strong>
                  </div>
                )}

                <button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: (!file || uploading) ? '#ccc' : '#007bff',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: (!file || uploading) ? 'not-allowed' : 'pointer',
                    fontSize: '16px',
                    fontWeight: 'bold'
                  }}
                >
                  {uploading ? 'アップロード中...' : '画像をアップロード'}
                </button>

                {uploadMessage && (
                  <div style={{
                    marginTop: '15px',
                    padding: '10px',
                    backgroundColor: uploadMessage.includes('成功') ? '#d4edda' : '#f8d7da',
                    borderRadius: '4px',
                    color: uploadMessage.includes('成功') ? '#155724' : '#721c24'
                  }}>
                    {uploadMessage}
                  </div>
                )}
              </div>
            </div>
          )}

          {puzzle.status !== 'pending' && puzzle.s3Key && (
            <div style={{
              padding: '20px',
              backgroundColor: '#d4edda',
              borderRadius: '4px',
              color: '#155724'
            }}>
              <p style={{ margin: '0' }}>
                <strong>✅ 画像がアップロードされています</strong>
              </p>
              <p style={{ fontSize: '14px', marginTop: '10px', color: '#666' }}>
                S3キー: {puzzle.s3Key}
              </p>
              <p style={{ fontSize: '14px', marginTop: '5px', color: '#999' }}>
                ※画像表示機能は今後実装予定です
              </p>
            </div>
          )}
        </div>

        <hr style={{ border: 'none', borderTop: '1px solid #ddd', margin: '20px 0' }} />

        <div>
          <h2 style={{ margin: '0 0 15px 0' }}>ピース画像一覧</h2>

          <div style={{
            padding: '40px 20px',
            backgroundColor: '#f8f9fa',
            borderRadius: '4px',
            textAlign: 'center',
            color: '#666'
          }}>
            <p>ピース画像の表示機能は今後実装予定です。</p>
            <p style={{ fontSize: '14px', marginTop: '10px' }}>
              （このパズルには {puzzle.pieceCount} 個のピースが含まれる予定です）
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

const backButtonStyle: React.CSSProperties = {
  padding: '10px 20px',
  backgroundColor: '#6c757d',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '16px'
}

export default PuzzleDetail
