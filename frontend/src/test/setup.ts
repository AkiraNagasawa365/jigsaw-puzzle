import '@testing-library/jest-dom'
import { afterEach, beforeAll, afterAll, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// クリーンアップを自動実行
afterEach(() => {
  cleanup()
})

// fetch APIのモック（テスト環境にはfetchがないため）
global.fetch = vi.fn() as any

// console.errorのモック（React Router等の警告を抑制）
const originalError = console.error
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render')
    ) {
      return
    }
    originalError.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
})
