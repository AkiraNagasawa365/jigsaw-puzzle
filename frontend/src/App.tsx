import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import PuzzleCreate from './pages/puzzles/PuzzleCreate'
import PuzzleDetail from './pages/puzzles/PuzzleDetail'
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'

// Amplify設定を読み込み
import './config/amplify'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* 認証不要のルート */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* 認証必須のルート */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route
          path="/puzzles/new"
          element={
            <ProtectedRoute>
              <PuzzleCreate />
            </ProtectedRoute>
          }
        />
        <Route
          path="/puzzles/:puzzleId"
          element={
            <ProtectedRoute>
              <PuzzleDetail />
            </ProtectedRoute>
          }
        />
      </Routes>
    </AuthProvider>
  )
}

export default App
