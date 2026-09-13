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
  searching.value = true
  const gen = generation
  try {
    const result = await search(queryText.value, queryImage.value)
    if (gen !== generation) return
    searchResult.value = result
    productIds.value = result.product_ids
    phase.value = 'results'
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

async function newSearch() {
  generation++
  await resetSession()
  phase.value = 'idle'
  queryText.value = ''
  queryImage.value = null
  searchResult.value = null
  productIds.value = []
  messages.value = []
  chatText.value = ''
}
</script>

<template>
  <div class="search-page">
    <form v-if="phase === 'idle'" class="search-bar" @submit.prevent="runSearch">
      <input v-model="queryText" type="text" placeholder="Describe what you're looking for…" :disabled="searching" />
      <label class="upload">
        📷
        <input type="file" accept="image/*" @change="onImageChange" hidden :disabled="searching" />
      </label>
      <span v-if="queryImage" class="filename">{{ queryImage.name }}</span>
      <button type="submit" :disabled="searching">
        <span v-if="searching" class="spinner"></span>
        {{ searching ? 'Searching…' : 'Search' }}
      </button>
    </form>

    <div v-else class="results">
      <button class="new-search" @click="newSearch">New search</button>

      <div class="grid">
        <ProductCard v-for="id in productIds" :key="id" :id="id" />
      </div>

      <div class="chat">
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
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem 1rem;
}
.search-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  justify-content: center;
  margin-top: 20vh;
}
.search-bar input[type='text'] {
  flex: 1;
  max-width: 480px;
  padding: 0.6rem 0.9rem;
  border-radius: 999px;
  border: 1px solid #ccc;
}
.upload {
  cursor: pointer;
  font-size: 1.3rem;
}
.filename {
  font-size: 0.8rem;
  color: #666;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}
button {
  padding: 0.6rem 1.1rem;
  border-radius: 999px;
  border: none;
  background: #222;
  color: #fff;
  cursor: pointer;
}
button:disabled {
  opacity: 0.5;
  cursor: default;
}
.new-search {
  margin-bottom: 1rem;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}
.chat {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 1rem;
}
.messages {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 40vh;
  overflow-y: auto;
  margin-bottom: 0.75rem;
}
.messages p {
  margin: 0;
  white-space: pre-wrap;
}
.messages p.user {
  align-self: flex-end;
  background: #222;
  color: #fff;
  padding: 0.4rem 0.7rem;
  border-radius: 10px;
}
.messages .assistant :deep(p) {
  margin: 0 0 0.5rem;
}
.messages .assistant :deep(p:last-child) {
  margin-bottom: 0;
}
.messages .assistant :deep(pre) {
  background: #f4f4f4;
  padding: 0.5rem;
  border-radius: 6px;
  overflow-x: auto;
}
.messages .assistant :deep(ul),
.messages .assistant :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.4rem;
}
.chat-input {
  display: flex;
  gap: 0.5rem;
}
.chat-input input {
  flex: 1;
  padding: 0.5rem 0.8rem;
  border-radius: 999px;
  border: 1px solid #ccc;
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
  background: #999;
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
