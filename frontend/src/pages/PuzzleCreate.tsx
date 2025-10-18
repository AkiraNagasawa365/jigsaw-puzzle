import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import type { PuzzleCreateRequest, PuzzleCreateResponse } from '../types/puzzle'
import { API_BASE_URL } from '../config/api'

const PuzzleCreate = () => {
  const navigate = useNavigate()
  const [puzzleName, setPuzzleName] = useState<string>('')
  const [pieceCount, setPieceCount] = useState<number>(300)
  const [creating, setCreating] = useState(false)
  const [message, setMessage] = useState<string>('')

  const handleCreate = async () => {
    if (!puzzleName.trim()) {
      setMessage('パズル名を入力してください')
      return
    }

    setCreating(true)
    setMessage('')

    try {
      const request: PuzzleCreateRequest = {
        puzzleName,
        pieceCount,
        userId: 'anonymous'
      }

      const response = await fetch(`${API_BASE_URL}/puzzles`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(request)
      })

      if (!response.ok) {
        throw new Error('パズル作成に失敗しました')
      }

      const data: PuzzleCreateResponse = await response.json()

      // 成功したら詳細画面に遷移（画像アップロードのため）
      navigate(`/puzzles/${data.puzzleId}`)

    } catch (error) {
      setMessage(`エラー: ${error}`)
      setCreating(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <button
        onClick={() => navigate('/')}
        style={{
          padding: '10px 20px',
          backgroundColor: '#6c757d',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '16px',
          marginBottom: '20px'
        }}
      >
        ← 一覧に戻る
      </button>

      <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px', backgroundColor: '#fff' }}>
        <h2>パズル新規作成</h2>
        <p style={{ color: '#666', fontSize: '14px' }}>
          まずパズルプロジェクトを作成してから、画像をアップロードします
        </p>

        <div style={{ marginTop: '20px', marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            パズル名 <span style={{ color: 'red' }}>*</span>
          </label>
          <input
            type="text"
            value={puzzleName}
            onChange={(e) => setPuzzleName(e.target.value)}
            placeholder="例：富士山の風景、海の絵"
            style={{
              width: '100%',
              padding: '10px',
              fontSize: '16px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              boxSizing: 'border-box'
            }}
          />
        </div>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
            ピース数 <span style={{ color: 'red' }}>*</span>
          </label>
          <select
            value={pieceCount}
            onChange={(e) => setPieceCount(Number(e.target.value))}
            style={{
              width: '100%',
              padding: '10px',
              fontSize: '16px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              boxSizing: 'border-box'
            }}
          >
            <option value={100}>100ピース</option>
            <option value={300}>300ピース</option>
            <option value={500}>500ピース</option>
            <option value={1000}>1000ピース</option>
            <option value={2000}>2000ピース</option>
          </select>
        </div>

        <button
          onClick={handleCreate}
          disabled={!puzzleName.trim() || creating}
          style={{
            width: '100%',
            padding: '12px 20px',
            backgroundColor: (!puzzleName.trim() || creating) ? '#ccc' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: (!puzzleName.trim() || creating) ? 'not-allowed' : 'pointer',
            fontSize: '16px',
            fontWeight: 'bold'
          }}
        >
          {creating ? '作成中...' : 'パズルを作成'}
        </button>

        {message && (
          <div style={{
            marginTop: '15px',
            padding: '10px',
            backgroundColor: message.includes('成功') || message.includes('作成') ? '#d4edda' : '#f8d7da',
            borderRadius: '4px',
            color: message.includes('成功') || message.includes('作成') ? '#155724' : '#721c24'
          }}>
            {message}
          </div>
        )}

        <div style={{
          marginTop: '20px',
          padding: '15px',
          backgroundColor: '#e7f3ff',
          borderLeft: '4px solid #2196F3',
          borderRadius: '4px'
        }}>
          <p style={{ margin: '0', fontSize: '14px', color: '#0c5460' }}>
            <strong>💡 ヒント：</strong> パズルを作成すると、詳細画面に移動します。そこで画像をアップロードできます。
          </p>
        </div>
      </div>
    </div>
  )
}

export default PuzzleCreate
