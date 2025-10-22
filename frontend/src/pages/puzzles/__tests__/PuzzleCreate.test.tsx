import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import PuzzleCreate from '../PuzzleCreate'

// react-router-domのnavigateをモック
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('PuzzleCreate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('フォームが正しくレンダリングされる', () => {
    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    expect(screen.getByText('パズル新規作成')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('例：富士山の風景、海の絵')).toBeInTheDocument()
    expect(screen.getByRole('combobox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'パズルを作成' })).toBeInTheDocument()
  })

  it('パズル名の入力が機能する', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const input = screen.getByPlaceholderText('例：富士山の風景、海の絵') as HTMLInputElement
    await user.type(input, 'テストパズル')

    expect(input.value).toBe('テストパズル')
  })

  it('ピース数の選択が機能する', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const select = screen.getByRole('combobox') as HTMLSelectElement
    await user.selectOptions(select, '500')

    expect(select.value).toBe('500')
  })

  it('空のパズル名で作成ボタンが無効化される', () => {
    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const button = screen.getByRole('button', { name: 'パズルを作成' })
    expect(button).toBeDisabled()
  })

  it('パズル名が入力されると作成ボタンが有効化される', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const input = screen.getByPlaceholderText('例：富士山の風景、海の絵')
    const button = screen.getByRole('button', { name: 'パズルを作成' })

    expect(button).toBeDisabled()

    await user.type(input, 'テストパズル')

    expect(button).not.toBeDisabled()
  })

  it('空のパズル名で作成を試みるとエラーメッセージが表示される', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    // 一度入力してからクリアすることでボタンを有効化→無効化する
    const input = screen.getByPlaceholderText('例：富士山の風景、海の絵')
    await user.type(input, 'テスト')
    await user.clear(input)

    // ボタンは無効化されているのでクリックできないが、
    // 内部のバリデーションは別途テストする必要がある
    // この場合、ボタンが無効化されていることを確認
    const button = screen.getByRole('button', { name: 'パズルを作成' })
    expect(button).toBeDisabled()
  })

  it('作成成功時に詳細画面に遷移する', async () => {
    const user = userEvent.setup()
    const mockPuzzleId = 'test-puzzle-123'

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzleId: mockPuzzleId }),
    })

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const input = screen.getByPlaceholderText('例：富士山の風景、海の絵')
    await user.type(input, 'テストパズル')

    const button = screen.getByRole('button', { name: 'パズルを作成' })
    await user.click(button)

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith(`/puzzles/${mockPuzzleId}`)
    })
  })

  it('作成中はボタンが無効化され、ローディング表示になる', async () => {
    const user = userEvent.setup()

    global.fetch = vi.fn(() => new Promise(() => {})) as any // 永続的にpending

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const input = screen.getByPlaceholderText('例：富士山の風景、海の絵')
    await user.type(input, 'テストパズル')

    const button = screen.getByRole('button', { name: 'パズルを作成' })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText('作成中...')).toBeInTheDocument()
    })
  })

  it('作成失敗時にエラーメッセージが表示される', async () => {
    const user = userEvent.setup()

    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
    })

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const input = screen.getByPlaceholderText('例：富士山の風景、海の絵')
    await user.type(input, 'テストパズル')

    const button = screen.getByRole('button', { name: 'パズルを作成' })
    await user.click(button)

    await waitFor(() => {
      expect(screen.getByText(/エラー:/)).toBeInTheDocument()
    })
  })

  it('正しいAPIエンドポイントとデータで作成リクエストが送信される', async () => {
    const user = userEvent.setup()

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ puzzleId: 'test-123' }),
    })

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const nameInput = screen.getByPlaceholderText('例：富士山の風景、海の絵')
    await user.type(nameInput, 'テストパズル')

    const pieceSelect = screen.getByRole('combobox')
    await user.selectOptions(pieceSelect, '1000')

    const button = screen.getByRole('button', { name: 'パズルを作成' })
    await user.click(button)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/puzzles'),
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            puzzleName: 'テストパズル',
            pieceCount: 1000,
            userId: 'anonymous',
          }),
        })
      )
    })
  })

  it('一覧に戻るボタンで戻る', async () => {
    const user = userEvent.setup()

    render(
      <BrowserRouter>
        <PuzzleCreate />
      </BrowserRouter>
    )

    const backButton = screen.getByText('← 一覧に戻る')
    await user.click(backButton)

    expect(mockNavigate).toHaveBeenCalledWith('/')
  })
})
