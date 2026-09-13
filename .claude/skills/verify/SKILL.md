---
name: verify
description: How to launch and drive this repo's app end-to-end for verification (backend + frontend).
---

# Verifying ai-shopping-assistant

Two apps, no root workspace tooling — start each independently.

## Launch

```bash
# backend (slow first boot: downloads/loads CLIP+SigLIP models, ~40-60s)
cd apps/api && uv run uvicorn app.main:app --port 8000 &
for i in $(seq 1 30); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)" = 200 ] && break
  sleep 2
done

# frontend
cd apps/web && npm install --legacy-peer-deps   # create-vue's oxlint pin conflicts with npm's resolver, --legacy-peer-deps is required
npm run dev -- --port 5173 &
```

Vite proxies `/api/*` to `localhost:8000` (see `apps/web/vite.config.ts`), so no CORS
setup is needed and the frontend can be driven at `http://localhost:5173/` alone.

The reranker microservice (`services/reranker`) is not required for local dev —
`/api/search` logs a warning ("Reranker call failed... Connection refused") and
falls back to un-reranked results, which is fine for verification.

## Drive it

No `claude-in-chrome`/browser MCP tool is available in this environment. Use
Playwright directly instead:

```bash
cd <scratchpad>
npm init -y && npm install playwright@1.63.0
npx playwright install chromium --with-deps   # ~280MB one-time download
node your-script.js   # require('playwright').chromium.launch()
```

Key selectors (from `apps/web/src`):
- Search page (`/`): `.search-bar input[type=text]`, `.upload input[type=file]`,
  `.search-bar button[type=submit]`, then `.results .grid .card`,
  `.messages p.assistant` / `p.user`, `.chat-input`, `.new-search`.
- Products page (`/products`): `.filters select` (7, in column order gender,
  masterCategory, subCategory, articleType, baseColour, season, usage),
  `.grid .card`, `.pager button` (Prev/Next), `.pager span`.
- Chat text streams in via SSE — poll with `page.waitForFunction` on
  `textContent.length`, not a fixed sleep; a single style-reasoning reply is
  ~1-2s server-side once the model call starts.

A sample query image for image-search testing:
`apps/api/data/products/evaluation/jacket/leather_jacket.jpg`.

## Gotchas hit during verification

- **Vue reactivity trap**: don't hoist a message object out of the `messages`
  ref and mutate it directly (`const reply = {...}; messages.value = [reply];
  reply.text += chunk`) — the ref wraps the array in a reactive proxy, but the
  raw `reply` reference bypasses it, so template updates never fire even
  though no error is thrown. Mutate through the array index instead
  (`messages.value[i].text += chunk`).
- **`watch()` on a `ref<object>` is shallow by default** — mutating a nested
  property (e.g. `filters.value[col] = x` from a `v-model`) won't trigger the
  watcher unless you pass `{ deep: true }`.
- Product grid uses `loading="lazy"` — a `fullPage` screenshot taken right
  after load can show blank gray boxes for below-the-fold images that simply
  haven't loaded yet. Not a bug; scroll + wait, or check `img.naturalWidth`
  before concluding an image is broken.
