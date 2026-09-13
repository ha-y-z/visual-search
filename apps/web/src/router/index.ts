import { createRouter, createWebHistory } from 'vue-router'
import SearchView from '@/views/SearchView.vue'
import ProductsView from '@/views/ProductsView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'search', component: SearchView },
    { path: '/products', name: 'products', component: ProductsView },
  ],
})
