[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![No Maintenance Intended](https://unmaintained.tech/badge.svg)](http://unmaintained.tech/)
# Visual Search

![frontpage](docs/pictures/frontpage.png)

A multimodal fashion search prototype. Search a 3,065-product fashion catalog by text, image,
or both, then keep talking — a conversational agent sits on top of the same retrieval stack so
you can refine, compare, and ask follow-up questions about what came back.

## About The Project

Most "AI shopping search" demos are either a plain vector-search box or a chatbot bolted onto a
product feed with no real retrieval behind it. This project pairs both, properly:

- **Hybrid retrieval, not just embeddings.** Results come from BM25 lexical search *and*
  CLIP/SigLIP semantic search combined, so exact keyword matches ("red midi dress") and
  fuzzy visual/semantic queries ("something for a summer wedding") both work well.
- **Cross-encoder reranking.** A Qwen3-VL reranker rescoring the merged candidate set to sharpen
  ordering — most hybrid-search demos stop at the merge step.
- **Multimodal in, multimodal out.** Query by text, by image, or both at once — the agent can
  also pull in more product images mid-conversation instead of only returning text.
- **Graceful degradation.** If the reranker is slow, down, or disabled, the API falls back to
  un-reranked results instead of failing the request.
- **A real conversational layer.** A Gemini-backed LangChain/LangGraph agent sits on top of
  search, so the interaction isn't "one query, one result grid" — you can ask it to narrow
  down, compare items, or explain why something matched.

## Built With

**Backend / retrieval** (`apps/api`)

API:

[![FastAPI](https://img.shields.io/badge/fastapi-109989?style=for-the-badge&logo=FASTAPI&logoColor=white)](https://fastapi.tiangolo.com/) 

Keyword Search:

[![BM25s](https://img.shields.io/badge/BM25s-f7ab05?style=for-the-badge&logo=BM25s)](https://github.com/xhluca/bm25s)


Vector Search:

[![ChromaDB](https://img.shields.io/badge/ChromaDB-1cde02?style=for-the-badge&logo=ChromaDB)](https://www.trychroma.com/)
[![open_clip](https://img.shields.io/badge/OpenCLIP-black?style=for-the-badge&logo=OpenCLIP)](https://github.com/mlfoundations/open_clip)

Conversational Agent:

[![LangChain](https://img.shields.io/badge/langchain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/)
[![LangGraph](https://img.shields.io/badge/langgraph-1C3C3C?style=for-the-badge&logo=langgraph&logoColor=white)](https://www.langchain.com/langgraph)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white)](https://aistudio.google.com/)

Model Inference:

[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/) 
[![Transformers](https://img.shields.io/badge/-HuggingFace-050030?style=for-the-badge&logo=HuggingFace)](https://huggingface.co/docs/transformers)

Product Metadata:

[![SQLite](https://img.shields.io/badge/Sqlite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org/)

**Reranking service** (`services/reranker`)
- FastAPI + [Sentence-Transformers](https://www.sbert.net/) running a Qwen3-VL cross-encoder,
  served as a standalone, stateless scoring service

**Frontend** (`apps/web`)

[![Vue 3](https://img.shields.io/badge/Vue%20js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D)](https://vuejs.org/)
[![Vite](https://img.shields.io/badge/Vite-B73BFE?style=for-the-badge&logo=vite&logoColor=FFD62E)](https://vitejs.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
- [Vue Router](https://router.vuejs.org/)
- [marked](https://github.com/markedjs/marked) + [DOMPurify](https://github.com/cure53/DOMPurify) — safe markdown rendering of chat responses

**Infrastructure**

[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)
[![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- (Optional, for GPU reranking) NVIDIA GPU + [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- A LLM API key from a provider ([Google Gemini](https://ai.google.dev/) was used for the LLM chatbot). Change code according to chosen LLM provider.

### Dataset

The product catalog comes from this Kaggle dataset:
- [Embedding](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-small)
- [Displaying](https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset)

### Installation

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd ai-shopping-assistant
   ```
2. Copy the env template and fill in your LLM provider key (See [langchain](https://docs.langchain.com/oss/python/integrations/providers/all_providers)):
   ```bash
   cp .env.example .env
   ```
   `_API_KEY` complete based on chosen provider — everything else has a sensible default (see the comments in
   `.env.example`).
3. Build and run:

   CPU (no GPU required):
   ```bash
   docker compose up --build
   ```

   GPU (NVIDIA + Container Toolkit):
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build
   ```

The API is now at `http://localhost:8000` and the reranker at `http://localhost:8001`. CPU
reranking of the 2B-parameter model takes ~22–27s per query, so the CPU path raises
`RERANKER_TIMEOUT_SECONDS` to 30s; the GPU overlay tightens it back to 10s since GPU reranking
only takes ~1–2s.

## Usage

Open the web app and search by text, by image, or both — then keep chatting with the assistant
about the results.

### Search

![Demo Search](docs/videos/search_demo.gif)

### Chat

![Demo Chat](docs/videos/chat_demo.gif)

### API directly

```bash
curl http://localhost:8000/health
curl "http://localhost:8000/api/search?q=red+midi+dress"
```

See `apps/api/app/api` for the full endpoint set.

## Architecture

```mermaid
flowchart LR
    User -->|text / image| API["apps/api (FastAPI)"]
    API -->|lexical| BM25[(BM25 index)]
    API -->|semantic| Chroma[(ChromaDB + SigLIP)]
    API -->|/rerank| Reranker["services/reranker \n(FastAPI + Qwen3-VL)"]
    API -->|product metadata| SQLite[(SQLite)]
    API -->|chat| Gemini[("Google Gemini \n(LangChain agent)")]
    Reranker -->|reads images \nread-only| Images[(product images)]
```

`apps/api` owns all product data (SQLite + Chroma + BM25) and the conversational agent;
`services/reranker` is a stateless scoring service with no database access.

## Tests

```bash
cd apps/api && uv run pytest
```

The suite is pure-logic and mock-based (no multi-GB model loads), so it runs in a few seconds.

## Notes & Limitations

- **Prototype scale.** The catalog is 3,065 products — retrieval quality and latency numbers
  above don't necessarily hold at production catalog sizes.
- **CPU reranking is slow by design tradeoff.** ~22–27s/query on CPU is only acceptable because
  this is a demo; a GPU (or a smaller reranker) is required for anything interactive at scale.
- **Reranking is best-effort.** The API intentionally serves un-reranked results rather than
  fail the request if the reranker is unavailable — don't assume every response was reranked.
- **Gemini dependency.** The chat agent is hard-wired to Google Gemini; there's no local/offline
  fallback for the conversational layer.
- **No auth, no persistence of conversations.** This is a search/chat prototype, not a
  production shopping app — there's no user accounts, cart, or checkout.
