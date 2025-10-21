import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import PuzzleList from '../components/PuzzleList'
import type { Puzzle } from '../types/puzzle'

const Home = () => {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handlePuzzleClick = (puzzle: Puzzle) => {
    console.log('選択されたパズル:', puzzle)
    navigate(`/puzzles/${puzzle.puzzleId}`)
  }

  const handleCreateNew = () => {
    navigate('/puzzles/new')
  }

  const handleLogout = async () => {
    try {
      await logout()
      navigate('/login')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      {/* ヘッダー部分 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', paddingBottom: '10px', borderBottom: '2px solid #eee' }}>
        <div>
          <h1 style={{ margin: '0 0 5px 0' }}>Jigsaw Puzzle Helper</h1>
          <p style={{ margin: '0', color: '#666' }}>パズル登録システムへようこそ</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          {user && (
            <span style={{ color: '#666', fontSize: '14px' }}>
              {user.email}
            </span>
          )}
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: '#6c757d',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            ログアウト
          </button>
        </div>
      </div>

      {/* コンテンツ部分 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0 }}>マイパズル</h2>
        <button
          onClick={handleCreateNew}
          style={{
            padding: '12px 24px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: 'bold',
            whiteSpace: 'nowrap'
          }}
        >
          + 新規作成
        </button>
      </div>

      <div>
        <PuzzleList onPuzzleClick={handlePuzzleClick} />
      </div>
    </div>
  )
}

export default Home
