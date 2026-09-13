<script setup lang="ts"></script>

<template>
  <header class="topbar">
    <div class="topbar-inner">
      <a href="/" class="brand">
        <span class="brand-mark">◆</span>
        Visual Search
      </a>
      <nav>
        <RouterLink to="/">Search</RouterLink>
        <RouterLink to="/products">Products</RouterLink>
      </nav>
    </div>
  </header>
  <main>
    <RouterView />
  </main>
</template>

<style>
:root {
  --bg: #fafafa;
  --surface: #ffffff;
  --text: #18181b;
  --muted: #71717a;
  --border: #e4e4e7;
  --border-strong: #d4d4d8;
  --accent: #18181b;
  --accent-contrast: #ffffff;
  --subtle: #f4f4f5;
  --radius: 14px;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.04);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04);
  --ring: 0 0 0 3px rgba(24, 24, 27, 0.08);
}
*,
*::before,
*::after {
  box-sizing: border-box;
}
html,
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    sans-serif;
  font-size: 15px;
  line-height: 1.55;
  -webkit-font-smoothing: antialiased;
}
button,
input,
select {
  font: inherit;
  color: inherit;
}
:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
</style>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(250, 250, 250, 0.8);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--border);
}
.topbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.85rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 650;
  letter-spacing: -0.01em;
  color: var(--text);
  text-decoration: none;
}
.brand-mark {
  font-size: 0.9rem;
}
nav {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  background: var(--subtle);
  border-radius: 999px;
}
nav a {
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  color: var(--muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  transition:
    color 0.15s,
    background 0.15s;
}
nav a:hover {
  color: var(--text);
}
nav a.router-link-exact-active {
  background: var(--surface);
  color: var(--text);
  box-shadow: var(--shadow-sm);
}
</style>
