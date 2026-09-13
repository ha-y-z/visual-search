<script setup lang="ts"></script>

<template>
  <nav>
    <RouterLink to="/">Search</RouterLink>
    <RouterLink to="/products">Products</RouterLink>
  </nav>
  <RouterView />
</template>

<style scoped>
nav {
  display: flex;
  gap: 1.5rem;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #eee;
}
nav a {
  color: #222;
  text-decoration: none;
  font-weight: 600;
}
nav a.router-link-active {
  color: #000;
  text-decoration: underline;
}
</style>
