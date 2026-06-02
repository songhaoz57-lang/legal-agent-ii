from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

SOURCE_EXTENSIONS = {".md", ".txt"}
WORD_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)

EMBEDDING_MODEL = "text-embedding-3-small"
CACHE_FILENAME = ".embeddings_cache.json"


@dataclass(frozen=True)
class SourceChunk:
    file: str
    heading: str
    text: str
    score: float


@dataclass
class EmbeddingCache:
    vectors: dict[str, list[float]] = field(default_factory=dict)
    model: str = EMBEDDING_MODEL
    file_hashes: dict[str, str] = field(default_factory=dict)


# ---- file I/O ----

def tokenize(text: str) -> set[str]:
    return {token.lower() for token in WORD_RE.findall(text) if len(token) > 1}


def split_markdown_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("Document", [])]
    for line in text.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip() or "Untitled"
            sections.append((heading, []))
        else:
            sections[-1][1].append(line)
    return [
        (heading, "\n".join(lines).strip())
        for heading, lines in sections
        if "\n".join(lines).strip()
    ]


def load_sources(source_dir: Path) -> list[tuple[Path, str, str]]:
    if not source_dir.exists():
        return []
    loaded: list[tuple[Path, str, str]] = []
    for path in sorted(source_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for heading, section_text in split_markdown_sections(text):
                loaded.append((path, heading, section_text))
    return loaded


# ---- cache management ----

def _cache_path(source_dir: Path) -> Path:
    return source_dir / CACHE_FILENAME


def _file_hash(p: Path) -> str:
    import hashlib
    return hashlib.md5(p.read_bytes()).hexdigest()


def _load_cache(source_dir: Path) -> EmbeddingCache:
    cp = _cache_path(source_dir)
    if cp.exists():
        try:
            raw = json.loads(cp.read_text(encoding="utf-8"))
            return EmbeddingCache(
                vectors=raw.get("vectors", {}),
                model=raw.get("model", EMBEDDING_MODEL),
                file_hashes=raw.get("file_hashes", {}),
            )
        except (json.JSONDecodeError, KeyError):
            pass
    return EmbeddingCache()


def _save_cache(source_dir: Path, cache: EmbeddingCache) -> None:
    _cache_path(source_dir).write_text(
        json.dumps({
            "vectors": cache.vectors,
            "model": cache.model,
            "file_hashes": cache.file_hashes,
        }, ensure_ascii=False),
        encoding="utf-8",
    )


def _chunk_key(p: Path, heading: str) -> str:
    return f"{p.relative_to(p.parents[1])}::{heading}"


# ---- embedding helpers ----

def _get_client():
    from openai import AsyncOpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))


async def _embed(texts: list[str]) -> list[list[float]] | None:
    client = _get_client()
    if client is None:
        return None
    try:
        resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        return [d.embedding for d in resp.data]
    except Exception:
        return None


# ---- index build ----

def build_embedding_index(source_dir: Path, force: bool = False) -> tuple[int, bool]:
    chunks = load_sources(source_dir)
    if not chunks:
        return 0, False

    cache = _load_cache(source_dir)
    if force or cache.model != EMBEDDING_MODEL:
        return len(chunks), True

    for p, _, _ in chunks:
        rel = str(p.relative_to(source_dir))
        if cache.file_hashes.get(rel) != _file_hash(p):
            return len(chunks), True

    if len(cache.vectors) < len(chunks):
        return len(chunks), True

    return len(chunks), False


async def _embed_and_cache(source_dir: Path, progress_cb: Any = None) -> int:
    chunks = load_sources(source_dir)
    if not chunks:
        return 0

    keys = [_chunk_key(p, h) for p, h, _ in chunks]
    texts = [f"{h}\n{t[:1500]}" for _, h, t in chunks]

    embeddings = await _embed(texts)
    if embeddings is None:
        return -1

    cache = EmbeddingCache(model=EMBEDDING_MODEL)
    for key, vec in zip(keys, embeddings):
        cache.vectors[key] = vec
    for p, _, _ in chunks:
        cache.file_hashes[str(p.relative_to(source_dir))] = _file_hash(p)

    _save_cache(source_dir, cache)
    if progress_cb:
        progress_cb()

    return len(chunks)


# ---- retrieval ----

def retrieve(query: str, source_dir: Path, limit: int = 5) -> list[SourceChunk]:
    """Primary retrieval: use cached embeddings if available, else keyword."""
    cache = _load_cache(source_dir)
    if cache.vectors:
        result = _retrieve_via_cache(query, source_dir, cache, limit)
        if result:
            return result
    return _retrieve_keyword(query, source_dir, limit)


def _retrieve_via_cache(
    query: str, source_dir: Path, cache: EmbeddingCache, limit: int
) -> list[SourceChunk]:
    """Sync retrieval using pre-built embedding cache + local embedding."""
    client = _get_client()
    if client is None:
        return []

    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # inside async context: can't use run_until_complete; fallback to keyword
            return []
        async def _go():
            resp = await client.embeddings.create(model=EMBEDDING_MODEL, input=[query])
            return np.array(resp.data[0].embedding, dtype=np.float64)
        query_vec = loop.run_until_complete(_go())
    except Exception:
        return []

    chunks = load_sources(source_dir)
    scored: list[tuple[float, Path, str, str]] = []
    for p, h, t in chunks:
        key = _chunk_key(p, h)
        vec_data = cache.vectors.get(key)
        if vec_data is None:
            continue
        sim = _cosine(query_vec, np.array(vec_data, dtype=np.float64))
        if sim > 0.3:
            scored.append((sim, p, h, t))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        SourceChunk(file=str(p.relative_to(source_dir)), heading=h, text=t[:1200], score=round(s, 4))
        for s, p, h, t in scored[:limit]
    ]


def _retrieve_keyword(query: str, source_dir: Path, limit: int) -> list[SourceChunk]:
    query_terms = tokenize(query)
    if not query_terms:
        return []
    chunks: list[SourceChunk] = []
    for path, heading, text in load_sources(source_dir):
        terms = tokenize(f"{heading}\n{text}")
        score = len(query_terms.intersection(terms))
        if score:
            chunks.append(
                SourceChunk(
                    file=str(path.relative_to(source_dir)),
                    heading=heading,
                    text=text[:1200],
                    score=float(score),
                )
            )
    return sorted(chunks, key=lambda c: c.score, reverse=True)[:limit]
