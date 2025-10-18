import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import PuzzleCreate from './pages/puzzles/PuzzleCreate'
import PuzzleDetail from './pages/puzzles/PuzzleDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/puzzles/new" element={<PuzzleCreate />} />
      <Route path="/puzzles/:puzzleId" element={<PuzzleDetail />} />
    </Routes>
  )
}

export default App
