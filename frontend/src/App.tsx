import { Routes, Route } from 'react-router-dom'
import Home from './pages/Home'
import PuzzleCreate from './pages/PuzzleCreate'
import PuzzleDetail from './components/PuzzleDetail'

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
