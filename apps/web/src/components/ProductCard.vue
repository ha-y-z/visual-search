<script setup lang="ts">
import { productImageUrl } from '@/api/client'

defineProps<{ id: string; name?: string | null }>()
</script>

<template>
  <figure class="card">
    <img :src="productImageUrl(id)" :alt="name ?? id" loading="lazy" />
    <figcaption v-if="name">{{ name }}</figcaption>
  </figure>
</template>

<style scoped>
.card {
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
img {
  width: 100%;
  aspect-ratio: 3 / 4;
  object-fit: cover;
  border-radius: 8px;
  background: #eee;
}
figcaption {
  font-size: 0.85rem;
  color: #333;
  line-clamp: 2;
  overflow: hidden;
}
</style>
