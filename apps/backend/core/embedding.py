"""
LifeOS Embedding 服务
支持本地 Ollama（隐私优先）和云端 API（备选）
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx
import numpy as np


EMBEDDING_CACHE_DIR = Path.home() / ".lifeos" / "embedding_cache"
EMBEDDING_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class EmbeddingService:
    """
    Embedding 服务，优先使用本地 Ollama，
    回退到 OpenAI text-embedding-3-small
    """

    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        self.openai_key = os.getenv("OPENAI_API_KEY", "")
        self._ollama_available: Optional[bool] = None

    async def _check_ollama(self) -> bool:
        if self._ollama_available is not None:
            return self._ollama_available
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.ollama_url}/api/tags")
                self._ollama_available = resp.status_code == 200
        except Exception:
            self._ollama_available = False
        return self._ollama_available

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _load_cache(self, key: str) -> list[float] | None:
        path = EMBEDDING_CACHE_DIR / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def _save_cache(self, key: str, embedding: list[float]):
        path = EMBEDDING_CACHE_DIR / f"{key}.json"
        path.write_text(json.dumps(embedding))

    async def embed(self, text: str) -> list[float]:
        """为单段文本生成 embedding，带本地缓存"""
        text = text.strip()[:2000]  # 截断过长文本
        if not text:
            return [0.0] * 768

        cache_key = self._cache_key(text)
        cached = self._load_cache(cache_key)
        if cached:
            return cached

        if await self._check_ollama():
            embedding = await self._embed_ollama(text)
        elif self.openai_key:
            embedding = await self._embed_openai(text)
        else:
            # 降级：使用简单的词频向量（仅开发用，不应用于生产）
            embedding = self._embed_fallback(text)

        self._save_cache(cache_key, embedding)
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量 embedding，并发控制避免过载"""
        semaphore = asyncio.Semaphore(5)
        async def _embed_one(text):
            async with semaphore:
                return await self.embed(text)
        return await asyncio.gather(*[_embed_one(t) for t in texts])

    async def _embed_ollama(self, text: str) -> list[float]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={"model": self.ollama_model, "prompt": text}
                )
                data = resp.json()
                return data["embedding"]
        except Exception as e:
            print(f"[Embedding] Ollama 失败: {e}，尝试备选方案")
            self._ollama_available = False
            if self.openai_key:
                return await self._embed_openai(text)
            return self._embed_fallback(text)

    async def _embed_openai(self, text: str) -> list[float]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    json={"model": "text-embedding-3-small", "input": text}
                )
                data = resp.json()
                return data["data"][0]["embedding"]
        except Exception as e:
            print(f"[Embedding] OpenAI 失败: {e}")
            return self._embed_fallback(text)

    def _embed_fallback(self, text: str) -> list[float]:
        """降级方案：基于字符哈希的伪向量，仅供开发调试"""
        import hashlib
        h = hashlib.sha256(text.encode()).digest()
        # 扩展到 768 维
        extended = (h * 24)[:768]
        vec = [b / 255.0 for b in extended]
        norm = sum(x**2 for x in vec) ** 0.5
        return [x / norm for x in vec] if norm > 0 else vec

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
        return float(dot / norm) if norm > 0 else 0.0


# 全局单例
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
