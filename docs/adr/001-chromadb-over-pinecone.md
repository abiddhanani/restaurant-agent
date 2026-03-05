# ADR 001: ChromaDB over Pinecone for Phase 0

**Date:** 2025-01-01
**Status:** Accepted

## Context
Need a vector DB for RAG review storage. Options considered: Pinecone (managed SaaS),
Weaviate (self-hosted), ChromaDB (local/containerised).

## Decision
Use ChromaDB for Phase 0 (zero customers, proving the concept).

## Reasoning
- Phase 0 has zero revenue — Pinecone starter plan is $70/month we don't need yet
- ChromaDB runs in Docker alongside the app — zero additional infrastructure
- Both have tenant namespacing via collections — migration path is clean
- Switching to Pinecone in Phase 1 requires changing only rag/retrieval/engine.py

## Revisit Trigger
First paying customer OR when ChromaDB performance becomes a bottleneck.

## Consequences
- No managed backups in Phase 0 — acceptable risk given no production data yet
- chroma_data/ volume in docker-compose.yml provides local persistence
