<script setup lang="ts">
import { productImageUrl } from '@/api/client'

defineProps<{ id: string; name?: string | null }>()
</script>

<template>
  <figure class="card">
    <div class="media">
      <img :src="productImageUrl(id)" :alt="name ?? id" loading="lazy" />
    </div>
    <figcaption v-if="name">{{ name }}</figcaption>
  </figure>
</template>

<style scoped>
.card {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.media {
  overflow: hidden;
  border-radius: 12px;
  background: var(--subtle);
  border: 1px solid var(--border);
  transition:
    box-shadow 0.2s,
    transform 0.2s;
}
.card:hover .media {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
img {
  display: block;
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  transition: transform 0.4s ease;
}
.card:hover img {
  transform: scale(1.03);
}
figcaption {
  font-size: 0.85rem;
  line-height: 1.4;
  color: var(--text);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  overflow: hidden;
}
</style>
