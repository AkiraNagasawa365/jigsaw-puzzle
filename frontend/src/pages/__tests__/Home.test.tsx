import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Home from '../Home'
import type { Puzzle } from '../../types/puzzle'

// react-router-domのnavigateをモック
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// AuthContextをモック
const mockLogout = vi.fn()
const mockUser = {
  email: 'test@example.com',
  userId: 'test-user-123',
}

vi.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    logout: mockLogout,
  }),
}))

const mockPuzzles: Puzzle[] = [
  {
    puzzleId: '123',
    userId: 'test-user-123',
    puzzleName: 'テストパズル',
    pieceCount: 300,
    status: 'completed',
    createdAt: '2025-10-22T10:00:00Z',
    updatedAt: '2025-10-22T10:00:00Z',
  },
]

describe('Home', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: mockPuzzles }),
    })
  })

  it('ページタイトルが表示される', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )

    expect(screen.getByText('Jigsaw Puzzle Helper')).toBeInTheDocument()
    expect(screen.getByText('パズル登録システムへようこそ')).toBeInTheDocument()
  })

  it('ログインユーザーのメールアドレスが表示される', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )

    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('新規作成ボタンが表示され、クリックで作成画面に遷移する', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )

    const createButton = screen.getByText('+ 新規作成')
    await user.click(createButton)

    expect(mockNavigate).toHaveBeenCalledWith('/puzzles/new')
  })

  it('ログアウトボタンが機能する', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )

    const logoutButton = screen.getByText('ログアウト')
    await user.click(logoutButton)

    expect(mockLogout).toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('PuzzleListコンポーネントが表示される', () => {
    render(
      <BrowserRouter>
        <Home />
      </BrowserRouter>
    )

    // PuzzleListが読み込まれることを確認（読み込み中の状態）
    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })
})
