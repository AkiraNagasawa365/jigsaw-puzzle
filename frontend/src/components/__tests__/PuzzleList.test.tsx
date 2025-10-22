import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import PuzzleList from '../PuzzleList'
import type { Puzzle } from '../../types/puzzle'

const mockPuzzles: Puzzle[] = [
  {
    puzzleId: '123',
    userId: 'anonymous',
    puzzleName: 'テストパズル1',
    pieceCount: 300,
    status: 'completed',
    createdAt: '2025-10-22T10:00:00Z',
    updatedAt: '2025-10-22T10:00:00Z',
  },
  {
    puzzleId: '456',
    userId: 'anonymous',
    puzzleName: 'テストパズル2',
    pieceCount: 500,
    status: 'pending',
    createdAt: '2025-10-22T11:00:00Z',
    updatedAt: '2025-10-22T11:00:00Z',
  },
]

describe('PuzzleList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('ローディング状態を表示する', () => {
    // fetchを永続的にpendingにする
    global.fetch = vi.fn(() => new Promise(() => {})) as any

    render(<PuzzleList />)

    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  it('パズル一覧を表示する', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: mockPuzzles }),
    })

    render(<PuzzleList />)

    await waitFor(() => {
      expect(screen.getByText('パズル一覧 (2件)')).toBeInTheDocument()
    })

    expect(screen.getByText('テストパズル1')).toBeInTheDocument()
    expect(screen.getByText('テストパズル2')).toBeInTheDocument()
    const pieceCounts = screen.getAllByText('ピース数:')
    expect(pieceCounts.length).toBeGreaterThan(0)
  })

  it('空の状態を表示する', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: [] }),
    })

    render(<PuzzleList />)

    await waitFor(() => {
      expect(screen.getByText('まだパズルが登録されていません')).toBeInTheDocument()
    })
  })

  it('エラー状態を表示する', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
    })

    render(<PuzzleList />)

    await waitFor(() => {
      expect(screen.getByText(/エラー:/)).toBeInTheDocument()
    })
  })

  it('パズルクリック時にコールバックが呼ばれる', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: mockPuzzles }),
    })

    const handleClick = vi.fn()
    render(<PuzzleList onPuzzleClick={handleClick} />)

    await waitFor(() => {
      expect(screen.getByText('テストパズル1')).toBeInTheDocument()
    })

    const puzzle1 = screen.getByText('テストパズル1').closest('div')
    if (puzzle1) {
      await userEvent.click(puzzle1)
    }

    expect(handleClick).toHaveBeenCalledWith(mockPuzzles[0])
  })

  it('更新ボタンクリックでデータを再取得する', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: mockPuzzles }),
    })

    render(<PuzzleList />)

    await waitFor(() => {
      expect(screen.getByText('パズル一覧 (2件)')).toBeInTheDocument()
    })

    // 最初のfetch呼び出し
    expect(global.fetch).toHaveBeenCalledTimes(1)

    const refreshButton = screen.getByText('更新')
    await userEvent.click(refreshButton)

    // 2回目のfetch呼び出し
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('正しいAPIエンドポイントを呼び出す', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: [] }),
    })

    render(<PuzzleList userId="test-user" />)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/users/test-user/puzzles')
      )
    })
  })

  it('ステータスに応じた表示が変わる', async () => {
    const puzzlesWithDifferentStatuses: Puzzle[] = [
      {
        ...mockPuzzles[0],
        status: 'pending',
      },
      {
        ...mockPuzzles[1],
        status: 'processing',
      },
      {
        puzzleId: '789',
        userId: 'anonymous',
        puzzleName: 'テストパズル3',
        pieceCount: 1000,
        status: 'completed',
        createdAt: '2025-10-22T12:00:00Z',
        updatedAt: '2025-10-22T12:00:00Z',
      },
    ]

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzles: puzzlesWithDifferentStatuses }),
    })

    render(<PuzzleList />)

    await waitFor(() => {
      expect(screen.getByText('待機中')).toBeInTheDocument()
      expect(screen.getByText('処理中')).toBeInTheDocument()
      expect(screen.getByText('完了')).toBeInTheDocument()
    })
  })
})
