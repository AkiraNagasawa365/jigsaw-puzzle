import { useNavigate } from 'react-router-dom'
import PuzzleList from '../components/PuzzleList'
import type { Puzzle } from '../types/puzzle'

const Home = () => {
  const navigate = useNavigate()

  const handlePuzzleClick = (puzzle: Puzzle) => {
    console.log('選択されたパズル:', puzzle)
    navigate(`/puzzles/${puzzle.puzzleId}`)
  }

  const handleCreateNew = () => {
    navigate('/puzzles/new')
  }

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1 style={{ margin: '0 0 5px 0' }}>Jigsaw Puzzle Helper</h1>
          <p style={{ margin: '0', color: '#666' }}>パズル登録システムへようこそ</p>
        </div>
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
