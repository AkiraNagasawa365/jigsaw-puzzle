import type { Mock } from 'vitest'

declare global {
  var fetch: Mock
}
