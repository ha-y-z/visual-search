import type { ChatEvent, FilterOptions, ProductListResponse, SearchResult } from './types'

export function productImageUrl(id: string): string {
  return `/api/images/${id}`
}

export async function search(text: string, image: File | null): Promise<SearchResult> {
  const body = new FormData()
  if (text) body.set('text', text)
  if (image) body.set('image', image)
  const res = await fetch('/api/search', { method: 'POST', body })
  if (!res.ok) throw new Error(`search failed: ${res.status}`)
  return res.json()
}

export async function resetSession(): Promise<void> {
  await fetch('/api/session/reset', { method: 'POST' })
}

export async function getFilterOptions(): Promise<FilterOptions> {
  const res = await fetch('/api/products/filters')
  if (!res.ok) throw new Error(`filters failed: ${res.status}`)
  return res.json()
}

export async function getProducts(params: {
  page: number
  pageSize: number
  filters: Record<string, string>
}): Promise<ProductListResponse> {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  })
  for (const [key, value] of Object.entries(params.filters)) {
    if (value) query.set(key, value)
  }
  const res = await fetch(`/api/products?${query}`)
  if (!res.ok) throw new Error(`products failed: ${res.status}`)
  return res.json()
}

async function streamSSE(path: string, body: unknown, onEvent: (event: ChatEvent) => void) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok || !res.body) throw new Error(`${path} failed: ${res.status}`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const frames = buffer.split('\n\n')
    buffer = frames.pop() ?? ''
    for (const frame of frames) {
      const line = frame.trim()
      if (!line.startsWith('data:')) continue
      onEvent(JSON.parse(line.slice(5)) as ChatEvent)
    }
  }
}

export function streamChatInit(result: SearchResult, onEvent: (event: ChatEvent) => void) {
  return streamSSE('/api/chat/init', result, onEvent)
}

export function streamChat(text: string, onEvent: (event: ChatEvent) => void) {
  return streamSSE('/api/chat', { text }, onEvent)
}
