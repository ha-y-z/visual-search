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

const FILTER_LABELS: Record<(typeof FILTER_COLUMNS)[number], string> = {
  gender: 'Gender',
  masterCategory: 'Category',
  subCategory: 'Subcategory',
  articleType: 'Article Type',
  baseColour: 'Colour',
  season: 'Season',
  usage: 'Usage',
}

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
  for (const col of FILTER_COLUMNS) {
    filters.value[col] = ''
  }
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
    <div class="page-header">
      <h1>Products</h1>
      <span class="count">{{ total.toLocaleString() }} items</span>
    </div>

    <div class="filters" v-if="filterOptions">
      <select v-for="col in FILTER_COLUMNS" :key="col" v-model="filters[col]">
        <option value="">All {{ FILTER_LABELS[col] }}</option>
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 2.5rem 1.5rem 3rem;
}
.page-header {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.page-header h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 650;
  letter-spacing: -0.02em;
}
.count {
  color: var(--muted);
  font-size: 0.9rem;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding-bottom: 1.5rem;
  margin-bottom: 2rem;
  border-bottom: 1px solid var(--border);
}
select {
  appearance: none;
  padding: 0.45rem 2rem 0.45rem 0.9rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface)
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2371717a' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E")
    no-repeat right 0.65rem center / 0.9rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
select:hover {
  border-color: var(--border-strong);
}
select:focus {
  outline: none;
  border-color: var(--border-strong);
  box-shadow: var(--ring);
}
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 1.75rem 1.25rem;
}
.pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 3rem;
}
.pager span {
  color: var(--muted);
  font-size: 0.875rem;
  font-variant-numeric: tabular-nums;
}
.pager button {
  padding: 0.45rem 1.1rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background 0.15s;
}
.pager button:hover:not(:disabled) {
  border-color: var(--border-strong);
  background: var(--subtle);
}
.pager button:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
