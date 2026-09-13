<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { getFilterOptions, getProducts } from '@/api/client'
import type { FilterOptions, Product } from '@/api/types'
import ProductCard from '@/components/ProductCard.vue'

const PAGE_SIZE = 24
const FILTER_COLUMNS = [
  'gender',
  'masterCategory',
  'subCategory',
  'articleType',
  'baseColour',
  'season',
  'usage',
] as const

const filterOptions = ref<FilterOptions | null>(null)
const filters = ref<Record<string, string>>({})
const page = ref(1)
const products = ref<Product[]>([])
const total = ref(0)

async function load() {
  const result = await getProducts({ page: page.value, pageSize: PAGE_SIZE, filters: filters.value })
  products.value = result.items
  total.value = result.total
}

onMounted(async () => {
  filterOptions.value = await getFilterOptions()
  await load()
})

watch(filters, () => {
  page.value = 1
  load()
}, { deep: true })
watch(page, load)
</script>

<template>
  <div class="products-page">
    <div class="filters" v-if="filterOptions">
      <select v-for="col in FILTER_COLUMNS" :key="col" v-model="filters[col]">
        <option value="">{{ col }}</option>
        <option v-for="value in filterOptions[col]" :key="value" :value="value">{{ value }}</option>
      </select>
    </div>

    <div class="grid">
      <ProductCard
        v-for="p in products"
        :key="p.id"
        :id="p.id"
        :name="p.productDisplayName"
      />
    </div>

    <div class="pager">
      <button :disabled="page === 1" @click="page--">Prev</button>
      <span>Page {{ page }} / {{ Math.max(1, Math.ceil(total / PAGE_SIZE)) }}</span>
      <button :disabled="page * PAGE_SIZE >= total" @click="page++">Next</button>
    </div>
  </div>
</template>

<style scoped>
.products-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}
select {
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  border: 1px solid #ccc;
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1.5rem;
}
.pager button {
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: none;
  background: #222;
  color: #fff;
  cursor: pointer;
}
.pager button:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
