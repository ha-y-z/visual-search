<script setup lang="ts">
import { ref } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import { resetSession, search, streamChat, streamChatInit } from '@/api/client'
import type { ChatMessage, SearchResult } from '@/api/types'
import ProductCard from '@/components/ProductCard.vue'

function renderMarkdown(text: string) {
  return DOMPurify.sanitize(marked.parse(text, { async: false }))
}

const phase = ref<'idle' | 'results'>('idle')
const queryText = ref('')
const queryImage = ref<File | null>(null)
const searching = ref(false)

const searchResult = ref<SearchResult | null>(null)
const productIds = ref<string[]>([])
const messages = ref<ChatMessage[]>([])
const chatText = ref('')
const chatPending = ref(false)
// Bumped by newSearch() so a chat stream still in flight from a previous
// search can tell it was reset and stop writing into the fresh state.
let generation = 0

function onImageChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0] ?? null
  queryImage.value = file
}

async function runSearch() {
  if (!queryText.value && !queryImage.value) return
  if (phase.value === 'results') {
    generation++
    searchResult.value = null
    productIds.value = []
    messages.value = []
    chatText.value = ''
    chatPending.value = false
    await resetSession()
  }
  searching.value = true
  const gen = generation
  try {
    const result = await search(queryText.value, queryImage.value)
    if (gen !== generation) return
    searchResult.value = result
    productIds.value = result.product_ids
    phase.value = 'results'
    queryText.value = ''
    queryImage.value = null
    messages.value = [{ role: 'assistant', text: '' }]
    const replyIndex = 0
    await streamChatInit(result, (event) => {
      if (gen !== generation) return
      if (event.type === 'token') {
        messages.value[replyIndex]!.text += event.text
      } else {
        productIds.value = event.product_ids
      }
    })
  } finally {
    searching.value = false
  }
}

async function sendChat() {
  const text = chatText.value.trim()
  if (!text || chatPending.value) return
  chatText.value = ''
  messages.value.push({ role: 'user', text })
  messages.value.push({ role: 'assistant', text: '' })
  const replyIndex = messages.value.length - 1
  const gen = generation
  chatPending.value = true
  try {
    await streamChat(text, (event) => {
      if (gen !== generation) return
      if (event.type === 'token') {
        messages.value[replyIndex]!.text += event.text
      } else {
        productIds.value = event.product_ids
      }
    })
  } finally {
    chatPending.value = false
  }
}

</script>

<template>
  <div class="search-page">
    <div v-if="phase === 'idle'" class="hero">
      <h1>Find it by describing it.</h1>
      <p>Search with words, a photo, or both — then refine with the assistant.</p>
    </div>

    <form class="search-bar" :class="{ compact: phase === 'results' }" @submit.prevent="runSearch">
      <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </svg>
      <input v-model="queryText" type="text" placeholder="Describe what you're looking for…" :disabled="searching" />
      <span v-if="queryImage" class="filename">{{ queryImage.name }}</span>
      <label class="upload" title="Upload an image">
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="5" width="18" height="15" rx="3" />
          <circle cx="12" cy="12.5" r="3.5" />
          <path d="M8.5 5 10 3h4l1.5 2" />
        </svg>
        <input type="file" accept="image/*" @change="onImageChange" hidden :disabled="searching" />
      </label>
      <button type="submit" :disabled="searching">
        <span v-if="searching" class="spinner"></span>
        {{ searching ? 'Searching…' : 'Search' }}
      </button>
    </form>

    <div v-if="phase === 'results'" class="results">
      <div class="grid">
        <ProductCard v-for="id in productIds" :key="id" :id="id" />
      </div>

      <div v-if="!searching" class="chat">
        <div class="chat-header">
          <span class="dot"></span>
          Assistant
        </div>
        <div class="messages">
          <template v-for="(m, i) in messages" :key="i">
            <p v-if="m.role === 'user'" :class="m.role">{{ m.text }}</p>
            <div
              v-else-if="!m.text && i === messages.length - 1 && (chatPending || searching)"
              class="assistant typing"
            >
              <span></span><span></span><span></span>
            </div>
            <div v-else :class="m.role" v-html="renderMarkdown(m.text)"></div>
          </template>
        </div>
        <form class="chat-input" @submit.prevent="sendChat">
          <input v-model="chatText" type="text" placeholder="Keep chatting…" :disabled="chatPending" />
          <button type="submit" :disabled="chatPending">{{ chatPending ? 'Sending…' : 'Send' }}</button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem 3rem;
}
.hero {
  text-align: center;
  margin: 18vh auto 2rem;
  max-width: 640px;
}
.hero h1 {
  margin: 0 0 0.6rem;
  font-size: clamp(2rem, 4vw, 2.75rem);
  font-weight: 650;
  letter-spacing: -0.03em;
  line-height: 1.1;
}
.hero p {
  margin: 0;
  color: var(--muted);
  font-size: 1.05rem;
}
.search-bar {
  display: flex;
  gap: 0.25rem;
  align-items: center;
  max-width: 640px;
  margin: 0 auto;
  padding: 0.35rem 0.35rem 0.35rem 1rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  box-shadow: var(--shadow-md);
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
.search-bar:focus-within {
  border-color: var(--border-strong);
  box-shadow: var(--shadow-md), var(--ring);
}
.search-bar.compact {
  max-width: none;
  margin-bottom: 2rem;
  box-shadow: var(--shadow-sm);
}
.search-bar.compact:focus-within {
  box-shadow: var(--shadow-sm), var(--ring);
}
svg {
  width: 1.15rem;
  height: 1.15rem;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.search-icon {
  flex-shrink: 0;
  color: var(--muted);
}
.search-bar input[type='text'] {
  flex: 1;
  min-width: 0;
  padding: 0.6rem 0.5rem;
  border: none;
  background: transparent;
  outline: none;
}
.search-bar input[type='text']::placeholder,
.chat-input input::placeholder {
  color: #a1a1aa;
}
.upload {
  display: grid;
  place-items: center;
  width: 2.4rem;
  height: 2.4rem;
  flex-shrink: 0;
  border-radius: 999px;
  color: var(--muted);
  cursor: pointer;
  transition:
    background 0.15s,
    color 0.15s;
}
.upload:hover {
  background: var(--subtle);
  color: var(--text);
}
.filename {
  font-size: 0.8rem;
  color: var(--text);
  background: var(--subtle);
  border: 1px solid var(--border);
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  max-width: 140px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
button {
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  padding: 0.6rem 1.25rem;
  border-radius: 999px;
  border: none;
  background: var(--accent);
  color: var(--accent-contrast);
  font-weight: 500;
  cursor: pointer;
  transition:
    opacity 0.15s,
    transform 0.1s;
}
button:hover:not(:disabled) {
  opacity: 0.88;
}
button:active:not(:disabled) {
  transform: scale(0.98);
}
button:disabled {
  opacity: 0.45;
  cursor: default;
}
.results {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 2rem;
  align-items: start;
}
@media (min-width: 960px) {
  .results {
    grid-template-columns: minmax(0, 1fr) 380px;
  }
  .chat {
    position: sticky;
    top: 5rem;
  }
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1.25rem;
}
.chat {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.8rem 1.1rem;
  border-bottom: 1px solid var(--border);
  font-size: 0.85rem;
  font-weight: 600;
}
.chat-header .dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #22c55e;
}
.messages {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  max-height: 60vh;
  overflow-y: auto;
  padding: 1.1rem;
  font-size: 0.925rem;
}
.messages p {
  margin: 0;
  white-space: pre-wrap;
}
.messages p.user {
  align-self: flex-end;
  max-width: 85%;
  background: var(--accent);
  color: var(--accent-contrast);
  padding: 0.5rem 0.85rem;
  border-radius: 16px 16px 4px 16px;
}
.messages .assistant {
  color: var(--text);
}
.messages .assistant :deep(p) {
  margin: 0 0 0.6rem;
}
.messages .assistant :deep(p:last-child) {
  margin-bottom: 0;
}
.messages .assistant :deep(strong) {
  font-weight: 600;
}
.messages .assistant :deep(code) {
  background: var(--subtle);
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  font-size: 0.85em;
}
.messages .assistant :deep(pre) {
  background: var(--subtle);
  padding: 0.75rem;
  border-radius: 8px;
  overflow-x: auto;
}
.messages .assistant :deep(pre code) {
  background: none;
  padding: 0;
}
.messages .assistant :deep(ul),
.messages .assistant :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.3rem;
}
.messages .assistant :deep(li) {
  margin: 0.2rem 0;
}
.chat-input {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid var(--border);
  background: var(--bg);
}
.chat-input input {
  flex: 1;
  min-width: 0;
  padding: 0.55rem 0.95rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  outline: none;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
.chat-input input:focus {
  border-color: var(--border-strong);
  box-shadow: var(--ring);
}
.chat-input button {
  padding: 0.55rem 1.1rem;
}
.spinner {
  display: inline-block;
  width: 0.8em;
  height: 0.8em;
  margin-right: 0.4em;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #fff;
  border-radius: 50%;
  vertical-align: -0.1em;
  animation: spin 0.7s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.typing {
  display: flex;
  gap: 0.25rem;
  padding: 0.2rem 0;
}
.typing span {
  width: 0.4rem;
  height: 0.4rem;
  border-radius: 50%;
  background: var(--muted);
  animation: bounce 1s infinite ease-in-out;
}
.typing span:nth-child(2) {
  animation-delay: 0.15s;
}
.typing span:nth-child(3) {
  animation-delay: 0.3s;
}
@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
