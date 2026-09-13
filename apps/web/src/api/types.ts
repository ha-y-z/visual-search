export interface SearchResult {
  product_ids: string[]
  query_image: string | null
  query_text: string | null
}

export type ChatEvent =
  | { type: 'token'; text: string }
  | { type: 'images'; product_ids: string[] }

export interface Product {
  id: string
  productDisplayName: string
  gender: string | null
  masterCategory: string | null
  subCategory: string | null
  articleType: string | null
  baseColour: string | null
  season: string | null
  usage: string | null
}

export interface ProductListResponse {
  items: Product[]
  total: number
}

export type FilterOptions = Record<
  'gender' | 'masterCategory' | 'subCategory' | 'articleType' | 'baseColour' | 'season' | 'usage',
  string[]
>

export interface ChatMessage {
  role: 'assistant' | 'user'
  text: string
}
