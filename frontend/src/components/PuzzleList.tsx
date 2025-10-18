import { useState, useEffect, useCallback } from 'react'
import type { Puzzle } from '../types/puzzle'

interface PuzzleListProps {
  userId?: string
  onPuzzleClick?: (puzzle: Puzzle) => void
}

const PuzzleList = ({ userId = 'anonymous', onPuzzleClick }: PuzzleListProps) => {
  const [puzzles, setPuzzles] = useState<Puzzle[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')

  const fetchPuzzles = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(`http://localhost:8000/users/${userId}/puzzles`)

      if (!response.ok) {
        throw new Error('パズル一覧の取得に失敗しました')
      }

      const data = await response.json()
      setPuzzles(data.puzzles || [])
    } catch (err) {
      setError(`エラー: ${err}`)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchPuzzles()
  }, [fetchPuzzles])

  const handlePuzzleClick = (puzzle: Puzzle) => {
    if (onPuzzleClick) {
      onPuzzleClick(puzzle)
    }
  }

  if (loading) {
    return <div style={{ padding: '20px' }}>読み込み中...</div>
  }

  if (error) {
    return (
      <div style={{
        padding: '20px',
        backgroundColor: '#f8d7da',
        borderRadius: '4px',
        color: '#721c24'
      }}>
        {error}
      </div>
    )
  }

  if (puzzles.length === 0) {
    return (
      <div style={{
        padding: '20px',
        border: '1px solid #ccc',
        borderRadius: '8px',
        textAlign: 'center',
        color: '#666'
      }}>
        <p>まだパズルが登録されていません</p>
        <p style={{ fontSize: '14px' }}>上のフォームからパズルをアップロードしてください</p>
      </div>
    )
  }

  return (
    <div style={{ padding: '20px', border: '1px solid #ccc', borderRadius: '8px' }}>
      <h2>パズル一覧 ({puzzles.length}件)</h2>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))',
        gap: '15px',
        marginTop: '15px'
      }}>
        {puzzles.map((puzzle) => (
          <div
            key={puzzle.puzzleId}
            onClick={() => handlePuzzleClick(puzzle)}
            style={{
              border: '1px solid #ddd',
              borderRadius: '8px',
              padding: '15px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              backgroundColor: '#fff'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)'
              e.currentTarget.style.transform = 'translateY(-2px)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.boxShadow = 'none'
              e.currentTarget.style.transform = 'translateY(0)'
            }}
          >
            <h3 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>
              {puzzle.puzzleName}
            </h3>

            <div style={{ fontSize: '14px', color: '#666' }}>
              <p style={{ margin: '5px 0' }}>
                <strong>ピース数:</strong> {puzzle.pieceCount}
              </p>
              <p style={{ margin: '5px 0' }}>
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
              <p style={{ margin: '5px 0', fontSize: '12px', color: '#999' }}>
                {new Date(puzzle.createdAt).toLocaleString('ja-JP')}
              </p>
            </div>
          </div>
        ))}
      </div>

      <button
        onClick={fetchPuzzles}
        style={{
          marginTop: '15px',
          padding: '8px 16px',
          backgroundColor: '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        更新
      </button>
    </div>
  )
}

export default PuzzleList
